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

    start, end, ps, pe, cq, pq, cqp, pqp = fetch_period(
        service, site, args.days, args.lag_days, args.end_date
    )

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
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": args.days},
        "previous_period": {"start": ps.isoformat(), "end": pe.isoformat(), "days": args.days},
        "summary": aggregate(cq),
        "previous_summary": aggregate(pq),
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
