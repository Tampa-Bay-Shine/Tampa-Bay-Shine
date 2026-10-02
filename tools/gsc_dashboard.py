from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import gsc_performance_audit as gsc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "gsc.json"

TRACKED = [
    "house cleaning tampa",
    "house cleaning services tampa",
    "maid service tampa",
    "deep cleaning tampa",
    "move out cleaning tampa",
    "move in cleaning tampa",
    "office cleaning tampa",
    "commercial cleaning tampa",
    "apartment cleaning tampa",
]

def metrics(row):
    if not row:
        return {"clicks": 0, "impressions": 0, "ctr": 0, "position": None}
    return {
        "clicks": round(float(row.get("clicks", 0)), 2),
        "impressions": round(float(row.get("impressions", 0)), 2),
        "ctr": round(float(row.get("ctr", 0)) * 100, 2),
        "position": round(float(row.get("position", 0)), 2),
    }

def aggregate(rows):
    clicks = sum(float(r.get("clicks", 0)) for r in rows)
    impressions = sum(float(r.get("impressions", 0)) for r in rows)
    ctr = clicks / impressions * 100 if impressions else 0
    pos_num = sum(float(r.get("position", 0)) * float(r.get("impressions", 0)) for r in rows)
    pos = pos_num / impressions if impressions else None
    return {
        "clicks": round(clicks, 2),
        "impressions": round(impressions, 2),
        "ctr": round(ctr, 2),
        "position": round(pos, 2) if pos is not None else None,
    }

def summary_change(current, previous):
    """Calculate comparable GSC changes. Positive position_change means improvement."""
    def pct_change(cur, prev):
        if prev in (None, 0):
            return None
        return round(((cur - prev) / prev) * 100, 2)

    cur_clicks = current.get("clicks", 0)
    prev_clicks = previous.get("clicks", 0)
    cur_impressions = current.get("impressions", 0)
    prev_impressions = previous.get("impressions", 0)
    cur_ctr = current.get("ctr")
    prev_ctr = previous.get("ctr")
    cur_position = current.get("position")
    prev_position = previous.get("position")

    return {
        "clicks_change": round(cur_clicks - prev_clicks, 2),
        "clicks_pct_change": pct_change(cur_clicks, prev_clicks),
        "impressions_change": round(cur_impressions - prev_impressions, 2),
        "impressions_pct_change": pct_change(cur_impressions, prev_impressions),
        "ctr_change_points": (
            round(cur_ctr - prev_ctr, 2)
            if cur_ctr is not None and prev_ctr is not None
            else None
        ),
        "position_change": (
            round(prev_position - cur_position, 2)
            if cur_position is not None and prev_position is not None
            else None
        ),
    }


def fetch_period(service, site, days, lag, end_date):
    start, end, prev_start, prev_end = gsc.period(days, lag, end_date)
    cur_q = gsc.normalize_rows(gsc.fetch_rows(service, site, start, end, ["query"]), ["query"])
    prev_q = gsc.normalize_rows(gsc.fetch_rows(service, site, prev_start, prev_end, ["query"]), ["query"])
    cur_qp = gsc.normalize_rows(gsc.fetch_rows(service, site, start, end, ["query", "page"]), ["query", "page"])
    prev_qp = gsc.normalize_rows(gsc.fetch_rows(service, site, prev_start, prev_end, ["query", "page"]), ["query", "page"])
    return start, end, prev_start, prev_end, cur_q, prev_q, cur_qp, prev_qp

def main():
    ap = argparse.ArgumentParser(description="Build the Tampa Bay Shine GSC dashboard data.")
    ap.add_argument("--property", default=None)
    ap.add_argument("--host", default="tampabayshine.com")
    ap.add_argument("--days", type=int, default=28)
    ap.add_argument("--lag-days", type=int, default=3)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--client-secret", default=str(Path.home()/".tbs-gsc"/"client_secret.json"))
    ap.add_argument("--token", default=str(Path.home()/".tbs-gsc"/"token.json"))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    creds = gsc.get_credentials(Path(args.client_secret), Path(args.token))
    service, webmasters = gsc.build_services(creds)
    site = gsc.choose_property(webmasters, args.property, args.host)

    periods = {}
    period_rows = {}

    for window in (7, 28, 90):
        w_start, w_end, w_ps, w_pe, w_cq, w_pq, w_cqp, w_pqp = fetch_period(
            service, site, window, args.lag_days, args.end_date
        )

        current_summary = aggregate(w_cq)
        previous_summary = aggregate(w_pq)

        periods[str(window)] = {
            "current": {
                "start": w_start.isoformat(),
                "end": w_end.isoformat(),
                "days": window,
                "summary": current_summary,
            },
            "previous": {
                "start": w_ps.isoformat(),
                "end": w_pe.isoformat(),
                "days": window,
                "summary": previous_summary,
            },
            "change": summary_change(current_summary, previous_summary),
        }

        period_rows[window] = {
            "current_queries": w_cq,
            "previous_queries": w_pq,
            "current_query_pages": w_cqp,
            "previous_query_pages": w_pqp,
        }

    # Existing detailed dashboard tables use the 28-day window.
    start, end, ps, pe = gsc.period(28, args.lag_days, args.end_date)

    cq = period_rows[28]["current_queries"]
    pq = period_rows[28]["previous_queries"]
    cqp = period_rows[28]["current_query_pages"]
    pqp = period_rows[28]["previous_query_pages"]

    cur = {r["query"].lower(): r for r in cq}
    prev = {r["query"].lower(): r for r in pq}

    tracked = []
    for keyword in TRACKED:
        c = cur.get(keyword)
        p = prev.get(keyword)
        cm, pm = metrics(c), metrics(p)
        tracked.append({
            "query": keyword,
            "current": cm,
            "previous": pm,
            "position_change": (
                round(pm["position"] - cm["position"], 2)
                if cm["position"] is not None and pm["position"] is not None else None
            ),
        })

    qp_by_query = {}
    for r in cqp:
        qp_by_query.setdefault(r["query"].lower(), []).append(r)
    for item in tracked:
        rows = sorted(qp_by_query.get(item["query"], []), key=lambda x: -float(x.get("impressions", 0)))
        item["ranking_page"] = rows[0].get("page") if rows else None

    comp = gsc.comparison_rows(cq, pq, ["query"])
    comp.sort(key=lambda r: -float(r.get("current_impressions", 0)))
    discovered = [r for r in comp if not gsc.is_branded(r.get("query",""))][:100]

    opportunities = gsc.build_opportunities(cqp, pqp, False)[:50]
    cannibal = gsc.build_cannibalization(cqp)[:50]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "source": "Google Search Console",
        "property": site,
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": 28},
        "previous_period": {"start": ps.isoformat(), "end": pe.isoformat(), "days": 28},
        "summary": aggregate(cq),
        "previous_summary": aggregate(pq),
        "periods": periods,
        "tracked_keywords": tracked,
        "top_queries": discovered,
        "opportunities": opportunities,
        "cannibalization": cannibal,
        "limitations": "GSC average position is impression-weighted performance data, not a deterministic live SERP rank. GSC does not provide competitor or Google Maps grid rankings."
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote GSC dashboard data to {out}")
    print(f"Period: {start} to {end}")
    print(f"Queries: {len(cq)} | Query/page rows: {len(cqp)}")
    print(f"Tracked keywords with impressions: {sum(1 for x in tracked if x['current']['impressions'] > 0)}/{len(tracked)}")

if __name__ == "__main__":
    main()
