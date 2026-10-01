
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def google_modules():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit(
            "Missing Google API packages.\n\nInstall once with:\n"
            "  python.exe -m pip install --upgrade "
            "google-api-python-client google-auth-httplib2 google-auth-oauthlib\n"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build


def get_credentials(client_secret: Path, token_path: Path):
    Request, Credentials, InstalledAppFlow, _ = google_modules()
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not client_secret.exists():
            raise SystemExit(
                "Google OAuth client secret not found.\n\n"
                f"Expected:\n  {client_secret}\n"
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_services(creds):
    _, _, _, build = google_modules()
    searchconsole = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    webmasters = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    return searchconsole, webmasters


def choose_property(webmasters, requested: str | None, host: str) -> str:
    resp = webmasters.sites().list().execute()
    props = [x.get("siteUrl", "") for x in resp.get("siteEntry", []) if x.get("siteUrl")]

    if requested:
        if requested not in props:
            raise SystemExit(
                "Requested Search Console property is not available:\n"
                f"  {requested}\n\nAvailable properties:\n  " + "\n  ".join(props)
            )
        return requested

    domain = f"sc-domain:{host}"
    if domain in props:
        return domain

    for candidate in (
        f"https://{host}/",
        f"https://www.{host}/",
        f"http://{host}/",
        f"http://www.{host}/",
    ):
        if candidate in props:
            return candidate

    raise SystemExit(
        f"No Search Console property matching {host} was found.\n\n"
        "Available properties:\n  " + "\n  ".join(props)
    )


def iso(d: date) -> str:
    return d.isoformat()


def period(days: int, lag_days: int, end_date: str | None):
    if end_date:
        end = date.fromisoformat(end_date)
    else:
        end = datetime.now(timezone.utc).date() - timedelta(days=lag_days)
    start = end - timedelta(days=days - 1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return start, end, prev_start, prev_end


def fetch_rows(
    service,
    site_url: str,
    start: date,
    end: date,
    dimensions: list[str],
    search_type: str = "web",
    row_limit: int = 25000,
) -> list[dict]:
    rows = []
    start_row = 0
    while True:
        body = {
            "startDate": iso(start),
            "endDate": iso(end),
            "dimensions": dimensions,
            "type": search_type,
            "rowLimit": row_limit,
            "startRow": start_row,
            "dataState": "final",
        }
        resp = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
        batch = resp.get("rows", [])
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < row_limit:
            break
        start_row += len(batch)
    return rows


def normalize_rows(rows: list[dict], dimensions: list[str]) -> list[dict]:
    out = []
    for row in rows:
        keys = row.get("keys", [])
        item = {}
        for i, dim in enumerate(dimensions):
            item[dim] = keys[i] if i < len(keys) else ""
        item.update(
            clicks=float(row.get("clicks", 0)),
            impressions=float(row.get("impressions", 0)),
            ctr=float(row.get("ctr", 0)),
            position=float(row.get("position", 0)),
        )
        out.append(item)
    return out


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        if not fields:
            f.write("")
            return
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def pct(v: float) -> float:
    return round(v * 100, 4)


def rounded_metrics(row: dict) -> dict:
    return {
        **row,
        "clicks": round(float(row.get("clicks", 0)), 2),
        "impressions": round(float(row.get("impressions", 0)), 2),
        "ctr_percent": pct(float(row.get("ctr", 0))),
        "position": round(float(row.get("position", 0)), 2),
    }


def keyed(rows: list[dict], dims: list[str]):
    return {tuple(r.get(d, "") for d in dims): r for r in rows}


def comparison_rows(current: list[dict], previous: list[dict], dims: list[str]) -> list[dict]:
    cur = keyed(current, dims)
    prev = keyed(previous, dims)
    result = []
    for key in sorted(set(cur) | set(prev)):
        c = cur.get(key, {})
        p = prev.get(key, {})
        ci = float(c.get("impressions", 0))
        pi = float(p.get("impressions", 0))
        cc = float(c.get("clicks", 0))
        pc = float(p.get("clicks", 0))
        cctr = float(c.get("ctr", 0))
        pctr = float(p.get("ctr", 0))
        cpos = float(c.get("position", 0))
        ppos = float(p.get("position", 0))
        row = {dims[i]: key[i] for i in range(len(dims))}
        row.update({
            "current_clicks": round(cc, 2),
            "previous_clicks": round(pc, 2),
            "click_change": round(cc - pc, 2),
            "current_impressions": round(ci, 2),
            "previous_impressions": round(pi, 2),
            "impression_change": round(ci - pi, 2),
            "impression_change_percent": (
                round(((ci - pi) / pi) * 100, 2) if pi else ""
            ),
            "current_ctr_percent": round(cctr * 100, 4),
            "previous_ctr_percent": round(pctr * 100, 4),
            "ctr_change_points": round((cctr - pctr) * 100, 4),
            "current_position": round(cpos, 2) if c else "",
            "previous_position": round(ppos, 2) if p else "",
            # Positive means ranking improved (position number got smaller).
            "position_improvement": round(ppos - cpos, 2) if c and p else "",
        })
        result.append(row)
    return result


def is_branded(query: str) -> bool:
    q = (query or "").lower().strip()
    return "tampa bay shine" in q


def opportunity_label(impressions: float, ctr: float, position: float) -> list[str]:
    labels = []
    if 4 <= position <= 10 and impressions >= 10 and ctr < 0.02:
        labels.append("PAGE_ONE_LOW_CTR")
    if 10 < position <= 20 and impressions >= 10:
        labels.append("NEAR_PAGE_ONE")
    if 4 <= position <= 20 and impressions >= 20:
        labels.append("STRIKING_DISTANCE")
    if impressions >= 30 and position <= 20 and ctr < 0.01:
        labels.append("HIGH_IMPRESSIONS_LOW_CTR")
    return labels


def opportunity_score(impressions: float, ctr: float, position: float, growth_pct) -> float:
    # Heuristic only: rewards impressions, rankings within reach of page one,
    # low CTR, and recent impression growth. It is for prioritization, not a Google score.
    if not (4 <= position <= 20) or impressions < 5:
        return 0.0
    proximity = max(0.10, (21.0 - position) / 17.0)
    ctr_factor = max(0.25, 1.0 - min(ctr / 0.05, 1.0))
    growth_factor = 1.0
    if isinstance(growth_pct, (int, float)):
        growth_factor += max(-0.25, min(growth_pct / 100.0, 1.0)) * 0.25
    return round(math.log1p(impressions) * proximity * ctr_factor * growth_factor * 100, 2)


def build_opportunities(current_qp: list[dict], previous_qp: list[dict], include_branded: bool):
    prev = keyed(previous_qp, ["query", "page"])
    rows = []
    for c in current_qp:
        query = c.get("query", "")
        page = c.get("page", "")
        if not include_branded and is_branded(query):
            continue

        impressions = float(c.get("impressions", 0))
        clicks = float(c.get("clicks", 0))
        ctr = float(c.get("ctr", 0))
        position = float(c.get("position", 0))
        labels = opportunity_label(impressions, ctr, position)
        if not labels:
            continue

        p = prev.get((query, page), {})
        prev_imp = float(p.get("impressions", 0))
        prev_pos = float(p.get("position", 0)) if p else None
        growth_pct = ((impressions - prev_imp) / prev_imp * 100) if prev_imp else None
        score = opportunity_score(impressions, ctr, position, growth_pct)

        rows.append({
            "opportunity_score": score,
            "query": query,
            "page": page,
            "flags": "|".join(labels),
            "clicks": round(clicks, 2),
            "impressions": round(impressions, 2),
            "ctr_percent": round(ctr * 100, 4),
            "position": round(position, 2),
            "previous_impressions": round(prev_imp, 2),
            "impression_change_percent": round(growth_pct, 2) if growth_pct is not None else "",
            "previous_position": round(prev_pos, 2) if prev_pos is not None else "",
            "position_improvement": round(prev_pos - position, 2) if prev_pos is not None else "",
            "branded": str(is_branded(query)).lower(),
        })
    rows.sort(key=lambda r: (-float(r["opportunity_score"]), -float(r["impressions"])))
    return rows


def build_page_opportunities(opps: list[dict]) -> list[dict]:
    buckets = defaultdict(list)
    for r in opps:
        buckets[r["page"]].append(r)

    out = []
    for page, rows in buckets.items():
        total_imp = sum(float(r["impressions"]) for r in rows)
        total_clicks = sum(float(r["clicks"]) for r in rows)
        weighted_pos = (
            sum(float(r["position"]) * float(r["impressions"]) for r in rows) / total_imp
            if total_imp else 0
        )
        top = sorted(rows, key=lambda r: (-float(r["opportunity_score"]), -float(r["impressions"])))[0]
        out.append({
            "page": page,
            "opportunity_queries": len(rows),
            "opportunity_impressions": round(total_imp, 2),
            "opportunity_clicks": round(total_clicks, 2),
            "weighted_position": round(weighted_pos, 2),
            "top_query": top["query"],
            "top_query_score": top["opportunity_score"],
            "top_query_flags": top["flags"],
        })

    out.sort(key=lambda r: (-float(r["top_query_score"]), -float(r["opportunity_impressions"])))
    return out


def build_cannibalization(current_qp: list[dict]) -> list[dict]:
    by_query = defaultdict(list)
    for r in current_qp:
        if float(r.get("impressions", 0)) >= 3:
            by_query[r.get("query", "")].append(r)

    out = []
    for query, rows in by_query.items():
        if len(rows) < 2:
            continue
        total_imp = sum(float(r.get("impressions", 0)) for r in rows)
        if total_imp < 10:
            continue
        rows = sorted(rows, key=lambda r: -float(r.get("impressions", 0)))
        out.append({
            "query": query,
            "pages_with_impressions": len(rows),
            "total_impressions": round(total_imp, 2),
            "page_1": rows[0].get("page", ""),
            "page_1_impressions": round(float(rows[0].get("impressions", 0)), 2),
            "page_1_position": round(float(rows[0].get("position", 0)), 2),
            "page_2": rows[1].get("page", ""),
            "page_2_impressions": round(float(rows[1].get("impressions", 0)), 2),
            "page_2_position": round(float(rows[1].get("position", 0)), 2),
        })
    out.sort(key=lambda r: -float(r["total_impressions"]))
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Pull Google Search Console performance data and surface SEO opportunities."
    )
    ap.add_argument("--property", default=None, help='e.g. sc-domain:tampabayshine.com')
    ap.add_argument("--host", default="tampabayshine.com")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--lag-days", type=int, default=3, help="Default avoids the freshest potentially incomplete GSC days.")
    ap.add_argument("--end-date", default=None, help="YYYY-MM-DD; overrides --lag-days")
    ap.add_argument("--search-type", default="web")
    ap.add_argument("--include-branded", action="store_true")
    ap.add_argument("--client-secret", default=str(Path.home() / ".tbs-gsc" / "client_secret.json"))
    ap.add_argument("--token", default=str(Path.home() / ".tbs-gsc" / "token.json"))
    ap.add_argument("--out-dir", default="reports/gsc-performance")
    args = ap.parse_args()

    if args.days < 1:
        raise SystemExit("--days must be at least 1")

    current_start, current_end, previous_start, previous_end = period(
        args.days, args.lag_days, args.end_date
    )

    creds = get_credentials(Path(args.client_secret), Path(args.token))
    service, webmasters = build_services(creds)
    property_url = choose_property(webmasters, args.property, args.host)

    print("TAMPA BAY SHINE GSC PERFORMANCE AUDIT")
    print("=====================================")
    print(f"Property:         {property_url}")
    print(f"Current period:   {current_start} to {current_end} ({args.days} days)")
    print(f"Previous period:  {previous_start} to {previous_end} ({args.days} days)")
    print(f"Search type:      {args.search_type}")
    print("")

    datasets = {}
    specs = [
        ("pages", ["page"]),
        ("queries", ["query"]),
        ("query_page", ["query", "page"]),
    ]
    for name, dims in specs:
        print(f"Fetching current {name}...")
        cur_raw = fetch_rows(service, property_url, current_start, current_end, dims, args.search_type)
        print(f"Fetching previous {name}...")
        prev_raw = fetch_rows(service, property_url, previous_start, previous_end, dims, args.search_type)
        datasets[name] = (
            normalize_rows(cur_raw, dims),
            normalize_rows(prev_raw, dims),
        )

    pages_cur, pages_prev = datasets["pages"]
    queries_cur, queries_prev = datasets["queries"]
    qp_cur, qp_prev = datasets["query_page"]

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pages_current_out = [rounded_metrics(r) for r in pages_cur]
    queries_current_out = [rounded_metrics(r) for r in queries_cur]
    qp_current_out = [rounded_metrics(r) for r in qp_cur]

    write_csv(out_dir / "pages-current.csv", pages_current_out)
    write_csv(out_dir / "queries-current.csv", queries_current_out)
    write_csv(out_dir / "query-page-current.csv", qp_current_out)

    page_comp = comparison_rows(pages_cur, pages_prev, ["page"])
    query_comp = comparison_rows(queries_cur, queries_prev, ["query"])
    qp_comp = comparison_rows(qp_cur, qp_prev, ["query", "page"])

    write_csv(out_dir / "pages-comparison.csv", page_comp)
    write_csv(out_dir / "queries-comparison.csv", query_comp)
    write_csv(out_dir / "query-page-comparison.csv", qp_comp)

    opportunities = build_opportunities(qp_cur, qp_prev, args.include_branded)
    page_opps = build_page_opportunities(opportunities)
    cannibal = build_cannibalization(qp_cur)

    write_csv(out_dir / "opportunities.csv", opportunities)
    write_csv(out_dir / "page-opportunities.csv", page_opps)
    write_csv(out_dir / "cannibalization-review.csv", cannibal)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "property": property_url,
        "current_period": {"start": iso(current_start), "end": iso(current_end), "days": args.days},
        "previous_period": {"start": iso(previous_start), "end": iso(previous_end), "days": args.days},
        "rows": {
            "current_pages": len(pages_cur),
            "current_queries": len(queries_cur),
            "current_query_page": len(qp_cur),
            "opportunities": len(opportunities),
            "page_opportunities": len(page_opps),
            "cannibalization_review": len(cannibal),
        },
        "top_page_opportunities": page_opps[:10],
        "top_query_page_opportunities": opportunities[:25],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary_txt = []
    summary_txt.append("TAMPA BAY SHINE GSC PERFORMANCE AUDIT")
    summary_txt.append("=====================================")
    summary_txt.append(f"Property: {property_url}")
    summary_txt.append(f"Current:  {current_start} to {current_end}")
    summary_txt.append(f"Previous: {previous_start} to {previous_end}")
    summary_txt.append("")
    summary_txt.append(f"Current page rows:          {len(pages_cur)}")
    summary_txt.append(f"Current query rows:         {len(queries_cur)}")
    summary_txt.append(f"Current query/page rows:    {len(qp_cur)}")
    summary_txt.append(f"Opportunity query/pages:    {len(opportunities)}")
    summary_txt.append(f"Opportunity pages:          {len(page_opps)}")
    summary_txt.append(f"Cannibalization review:     {len(cannibal)}")
    summary_txt.append("")
    summary_txt.append("TOP PAGE OPPORTUNITIES")
    summary_txt.append("----------------------")
    for i, r in enumerate(page_opps[:10], 1):
        summary_txt.append(
            f"{i:02d}. score={r['top_query_score']:>7}  "
            f"queries={r['opportunity_queries']:>3}  "
            f"impr={r['opportunity_impressions']:>7}  "
            f"{r['page']}"
        )
        summary_txt.append(f"    top query: {r['top_query']} [{r['top_query_flags']}]")
    summary_txt.append("")
    summary_txt.append("NOTE: opportunity_score is a local heuristic for prioritization only.")
    summary_txt.append("It is not a Google metric or ranking factor.")

    text = "\n".join(summary_txt) + "\n"
    (out_dir / "summary.txt").write_text(text, encoding="utf-8")
    print("")
    print(text)
    print(f"Reports written to: {out_dir}")


if __name__ == "__main__":
    main()
