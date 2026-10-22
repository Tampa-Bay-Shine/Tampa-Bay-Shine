from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "cloudflare-site" / "seo-dashboard" / "data"
CONFIG = ROOT / "config" / "seo-core-search.json"
OUT = DATA / "core-search.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def synthetic_query_reason(query: str):
    text = " ".join(str(query or "").strip().lower().split())
    if not text:
        return None
    operator_hits = sum(text.count(token) for token in (" or ", " and "))
    quoted_phrases = text.count('"') // 2
    parenthesized = "(" in text and ")" in text
    if parenthesized and operator_hits >= 2 and quoted_phrases >= 1:
        return "boolean_operator_pattern"
    if operator_hits >= 4 and quoted_phrases >= 2:
        return "boolean_operator_pattern"
    if len(text) >= 180 and operator_hits >= 2:
        return "long_automation_pattern"
    return None


def parse_series(history):
    result = {}
    for row in history.get("queries", []):
        query = str(row.get("query", "")).strip()
        if not query:
            continue
        points = []
        for p in row.get("points", []):
            if not isinstance(p, list) or len(p) < 5:
                continue
            d, clicks, impressions, _ctr, position = p[:5]
            points.append({
                "date": str(d),
                "clicks": float(clicks or 0),
                "impressions": float(impressions or 0),
                "position": float(position) if position is not None else None,
            })
        result[query.lower()] = {"query": query, "points": points}
    return result


def aggregate(points, start, end):
    rows = [p for p in points if start <= p["date"] <= end]
    clicks = sum(p["clicks"] for p in rows)
    impressions = sum(p["impressions"] for p in rows)
    weighted = sum(
        p["position"] * p["impressions"]
        for p in rows
        if p["position"] is not None
    )
    return {
        "clicks": round(clicks, 2),
        "impressions": round(impressions, 2),
        "ctr": round(clicks / impressions * 100, 2) if impressions else 0,
        "position": round(weighted / impressions, 2) if impressions else None,
        "observed_days": len(rows),
    }


def metric_change(current, previous):
    def pct(cur, prev):
        return None if not prev else round((cur - prev) / prev * 100, 2)
    return {
        "clicks": round(current["clicks"] - previous["clicks"], 2),
        "clicks_pct": pct(current["clicks"], previous["clicks"]),
        "impressions": round(current["impressions"] - previous["impressions"], 2),
        "impressions_pct": pct(current["impressions"], previous["impressions"]),
        "ctr_points": round(current["ctr"] - previous["ctr"], 2),
        "position": (
            round(previous["position"] - current["position"], 2)
            if previous["position"] is not None and current["position"] is not None
            else None
        ),
    }


def compare(points, end_date, days):
    end = date.fromisoformat(end_date)
    current_start = end - timedelta(days=days - 1)
    previous_end = current_start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    current = aggregate(points, current_start.isoformat(), end.isoformat())
    previous = aggregate(points, previous_start.isoformat(), previous_end.isoformat())
    return {
        "current": current,
        "previous": previous,
        "change": metric_change(current, previous),
        "range": {
            "current": [current_start.isoformat(), end.isoformat()],
            "previous": [previous_start.isoformat(), previous_end.isoformat()],
        },
    }


def combine(series, names):
    by_date = {}
    for name in names:
        record = series.get(name.lower())
        if not record:
            continue
        for p in record["points"]:
            row = by_date.setdefault(
                p["date"],
                {"date": p["date"], "clicks": 0.0, "impressions": 0.0, "weighted": 0.0},
            )
            row["clicks"] += p["clicks"]
            row["impressions"] += p["impressions"]
            if p["position"] is not None:
                row["weighted"] += p["position"] * p["impressions"]
    return [
        {
            "date": d,
            "clicks": x["clicks"],
            "impressions": x["impressions"],
            "position": x["weighted"] / x["impressions"] if x["impressions"] else None,
        }
        for d, x in sorted(by_date.items())
    ]


def confidence(metric):
    impressions = metric["impressions"]
    days = metric["observed_days"]
    if impressions >= 30 and days >= 10:
        return "high"
    if impressions >= 10 and days >= 5:
        return "medium"
    return "low"


def momentum(current, previous):
    conf = confidence(current)
    if current["position"] is None:
        return "insufficient_data"
    if previous["position"] is None:
        return "new_visibility" if current["impressions"] >= 10 else "insufficient_data"

    pos_delta = previous["position"] - current["position"]
    imp_delta = current["impressions"] - previous["impressions"]

    if conf == "low":
        return "low_sample"
    if pos_delta >= 3:
        return "improving"
    if pos_delta <= -3 and previous["impressions"] >= 10:
        return "needs_attention"
    if abs(pos_delta) < 3 and imp_delta >= max(10, previous["impressions"] * 0.25):
        return "expanding"
    return "stable"


def distribution(series, names, start, end, previous_start, previous_end):
    buckets = {
        "top_3": 0,
        "top_10": 0,
        "top_20": 0,
        "positions_21_50": 0,
        "positions_51_plus": 0,
        "no_observation": 0,
    }
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    momentum_counts = {
        "improving": 0,
        "expanding": 0,
        "stable": 0,
        "needs_attention": 0,
        "new_visibility": 0,
        "low_sample": 0,
        "insufficient_data": 0,
    }
    rows = []

    for name in names:
        record = series.get(name.lower())
        if record:
            current = aggregate(record["points"], start, end)
            previous = aggregate(record["points"], previous_start, previous_end)
        else:
            current = {"clicks": 0, "impressions": 0, "ctr": 0, "position": None, "observed_days": 0}
            previous = dict(current)

        pos = current["position"]
        if pos is None:
            bucket = "no_observation"
        elif pos <= 3:
            bucket = "top_3"
        elif pos <= 10:
            bucket = "top_10"
        elif pos <= 20:
            bucket = "top_20"
        elif pos <= 50:
            bucket = "positions_21_50"
        else:
            bucket = "positions_51_plus"

        conf = confidence(current)
        state = momentum(current, previous)
        buckets[bucket] += 1
        confidence_counts[conf] += 1
        momentum_counts[state] += 1

        rows.append({
            "query": name,
            "bucket": bucket,
            "confidence": conf,
            "momentum": state,
            "current": current,
            "previous": previous,
            "change": metric_change(current, previous),
        })

    return buckets, confidence_counts, momentum_counts, rows


def overall_status(period_7, momentum_counts):
    imp = period_7["change"]["impressions_pct"]
    pos = period_7["change"]["position"]
    attention = momentum_counts["needs_attention"]

    if attention >= 5 or (imp is not None and imp <= -20 and pos is not None and pos <= -3):
        return "needs_attention"
    if (
        (imp is not None and imp >= 10)
        and (pos is not None and pos >= 2)
        and attention <= 3
    ):
        return "improving"
    return "stable"


def main():
    history = load(DATA / "query-history.json")
    config = load(CONFIG)
    series = parse_series(history)
    end = history.get("period", {}).get("end")
    if not end:
        raise SystemExit("query-history.json has no period.end")

    configured = [str(q).strip() for q in config.get("queries", []) if str(q).strip()]
    noisy = [{"query": q, "reason": synthetic_query_reason(q)} for q in configured if synthetic_query_reason(q)]
    names = [q for q in configured if not synthetic_query_reason(q)]
    if len(names) < 20:
        raise SystemExit("Core Search Portfolio must contain at least 20 clean queries")

    cohorts = {"top_10": names[:10], "top_20": names[:20]}
    output = {
        "schema_version": 2,
        "generated_at": datetime.now().astimezone().isoformat(),
        "data_through": end,
        "source": "Google Search Console retained daily query history",
        "baseline": config.get("baseline", {}),
        "methodology": {
            "membership": "Fixed cohort; membership changes only by explicit config update/rebaseline.",
            "position": "Impression-weighted average GSC position.",
            "missing_dates": "Missing query/date observations are not treated as zero ranking.",
            "noise_filter": "Boolean/operator automation patterns are excluded from decision intelligence.",
            "confidence": {
                "high": "At least 30 impressions across at least 10 observed days in the current 28-day window.",
                "medium": "At least 10 impressions across at least 5 observed days in the current 28-day window.",
                "low": "Below the medium evidence threshold; do not treat as a reliable ranking trend.",
            },
            "momentum": "Evidence-aware classification using current vs previous 28-day position and impressions.",
        },
        "excluded_configured_queries": noisy,
        "cohorts": {},
    }

    for cohort_name, cohort_queries in cohorts.items():
        points = combine(series, cohort_queries)
        periods = {str(days): compare(points, end, days) for days in (7, 28, 90)}
        r28 = periods["28"]["range"]
        buckets, confidence_counts, momentum_counts, query_rows = distribution(
            series,
            cohort_queries,
            r28["current"][0],
            r28["current"][1],
            r28["previous"][0],
            r28["previous"][1],
        )

        reliable_top20 = sum(
            1 for row in query_rows
            if row["bucket"] in ("top_3", "top_10", "top_20")
            and row["confidence"] in ("high", "medium")
        )
        low_sample_top20 = sum(
            1 for row in query_rows
            if row["bucket"] in ("top_3", "top_10", "top_20")
            and row["confidence"] == "low"
        )

        output["cohorts"][cohort_name] = {
            "query_count": len(cohort_queries),
            "queries": cohort_queries,
            "periods": periods,
            "position_distribution_28d": buckets,
            "confidence_28d": confidence_counts,
            "momentum_28d": momentum_counts,
            "executive": {
                "overall_status": overall_status(periods["7"], momentum_counts),
                "reliable_top_20": reliable_top20,
                "low_sample_top_20": low_sample_top20,
                "high_confidence_queries": confidence_counts["high"],
                "medium_confidence_queries": confidence_counts["medium"],
                "low_confidence_queries": confidence_counts["low"],
                "improving": momentum_counts["improving"],
                "expanding": momentum_counts["expanding"],
                "stable": momentum_counts["stable"],
                "needs_attention": momentum_counts["needs_attention"],
                "new_visibility": momentum_counts["new_visibility"],
            },
            "queries_28d": query_rows,
        }

    OUT.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} through {end}")


if __name__ == "__main__":
    main()
