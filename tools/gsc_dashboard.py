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


def aggregate_by_dimension(rows, dimension):
    """Aggregate GSC rows to one row per query or page."""
    grouped = {}

    for row in rows:
        key = row.get(dimension)
        if not key:
            continue

        item = grouped.setdefault(key, {
            dimension: key,
            "clicks": 0.0,
            "impressions": 0.0,
            "_position_weight": 0.0,
        })

        clicks = float(row.get("clicks", 0) or 0)
        impressions = float(row.get("impressions", 0) or 0)
        position = row.get("position")

        item["clicks"] += clicks
        item["impressions"] += impressions

        if position not in (None, "") and impressions > 0:
            item["_position_weight"] += float(position) * impressions

    result = []

    for item in grouped.values():
        impressions = item["impressions"]
        clicks = item["clicks"]

        item["ctr"] = clicks / impressions if impressions else 0.0
        item["position"] = (
            item["_position_weight"] / impressions
            if impressions
            else None
        )

        del item["_position_weight"]
        result.append(item)

    return result


def build_movers(current_rows, previous_rows, dimensions, limit=25):
    """Build 28-day SEO movers with confidence and movement classifications."""
    compared = gsc.comparison_rows(current_rows, previous_rows, dimensions)
    movers = []

    for row in compared:
        current_impressions = float(row.get("current_impressions", 0) or 0)
        previous_impressions = float(row.get("previous_impressions", 0) or 0)
        current_clicks = float(row.get("current_clicks", 0) or 0)
        previous_clicks = float(row.get("previous_clicks", 0) or 0)

        current_position = row.get("current_position")
        previous_position = row.get("previous_position")
        current_ctr = row.get("current_ctr_percent")
        previous_ctr = row.get("previous_ctr_percent")

        current_position = (
            float(current_position)
            if current_position not in (None, "")
            else None
        )
        previous_position = (
            float(previous_position)
            if previous_position not in (None, "")
            else None
        )
        current_ctr = (
            float(current_ctr)
            if current_ctr not in (None, "")
            else None
        )
        previous_ctr = (
            float(previous_ctr)
            if previous_ctr not in (None, "")
            else None
        )

        total_impressions = current_impressions + previous_impressions

        # Five impressions is enough to retain a row for analysis, but
        # confidence is exposed so the UI can distinguish noisy movement.
        if total_impressions < 5:
            continue

        if total_impressions >= 50:
            confidence = "high"
        elif total_impressions >= 20:
            confidence = "medium"
        else:
            confidence = "low"

        position_change = (
            round(previous_position - current_position, 2)
            if current_position is not None and previous_position is not None
            else None
        )

        impression_change = round(
            current_impressions - previous_impressions, 2
        )
        click_change = round(
            current_clicks - previous_clicks, 2
        )

        ctr_change = (
            round(current_ctr - previous_ctr, 2)
            if current_ctr is not None and previous_ctr is not None
            else None
        )

        if previous_impressions > 0:
            impression_pct_change = round(
                (impression_change / previous_impressions) * 100, 2
            )
        else:
            impression_pct_change = None

        meaningful = (
            abs(click_change) >= 1
            or abs(impression_change) >= 5
            or (
                position_change is not None
                and abs(position_change) >= 2
                and total_impressions >= 10
            )
        )

        if not meaningful:
            continue

        # Classify the dominant business-relevant movement instead of allowing
        # a large position swing to hide a major visibility decline.
        if click_change > 0:
            movement = "winner"
            reason = "Clicks increased"
        elif click_change < 0:
            movement = "loser"
            reason = "Clicks decreased"
        elif impression_change >= 5 and (position_change or 0) >= 0:
            movement = "winner"
            reason = "Visibility increased"
        elif impression_change <= -5:
            movement = "loser"
            reason = "Visibility decreased"
        elif position_change is not None and position_change >= 2:
            movement = "winner"
            reason = "Average position improved"
        elif position_change is not None and position_change <= -2:
            movement = "loser"
            reason = "Average position declined"
        else:
            continue

        # Score magnitude is for ordering only. Classification above determines
        # whether the row is a winner or loser.
        impact_score = (
            abs(click_change) * 20
            + abs(impression_change) * 0.25
            + abs(position_change or 0) * min(total_impressions, 100) / 50
        )

        item = {dim: row.get(dim) for dim in dimensions}

        item.update({
            "movement": movement,
            "reason": reason,
            "confidence": confidence,
            "current_clicks": current_clicks,
            "previous_clicks": previous_clicks,
            "click_change": click_change,
            "current_impressions": current_impressions,
            "previous_impressions": previous_impressions,
            "impression_change": impression_change,
            "impression_pct_change": impression_pct_change,
            "current_ctr": current_ctr,
            "previous_ctr": previous_ctr,
            "ctr_change": ctr_change,
            "current_position": current_position,
            "previous_position": previous_position,
            "position_change": position_change,
            "impact_score": round(impact_score, 2),
        })

        movers.append(item)

    confidence_order = {"high": 3, "medium": 2, "low": 1}

    def sort_key(item):
        return (
            confidence_order[item["confidence"]],
            item["impact_score"],
        )

    winners = sorted(
        (x for x in movers if x["movement"] == "winner"),
        key=sort_key,
        reverse=True,
    )[:limit]

    losers = sorted(
        (x for x in movers if x["movement"] == "loser"),
        key=sort_key,
        reverse=True,
    )[:limit]

    return {
        "winners": winners,
        "losers": losers,
        "minimum_total_impressions": 5,
        "confidence": {
            "high": "50+ combined impressions",
            "medium": "20-49 combined impressions",
            "low": "5-19 combined impressions",
        },
        "method": (
            "28-day current period versus previous 28 days. "
            "Clicks take priority, followed by visibility and ranking movement. "
            "Rows with fewer than 5 combined impressions are excluded."
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

    query_movers = build_movers(cq, pq, ["query"])

    current_pages = aggregate_by_dimension(cqp, "page")
    previous_pages = aggregate_by_dimension(pqp, "page")
    page_movers = build_movers(current_pages, previous_pages, ["page"])

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
        "query_movers": query_movers,
        "page_movers": page_movers,
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
