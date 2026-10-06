from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import gsc_performance_audit as gsc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "gsc.json"
DEFAULT_QUERY_HISTORY_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "query-history.json"
DEFAULT_PAGE_HISTORY_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "page-history.json"
DEFAULT_DAILY_TOTAL_HISTORY_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "daily-total-history.json"

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



def build_action_center(
    query_movers,
    page_movers,
    query_rows,
    query_page_rows,
    previous_query_page_rows,
):
    """Build conservative deterministic SEO recommendations from GSC evidence."""
    actions = []

    def number(value, default=0.0):
        if value in (None, ""):
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def add_action(
        priority,
        category,
        subject,
        evidence,
        recommendation,
        data_level,
        query=None,
        page=None,
        previous_page=None,
    ):
        actions.append({
            "priority": priority,
            "category": category,
            "subject": subject,
            "query": query,
            "page": page,
            "previous_page": previous_page,
            "evidence": evidence,
            "recommended_action": recommendation,
            "data_level": data_level,
        })

    def strongest_query_pages(rows):
        """Return the strongest landing page observed for each query."""
        result = {}

        for row in rows:
            query = row.get("query")
            page = row.get("page")

            if not query or not page:
                continue

            impressions = number(row.get("impressions"))
            position = (
                number(row.get("position"))
                if row.get("position") not in (None, "")
                else None
            )

            candidate = {
                "page": page,
                "impressions": impressions,
                "position": position,
            }

            existing = result.get(query)

            if (
                existing is None
                or impressions > existing["impressions"]
                or (
                    impressions == existing["impressions"]
                    and position is not None
                    and (
                        existing["position"] is None
                        or position < existing["position"]
                    )
                )
            ):
                result[query] = candidate

        return result

    current_query_pages = strongest_query_pages(query_page_rows)
    previous_query_pages = strongest_query_pages(previous_query_page_rows)

    # Track pages already represented by meaningful query-level declines.
    decline_pages = set()

    # ---------------------------------------------------------
    # WINNERS: queries approaching useful organic positions
    # ---------------------------------------------------------

    for item in query_movers.get("winners", []):
        query = item.get("query")

        if not query:
            continue

        impressions = number(item.get("current_impressions"))
        impression_change = number(item.get("impression_change"))

        position = (
            number(item.get("current_position"))
            if item.get("current_position") not in (None, "")
            else None
        )

        position_change = number(item.get("position_change"))
        data_level = item.get("confidence", "low")

        ranking = current_query_pages.get(query, {})
        page = ranking.get("page")

        # Page-one bottom through page two, with enough evidence and momentum.
        if (
            position is not None
            and 8 <= position <= 20
            and impressions >= 15
            and (
                impression_change >= 8
                or position_change >= 3
            )
        ):
            add_action(
                "high" if impressions >= 25 else "medium",
                "Striking distance",
                query,
                (
                    f"Position {position:.2f}; "
                    f"{impressions:.0f} impressions; "
                    f"impressions {impression_change:+.0f}; "
                    f"position improvement {position_change:+.2f}."
                ),
                (
                    "Review the ranking landing page for search-intent alignment. "
                    "Strengthen relevant internal links and improve the section that "
                    "most directly answers this query while preserving content already "
                    "earning visibility."
                ),
                data_level,
                query=query,
                page=page,
            )

        # Require stronger growth before surfacing distant rankings.
        elif (
            position is not None
            and 20 < position <= 50
            and impressions >= 20
            and impression_change >= 15
        ):
            add_action(
                "medium",
                "Emerging opportunity",
                query,
                (
                    f"Position {position:.2f}; "
                    f"{impressions:.0f} impressions; "
                    f"impressions {impression_change:+.0f}."
                ),
                (
                    "Confirm that the best existing service or location page targets "
                    "this search intent. Strengthen relevant supporting content and "
                    "internal links. Create a new page only if the search intent is "
                    "materially different from existing coverage."
                ),
                data_level,
                query=query,
                page=page,
            )

    # ---------------------------------------------------------
    # LOSERS: meaningful query visibility declines
    # ---------------------------------------------------------

    for item in query_movers.get("losers", []):
        query = item.get("query")

        if not query:
            continue

        current_impressions = number(item.get("current_impressions"))
        previous_impressions = number(item.get("previous_impressions"))
        impression_change = number(item.get("impression_change"))
        position_change = number(item.get("position_change"))
        data_level = item.get("confidence", "low")

        current_ranking = current_query_pages.get(query, {})
        previous_ranking = previous_query_pages.get(query, {})

        page = current_ranking.get("page")
        previous_page = previous_ranking.get("page")

        # If current visibility disappeared, preserve the historical URL.
        display_page = page or previous_page

        absolute_loss = abs(min(impression_change, 0))
        loss_pct = (
            absolute_loss / previous_impressions
            if previous_impressions > 0
            else 0
        )

        # Require both meaningful prior volume and a material decline.
        if (
            previous_impressions >= 25
            and absolute_loss >= 15
            and loss_pct >= 0.30
        ):
            if display_page:
                decline_pages.add(display_page)

            priority = (
                "high"
                if previous_impressions >= 40
                and absolute_loss >= 20
                and loss_pct >= 0.40
                else "medium"
            )

            page_note = ""

            if page:
                page_note = f" Current landing page: {page}."
            elif previous_page:
                page_note = (
                    f" Current period has no ranking URL; previous landing page: "
                    f"{previous_page}."
                )

            add_action(
                priority,
                "Visibility decline",
                query,
                (
                    f"Impressions fell from {previous_impressions:.0f} "
                    f"to {current_impressions:.0f} "
                    f"({impression_change:+.0f}, "
                    f"{loss_pct * 100:.0f}% decline); "
                    f"position change {position_change:+.2f}."
                    f"{page_note}"
                ),
                (
                    "Inspect the query and landing-page history before changing "
                    "content. Determine whether the loss reflects ranking decline, "
                    "reduced search demand, indexing/canonical changes, or Google "
                    "selecting a different URL."
                ),
                data_level,
                query=query,
                page=display_page,
                previous_page=previous_page,
            )

    # ---------------------------------------------------------
    # CTR WATCH: deliberately conservative because GSC position
    # and CTR can be noisy at small impression counts.
    # ---------------------------------------------------------

    for row in query_rows:
        query = row.get("query")

        if not query:
            continue

        impressions = number(row.get("impressions"))
        clicks = number(row.get("clicks"))

        position = (
            number(row.get("position"))
            if row.get("position") not in (None, "")
            else None
        )

        if impressions <= 0 or position is None:
            continue

        ctr = clicks / impressions

        # Do not call small samples high-priority CTR problems.
        if impressions >= 50 and position <= 10 and ctr < 0.02:
            ranking = current_query_pages.get(query, {})
            page = ranking.get("page")

            add_action(
                "medium",
                "CTR watch",
                query,
                (
                    f"Position {position:.2f}; "
                    f"{impressions:.0f} impressions; "
                    f"{clicks:.0f} clicks; "
                    f"CTR {ctr * 100:.2f}%."
                ),
                (
                    "Review the actual search result and query intent before editing "
                    "metadata. If the snippet is underperforming for the intended "
                    "audience, test a clearer title or meta description without "
                    "disturbing rankings that are already strong."
                ),
                "high" if impressions >= 100 else "medium",
                query=query,
                page=page,
            )

    # ---------------------------------------------------------
    # PAGE-LEVEL DECLINES
    #
    # Suppress pages already represented by a material query
    # decline so the Action Center does not repeat the same issue.
    # ---------------------------------------------------------

    for item in page_movers.get("losers", []):
        page = item.get("page")

        if not page or page in decline_pages:
            continue

        current_impressions = number(item.get("current_impressions"))
        previous_impressions = number(item.get("previous_impressions"))
        impression_change = number(item.get("impression_change"))

        absolute_loss = abs(min(impression_change, 0))
        loss_pct = (
            absolute_loss / previous_impressions
            if previous_impressions > 0
            else 0
        )

        if (
            previous_impressions < 40
            or absolute_loss < 20
            or loss_pct < 0.35
        ):
            continue

        priority = (
            "high"
            if previous_impressions >= 60
            and absolute_loss >= 30
            else "medium"
        )

        add_action(
            priority,
            "Page visibility decline",
            page,
            (
                f"Page impressions fell from {previous_impressions:.0f} "
                f"to {current_impressions:.0f} "
                f"({impression_change:+.0f}, "
                f"{loss_pct * 100:.0f}% decline)."
            ),
            (
                "Review the queries that previously generated visibility for this "
                "URL. Check indexing, canonical status, internal links, recent "
                "content changes, and competing pages before rewriting it."
            ),
            item.get("confidence", "low"),
            page=page,
        )

    # Remove exact duplicates.
    seen = set()
    unique = []

    for item in actions:
        key = (
            item["category"],
            item.get("query"),
            item.get("page"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    category_order = {
        "Striking distance": 0,
        "Visibility decline": 1,
        "Page visibility decline": 2,
        "CTR watch": 3,
        "Emerging opportunity": 4,
    }

    unique.sort(
        key=lambda item: (
            priority_order.get(item["priority"], 9),
            category_order.get(item["category"], 9),
            item["subject"].lower(),
        )
    )

    counts = {
        "high": sum(1 for item in unique if item["priority"] == "high"),
        "medium": sum(1 for item in unique if item["priority"] == "medium"),
        "low": sum(1 for item in unique if item["priority"] == "low"),
    }

    category_counts = {}

    for item in unique:
        category = item["category"]
        category_counts[category] = category_counts.get(category, 0) + 1

    return {
        "actions": unique[:50],
        "counts": counts,
        "category_counts": category_counts,
        "method": (
            "Conservative deterministic recommendations based on current 28-day "
            "Google Search Console performance compared with the previous 28 days. "
            "Small CTR samples are treated as watch items rather than urgent issues. "
            "Query-level declines take precedence over duplicate page-level alerts. "
            "Recommendations are diagnostic prompts and do not automatically modify "
            "the website."
        ),
    }


def build_history_snapshot(payload):
    """Create a compact daily historical snapshot from dashboard data."""
    period = payload.get("period", {})
    summary = payload.get("summary", {})

    tracked = {}

    for item in payload.get("tracked_keywords", []):
        query = item.get("query")
        current = item.get("current", {})

        if not query:
            continue

        tracked[query] = {
            "position": current.get("position"),
            "impressions": current.get("impressions", 0),
            "clicks": current.get("clicks", 0),
            "ctr": current.get("ctr"),
            "ranking_page": item.get("ranking_page"),
        }

    # Preserve only the most useful page-level movers rather than
    # archiving the entire query/page GSC response every day.
    pages = {}

    page_movers = payload.get("page_movers", {})

    for group in ("winners", "losers"):
        for item in page_movers.get(group, []):
            page = item.get("page")

            if not page:
                continue

            pages[page] = {
                "position": item.get("current_position"),
                "impressions": item.get("current_impressions", 0),
                "clicks": item.get("current_clicks", 0),
                "impression_change": item.get("impression_change", 0),
                "click_change": item.get("click_change", 0),
                "position_change": item.get("position_change"),
                "movement": item.get("movement"),
                "confidence": item.get("confidence"),
            }

    action_center = payload.get("action_center", {})

    return {
        # Use the end of the GSC reporting period as the observation date.
        # This avoids labeling lagged GSC data as if it represented today's
        # search activity.
        "date": period.get("end"),
        "period_start": period.get("start"),
        "period_end": period.get("end"),
        "period_days": period.get("days", 28),
        "summary": {
            "clicks": summary.get("clicks", 0),
            "impressions": summary.get("impressions", 0),
            "ctr": summary.get("ctr", 0),
            "position": summary.get("position"),
        },
        "actions": {
            "high": action_center.get("counts", {}).get("high", 0),
            "medium": action_center.get("counts", {}).get("medium", 0),
            "low": action_center.get("counts", {}).get("low", 0),
            "total": len(action_center.get("actions", [])),
        },
        "tracked_keywords": tracked,
        "pages": pages,
    }


def update_history_file(history_path, payload, max_snapshots=400):
    """Insert or replace one historical snapshot and keep history bounded."""
    snapshot = build_history_snapshot(payload)
    snapshot_date = snapshot.get("date")

    if not snapshot_date:
        raise ValueError("Dashboard payload does not contain a history snapshot date.")

    history_path = Path(history_path)

    history = {
        "schema_version": 1,
        "max_snapshots": max_snapshots,
        "snapshots": [],
    }

    if history_path.exists():
        try:
            existing = json.loads(history_path.read_text(encoding="utf-8"))

            if isinstance(existing, dict):
                history.update(existing)

        except (json.JSONDecodeError, OSError) as exc:
            raise ValueError(
                f"Could not read existing history file {history_path}: {exc}"
            ) from exc

    snapshots = history.get("snapshots", [])

    if not isinstance(snapshots, list):
        raise ValueError("History file snapshots value must be a list.")

    # Idempotent daily update: replace the same GSC period-end date rather
    # than creating duplicates when the generator is rerun.
    snapshots = [
        item
        for item in snapshots
        if item.get("date") != snapshot_date
    ]

    snapshots.append(snapshot)

    snapshots.sort(key=lambda item: item.get("date") or "")

    if len(snapshots) > max_snapshots:
        snapshots = snapshots[-max_snapshots:]

    history["schema_version"] = 1
    history["max_snapshots"] = max_snapshots
    history["snapshots"] = snapshots
    history["latest_date"] = snapshots[-1]["date"] if snapshots else None
    history["snapshot_count"] = len(snapshots)

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return history


def fetch_period(service, site, days, lag, end_date):
    start, end, prev_start, prev_end = gsc.period(days, lag, end_date)
    cur_q = gsc.normalize_rows(gsc.fetch_rows(service, site, start, end, ["query"]), ["query"])
    prev_q = gsc.normalize_rows(gsc.fetch_rows(service, site, prev_start, prev_end, ["query"]), ["query"])
    cur_qp = gsc.normalize_rows(gsc.fetch_rows(service, site, start, end, ["query", "page"]), ["query", "page"])
    prev_qp = gsc.normalize_rows(gsc.fetch_rows(service, site, prev_start, prev_end, ["query", "page"]), ["query", "page"])
    return start, end, prev_start, prev_end, cur_q, prev_q, cur_qp, prev_qp

def build_tracked_keywords(current_queries, current_query_pages, previous_queries=None):
    """Build tracked-keyword metrics and strongest current ranking page."""
    previous_queries = previous_queries or []

    current = {
        row["query"].lower(): row
        for row in current_queries
        if row.get("query")
    }

    previous = {
        row["query"].lower(): row
        for row in previous_queries
        if row.get("query")
    }

    tracked = []

    for keyword in TRACKED:
        current_row = current.get(keyword)
        previous_row = previous.get(keyword)

        current_metrics = metrics(current_row)
        previous_metrics = metrics(previous_row)

        tracked.append({
            "query": keyword,
            "current": current_metrics,
            "previous": previous_metrics,
            "position_change": (
                round(
                    previous_metrics["position"] - current_metrics["position"],
                    2,
                )
                if current_metrics["position"] is not None
                and previous_metrics["position"] is not None
                else None
            ),
        })

    query_pages = {}

    for row in current_query_pages:
        query = row.get("query")

        if not query:
            continue

        query_pages.setdefault(query.lower(), []).append(row)

    for item in tracked:
        rows = sorted(
            query_pages.get(item["query"], []),
            key=lambda row: -float(row.get("impressions", 0)),
        )

        item["ranking_page"] = rows[0].get("page") if rows else None

    return tracked


def backfill_history(
    service,
    site,
    history_path,
    backfill_days,
    interval_days,
    lag_days,
    end_date=None,
    max_snapshots=400,
):
    """Backfill compact 28-day GSC history using real historical API data."""
    from datetime import date, datetime, timedelta

    if backfill_days < 1:
        raise ValueError("--backfill-days must be at least 1.")

    if interval_days < 1:
        raise ValueError("--backfill-interval must be at least 1.")

    if end_date:
        if isinstance(end_date, str):
            latest_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        else:
            latest_end = end_date
    else:
        latest_end = date.today() - timedelta(days=lag_days)

    earliest_end = latest_end - timedelta(days=backfill_days - 1)

    history_path = Path(history_path)

    if history_path.exists():
        history = json.loads(history_path.read_text(encoding="utf-8"))
    else:
        history = {
            "schema_version": 1,
            "max_snapshots": max_snapshots,
            "snapshots": [],
        }

    if history.get("schema_version") != 1:
        raise ValueError("Unsupported history schema_version.")

    existing = {
        item.get("date"): item
        for item in history.get("snapshots", [])
        if item.get("date")
    }

    end_dates = []
    cursor = earliest_end

    while cursor <= latest_end:
        end_dates.append(cursor)
        cursor += timedelta(days=interval_days)

    # Always include the newest available GSC date even when the interval
    # does not land exactly on it.
    if not end_dates or end_dates[-1] != latest_end:
        end_dates.append(latest_end)

    print(
        f"Backfilling {len(end_dates)} historical observations "
        f"from {end_dates[0]} through {end_dates[-1]} "
        f"at approximately {interval_days}-day intervals."
    )

    for index, snapshot_end in enumerate(end_dates, start=1):
        period_start = snapshot_end - timedelta(days=27)

        query_rows = gsc.normalize_rows(
            gsc.fetch_rows(
                service,
                site,
                period_start,
                snapshot_end,
                ["query"],
            ),
            ["query"],
        )

        query_page_rows = gsc.normalize_rows(
            gsc.fetch_rows(
                service,
                site,
                period_start,
                snapshot_end,
                ["query", "page"],
            ),
            ["query", "page"],
        )

        summary = aggregate(query_rows)

        tracked = build_tracked_keywords(
            query_rows,
            query_page_rows,
        )

        tracked_history = {}

        for item in tracked:
            query = item.get("query")
            current = item.get("current", {})

            if not query:
                continue

            tracked_history[query] = {
                "position": current.get("position"),
                "impressions": current.get("impressions", 0),
                "clicks": current.get("clicks", 0),
                "ctr": current.get("ctr", 0),
                "ranking_page": item.get("ranking_page"),
            }

        # Preserve fields from an existing same-date snapshot where
        # appropriate, especially Action Center counts generated by the
        # full daily dashboard build.
        old = existing.get(snapshot_end.isoformat(), {})

        snapshot = {
            "date": snapshot_end.isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": snapshot_end.isoformat(),
            "period_days": 28,
            "summary": summary,
            "actions": old.get(
                "actions",
                {
                    "high": None,
                    "medium": None,
                    "low": None,
                    "total": None,
                },
            ),
            "tracked_keywords": tracked_history,
            "pages": old.get("pages", {}),
        }

        existing[snapshot["date"]] = snapshot

        print(
            f"[{index}/{len(end_dates)}] {snapshot['date']} | "
            f"clicks={summary.get('clicks', 0)} | "
            f"impressions={summary.get('impressions', 0)} | "
            f"tracked={sum(1 for value in tracked_history.values() if value.get('impressions', 0) > 0)}"
        )

    snapshots = sorted(
        existing.values(),
        key=lambda item: item.get("date", ""),
    )

    if len(snapshots) > max_snapshots:
        snapshots = snapshots[-max_snapshots:]

    history = {
        "schema_version": 1,
        "max_snapshots": max_snapshots,
        "snapshots": snapshots,
    }

    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(history, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(
        f"History backfill complete: {history_path} | "
        f"{len(snapshots)} snapshots | "
        f"{snapshots[0]['date'] if snapshots else '--'} to "
        f"{snapshots[-1]['date'] if snapshots else '--'}"
    )




def build_daily_total_history(service, site, start_date, end_date):
    """Fetch authoritative site-wide daily GSC totals using date only."""
    from datetime import datetime
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    rows = gsc.normalize_rows(
        gsc.fetch_rows(service, site, start_date, end_date, ["date"]),
        ["date"],
    )
    points = []
    for row in rows:
        d = row.get("date")
        if not d:
            continue
        clicks = float(row.get("clicks", 0) or 0)
        impressions = float(row.get("impressions", 0) or 0)
        position = row.get("position")
        position = float(position) if position not in (None, "") else None
        ctr = clicks / impressions * 100 if impressions else 0.0
        points.append([
            d, round(clicks,2), round(impressions,2), round(ctr,4),
            round(position,2) if position is not None else None
        ])
    points.sort(key=lambda x:x[0])
    return {
        "schema_version":1,
        "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "source":"Google Search Console",
        "property":site,
        "period":{"start":start_date.isoformat(),"end":end_date.isoformat()},
        "granularity":"day",
        "point_columns":["date","clicks","impressions","ctr","position"],
        "points":points,
        "limitations":"Site-wide daily totals fetched with date as the only dimension. Use these for headline Performance Intelligence metrics; query-level GSC data may omit anonymized or low-volume queries."
    }

def write_daily_total_history(service, site, output_path, days=365, lag_days=3, end_date=None):
    """Write authoritative site-wide daily GSC totals."""
    from datetime import date, datetime, timedelta
    if end_date:
        latest = datetime.strptime(end_date,"%Y-%m-%d").date() if isinstance(end_date,str) else end_date
    else:
        latest = date.today() - timedelta(days=lag_days)
    earliest = latest - timedelta(days=days-1)
    payload = build_daily_total_history(service,site,earliest,latest)
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    output_path.write_text(json.dumps(payload,separators=(",",":"),ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Daily total history: {output_path} | {len(payload['points'])} points | {payload['period']['start']} to {payload['period']['end']}")
    return payload


def build_daily_query_history(
    service,
    site,
    start_date,
    end_date,
    tracked_queries=None,
    required_queries=None,
    minimum_impressions=20,
):
    """Fetch compact real daily GSC query metrics for trend charts."""
    from datetime import datetime

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    tracked_queries = {
        value.lower()
        for value in (tracked_queries or [])
        if value
    }

    required_queries = {
        value.lower()
        for value in (required_queries or [])
        if value
    }

    required_queries.update(tracked_queries)

    rows = gsc.normalize_rows(
        gsc.fetch_rows(
            service,
            site,
            start_date,
            end_date,
            ["date", "query"],
        ),
        ["date", "query"],
    )

    by_query = {}

    for row in rows:
        query = row.get("query")
        observation_date = row.get("date")

        if not query or not observation_date:
            continue

        key = query.lower()

        item = by_query.setdefault(
            key,
            {
                "query": query,
                "tracked": key in tracked_queries,
                "points": [],
                "_clicks": 0.0,
                "_impressions": 0.0,
                "_position_weight": 0.0,
            },
        )

        clicks = float(row.get("clicks", 0) or 0)
        impressions = float(row.get("impressions", 0) or 0)
        position = row.get("position")
        position = (
            float(position)
            if position not in (None, "")
            else None
        )

        ctr = (
            clicks / impressions * 100
            if impressions
            else 0.0
        )

        item["points"].append([
            observation_date,
            round(clicks, 2),
            round(impressions, 2),
            round(ctr, 2),
            round(position, 2) if position is not None else None,
        ])

        item["_clicks"] += clicks
        item["_impressions"] += impressions

        if position is not None and impressions:
            item["_position_weight"] += position * impressions

    queries = []

    for key, item in by_query.items():
        impressions = item["_impressions"]

        if (
            impressions < minimum_impressions
            and key not in required_queries
        ):
            continue

        clicks = item["_clicks"]

        item["points"].sort(key=lambda point: point[0])

        item["summary"] = {
            "clicks": round(clicks, 2),
            "impressions": round(impressions, 2),
            "ctr": round(
                clicks / impressions * 100,
                2,
            ) if impressions else 0.0,
            "position": round(
                item["_position_weight"] / impressions,
                2,
            ) if impressions else None,
        }

        del item["_clicks"]
        del item["_impressions"]
        del item["_position_weight"]

        queries.append(item)

    queries.sort(
        key=lambda item: (
            item["summary"]["impressions"],
            item["summary"]["clicks"],
        ),
        reverse=True,
    )

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        "source": "Google Search Console",
        "property": site,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "granularity": "day",
        "point_columns": [
            "date",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ],
        "retention": {
            "minimum_impressions": minimum_impressions,
            "always_include_tracked": True,
            "always_include_dashboard_queries": True,
        },
        "queries": queries,
        "query_count": len(queries),
        "limitations": (
            "Daily query rows are Google Search Console performance data. "
            "Google may omit anonymized or very low-volume queries. Average "
            "position is impression-weighted and is not a deterministic live "
            "SERP rank. Queries below the retention threshold are omitted "
            "unless tracked or currently used by dashboard analysis."
        ),
    }


def dashboard_required_queries(payload):
    """Collect queries that must retain trend history for dashboard rows."""
    result = set()

    for item in payload.get("tracked_keywords", []):
        if item.get("query"):
            result.add(item["query"])

    for item in payload.get("top_queries", []):
        if item.get("query"):
            result.add(item["query"])

    for group in ("winners", "losers"):
        for item in payload.get("query_movers", {}).get(group, []):
            if item.get("query"):
                result.add(item["query"])

    for item in payload.get("opportunities", []):
        if item.get("query"):
            result.add(item["query"])

    for item in payload.get("action_center", {}).get("actions", []):
        if item.get("query"):
            result.add(item["query"])

    return result


def write_daily_query_history(
    service,
    site,
    output_path,
    dashboard_payload,
    days=365,
    lag_days=3,
    end_date=None,
    minimum_impressions=20,
    refresh_days=7,
):
    """Create or incrementally refresh compact daily GSC query history."""
    from datetime import date, datetime, timedelta

    if days < 1:
        raise ValueError("--query-history-days must be at least 1.")

    if refresh_days < 1:
        raise ValueError("--query-history-refresh-days must be at least 1.")

    if end_date:
        if isinstance(end_date, str):
            latest = datetime.strptime(
                end_date,
                "%Y-%m-%d",
            ).date()
        else:
            latest = end_date
    else:
        latest = date.today() - timedelta(days=lag_days)

    earliest = latest - timedelta(days=days - 1)

    output_path = Path(output_path)
    required = dashboard_required_queries(dashboard_payload)

    existing = None

    if output_path.exists():
        try:
            existing = json.loads(
                output_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            existing = None

    use_incremental = (
        existing
        and existing.get("schema_version") == 2
        and existing.get("property") == site
        and existing.get("point_columns") == [
            "date",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ]
    )

    if use_incremental:
        refresh_start = max(
            earliest,
            latest - timedelta(days=refresh_days - 1),
        )

        fresh = build_daily_query_history(
            service=service,
            site=site,
            start_date=refresh_start,
            end_date=latest,
            tracked_queries=TRACKED,
            required_queries=required,
            minimum_impressions=0,
        )

        merged = {}

        # Keep existing observations outside the refresh window.
        for item in existing.get("queries", []):
            query = item.get("query")
            if not query:
                continue

            key = query.lower()

            target = merged.setdefault(
                key,
                {
                    "query": query,
                    "tracked": key in {
                        value.lower() for value in TRACKED
                    },
                    "points": {},
                },
            )

            for point in item.get("points", []):
                if not point:
                    continue

                point_date = point[0]

                if (
                    earliest.isoformat()
                    <= point_date
                    < refresh_start.isoformat()
                ):
                    target["points"][point_date] = point

        # Replace the overlap with newly fetched GSC observations.
        for item in fresh.get("queries", []):
            query = item.get("query")
            if not query:
                continue

            key = query.lower()

            target = merged.setdefault(
                key,
                {
                    "query": query,
                    "tracked": key in {
                        value.lower() for value in TRACKED
                    },
                    "points": {},
                },
            )

            target["query"] = query

            for point in item.get("points", []):
                if point:
                    target["points"][point[0]] = point

        queries = []

        for key, item in merged.items():
            points = sorted(
                item["points"].values(),
                key=lambda point: point[0],
            )

            clicks = sum(float(point[1] or 0) for point in points)
            impressions = sum(float(point[2] or 0) for point in points)

            position_weight = sum(
                float(point[4]) * float(point[2] or 0)
                for point in points
                if point[4] is not None and float(point[2] or 0)
            )

            if (
                impressions < minimum_impressions
                and key not in {
                    value.lower() for value in required
                }
            ):
                continue

            queries.append({
                "query": item["query"],
                "tracked": key in {
                    value.lower() for value in TRACKED
                },
                "points": points,
                "summary": {
                    "clicks": round(clicks, 2),
                    "impressions": round(impressions, 2),
                    "ctr": round(
                        clicks / impressions * 100,
                        2,
                    ) if impressions else 0.0,
                    "position": round(
                        position_weight / impressions,
                        2,
                    ) if impressions else None,
                },
            })

        queries.sort(
            key=lambda item: (
                item["summary"]["impressions"],
                item["summary"]["clicks"],
            ),
            reverse=True,
        )

        payload = {
            "schema_version": 2,
            "generated_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            "source": "Google Search Console",
            "property": site,
            "period": {
                "start": earliest.isoformat(),
                "end": latest.isoformat(),
            },
            "granularity": "day",
            "point_columns": [
                "date",
                "clicks",
                "impressions",
                "ctr",
                "position",
            ],
            "retention": {
                "minimum_impressions": minimum_impressions,
                "always_include_tracked": True,
                "always_include_dashboard_queries": True,
            },
            "refresh": {
                "mode": "incremental",
                "start": refresh_start.isoformat(),
                "end": latest.isoformat(),
                "days": refresh_days,
            },
            "queries": queries,
            "query_count": len(queries),
            "limitations": (
                "Daily query rows are Google Search Console performance data. "
                "Google may omit anonymized or very low-volume queries. Average "
                "position is impression-weighted and is not a deterministic live "
                "SERP rank. Queries below the retention threshold are omitted "
                "unless tracked or currently used by dashboard analysis."
            ),
        }

    else:
        payload = build_daily_query_history(
            service=service,
            site=site,
            start_date=earliest,
            end_date=latest,
            tracked_queries=TRACKED,
            required_queries=required,
            minimum_impressions=minimum_impressions,
        )

        payload["refresh"] = {
            "mode": "full",
            "start": earliest.isoformat(),
            "end": latest.isoformat(),
            "days": days,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    point_count = sum(
        len(item.get("points", []))
        for item in payload["queries"]
    )

    print(
        f"Query history: {output_path} | "
        f"{payload['query_count']} queries | "
        f"{point_count} daily points | "
        f"{payload['period']['start']} to "
        f"{payload['period']['end']} | "
        f"{payload['refresh']['mode']} refresh "
        f"{payload['refresh']['start']} to "
        f"{payload['refresh']['end']}"
    )

    return payload


def dashboard_required_pages(payload):
    """Collect pages that need daily trend history for dashboard rows."""
    result = set()

    for group in ("winners", "losers"):
        for item in payload.get("page_movers", {}).get(group, []):
            page = item.get("page")
            if page:
                result.add(page)

    for item in payload.get("tracked_keywords", []):
        page = item.get("ranking_page")
        if page:
            result.add(page)

    for item in payload.get("opportunities", []):
        page = item.get("page")
        if page:
            result.add(page)

    return result


def build_daily_page_history(
    service,
    site,
    start_date,
    end_date,
    required_pages=None,
    minimum_impressions=20,
):
    """Fetch compact real daily GSC page metrics for trend charts."""
    from datetime import datetime

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    required_pages = {
        value
        for value in (required_pages or [])
        if value
    }

    rows = gsc.normalize_rows(
        gsc.fetch_rows(
            service,
            site,
            start_date,
            end_date,
            ["date", "page"],
        ),
        ["date", "page"],
    )

    by_page = {}

    for row in rows:
        page = row.get("page")
        observation_date = row.get("date")

        if not page or not observation_date:
            continue

        item = by_page.setdefault(
            page,
            {
                "page": page,
                "points": [],
                "_clicks": 0.0,
                "_impressions": 0.0,
                "_position_weight": 0.0,
            },
        )

        clicks = float(row.get("clicks", 0) or 0)
        impressions = float(row.get("impressions", 0) or 0)

        position = row.get("position")
        position = (
            float(position)
            if position not in (None, "")
            else None
        )

        ctr = (
            clicks / impressions * 100
            if impressions
            else 0.0
        )

        item["points"].append([
            observation_date,
            round(clicks, 2),
            round(impressions, 2),
            round(ctr, 2),
            round(position, 2) if position is not None else None,
        ])

        item["_clicks"] += clicks
        item["_impressions"] += impressions

        if position is not None and impressions:
            item["_position_weight"] += position * impressions

    pages = []

    for page, item in by_page.items():
        impressions = item["_impressions"]

        if (
            impressions < minimum_impressions
            and page not in required_pages
        ):
            continue

        clicks = item["_clicks"]

        item["points"].sort(key=lambda point: point[0])

        item["summary"] = {
            "clicks": round(clicks, 2),
            "impressions": round(impressions, 2),
            "ctr": round(
                clicks / impressions * 100,
                2,
            ) if impressions else 0.0,
            "position": round(
                item["_position_weight"] / impressions,
                2,
            ) if impressions else None,
        }

        del item["_clicks"]
        del item["_impressions"]
        del item["_position_weight"]

        pages.append(item)

    pages.sort(
        key=lambda item: (
            item["summary"]["impressions"],
            item["summary"]["clicks"],
        ),
        reverse=True,
    )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        "source": "Google Search Console",
        "property": site,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "granularity": "day",
        "point_columns": [
            "date",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ],
        "retention": {
            "minimum_impressions": minimum_impressions,
            "always_include_dashboard_pages": True,
        },
        "pages": pages,
        "page_count": len(pages),
        "limitations": (
            "Daily page rows are Google Search Console performance data. "
            "Average position is impression-weighted and is not a "
            "deterministic live SERP rank."
        ),
    }


def write_daily_page_history(
    service,
    site,
    output_path,
    dashboard_payload,
    days=365,
    lag_days=3,
    end_date=None,
    minimum_impressions=20,
    refresh_days=7,
):
    """Create or incrementally refresh compact daily GSC page history."""
    from datetime import date, datetime, timedelta

    if days < 1:
        raise ValueError("--page-history-days must be at least 1.")

    if refresh_days < 1:
        raise ValueError("--page-history-refresh-days must be at least 1.")

    if end_date:
        if isinstance(end_date, str):
            latest = datetime.strptime(
                end_date,
                "%Y-%m-%d",
            ).date()
        else:
            latest = end_date
    else:
        latest = date.today() - timedelta(days=lag_days)

    earliest = latest - timedelta(days=days - 1)
    required = dashboard_required_pages(dashboard_payload)

    output_path = Path(output_path)

    existing = None

    if output_path.exists():
        try:
            existing = json.loads(
                output_path.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            existing = None

    use_incremental = (
        existing
        and existing.get("schema_version") == 1
        and existing.get("property") == site
        and existing.get("point_columns") == [
            "date",
            "clicks",
            "impressions",
            "ctr",
            "position",
        ]
    )

    if use_incremental:
        refresh_start = max(
            earliest,
            latest - timedelta(days=refresh_days - 1),
        )

        fresh = build_daily_page_history(
            service=service,
            site=site,
            start_date=refresh_start,
            end_date=latest,
            required_pages=required,
            minimum_impressions=0,
        )

        merged = {}

        for item in existing.get("pages", []):
            page = item.get("page")
            if not page:
                continue

            target = merged.setdefault(
                page,
                {
                    "page": page,
                    "points": {},
                },
            )

            for point in item.get("points", []):
                if not point:
                    continue

                point_date = point[0]

                if (
                    earliest.isoformat()
                    <= point_date
                    < refresh_start.isoformat()
                ):
                    target["points"][point_date] = point

        for item in fresh.get("pages", []):
            page = item.get("page")
            if not page:
                continue

            target = merged.setdefault(
                page,
                {
                    "page": page,
                    "points": {},
                },
            )

            for point in item.get("points", []):
                if point:
                    target["points"][point[0]] = point

        pages = []

        for page, item in merged.items():
            points = sorted(
                item["points"].values(),
                key=lambda point: point[0],
            )

            clicks = sum(float(point[1] or 0) for point in points)
            impressions = sum(float(point[2] or 0) for point in points)

            position_weight = sum(
                float(point[4]) * float(point[2] or 0)
                for point in points
                if point[4] is not None and float(point[2] or 0)
            )

            if (
                impressions < minimum_impressions
                and page not in required
            ):
                continue

            pages.append({
                "page": page,
                "points": points,
                "summary": {
                    "clicks": round(clicks, 2),
                    "impressions": round(impressions, 2),
                    "ctr": round(
                        clicks / impressions * 100,
                        2,
                    ) if impressions else 0.0,
                    "position": round(
                        position_weight / impressions,
                        2,
                    ) if impressions else None,
                },
            })

        pages.sort(
            key=lambda item: (
                item["summary"]["impressions"],
                item["summary"]["clicks"],
            ),
            reverse=True,
        )

        payload = {
            "schema_version": 1,
            "generated_at": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            "source": "Google Search Console",
            "property": site,
            "period": {
                "start": earliest.isoformat(),
                "end": latest.isoformat(),
            },
            "granularity": "day",
            "point_columns": [
                "date",
                "clicks",
                "impressions",
                "ctr",
                "position",
            ],
            "retention": {
                "minimum_impressions": minimum_impressions,
                "always_include_dashboard_pages": True,
            },
            "refresh": {
                "mode": "incremental",
                "start": refresh_start.isoformat(),
                "end": latest.isoformat(),
                "days": refresh_days,
            },
            "pages": pages,
            "page_count": len(pages),
            "limitations": (
                "Daily page rows are Google Search Console performance data. "
                "Average position is impression-weighted and is not a "
                "deterministic live SERP rank."
            ),
        }

    else:
        payload = build_daily_page_history(
            service=service,
            site=site,
            start_date=earliest,
            end_date=latest,
            required_pages=required,
            minimum_impressions=minimum_impressions,
        )

        payload["refresh"] = {
            "mode": "full",
            "start": earliest.isoformat(),
            "end": latest.isoformat(),
            "days": days,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            payload,
            separators=(",", ":"),
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    point_count = sum(
        len(item.get("points", []))
        for item in payload["pages"]
    )

    print(
        f"Page history: {output_path} | "
        f"{payload['page_count']} pages | "
        f"{point_count} daily points | "
        f"{payload['period']['start']} to "
        f"{payload['period']['end']} | "
        f"{payload['refresh']['mode']} refresh "
        f"{payload['refresh']['start']} to "
        f"{payload['refresh']['end']}"
    )

    return payload

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
    ap.add_argument(
        "--history-out",
        default=str(DEFAULT_OUT.parent / "history.json"),
        help="Path to compact historical dashboard snapshots.",
    )
    ap.add_argument(
        "--daily-total-history-out",
        default=str(DEFAULT_DAILY_TOTAL_HISTORY_OUT),
        help="Path to authoritative site-wide daily GSC totals.",
    )
    ap.add_argument(
        "--daily-total-history-days",
        type=int,
        default=365,
        help="Number of calendar days of authoritative daily GSC totals to retain.",
    )
    ap.add_argument(
        "--query-history-out",
        default=str(DEFAULT_QUERY_HISTORY_OUT),
        help="Path to daily query-level GSC history.",
    )
    ap.add_argument(
        "--query-history-days",
        type=int,
        default=365,
        help="Number of calendar days of daily query history to retrieve.",
    )
    ap.add_argument(
        "--query-history-refresh-days",
        type=int,
        default=7,
        help="Recent GSC days to refetch when query history already exists.",
    )
    ap.add_argument(
        "--page-history-out",
        default=str(DEFAULT_PAGE_HISTORY_OUT),
        help="Path to daily page-level GSC history.",
    )
    ap.add_argument(
        "--page-history-days",
        type=int,
        default=365,
        help="Number of calendar days of daily page history to retain.",
    )
    ap.add_argument(
        "--page-history-refresh-days",
        type=int,
        default=7,
        help="Recent GSC days to refetch when page history already exists.",
    )
    ap.add_argument(
        "--backfill-history",
        action="store_true",
        help="Backfill real historical 28-day GSC snapshots and exit.",
    )
    ap.add_argument(
        "--backfill-days",
        type=int,
        default=180,
        help="Calendar span to backfill when --backfill-history is used.",
    )
    ap.add_argument(
        "--backfill-interval",
        type=int,
        default=7,
        help="Days between historical observations during backfill.",
    )
    args = ap.parse_args()

    creds = gsc.get_credentials(Path(args.client_secret), Path(args.token))
    service, webmasters = gsc.build_services(creds)
    site = gsc.choose_property(webmasters, args.property, args.host)

    if args.backfill_history:
        backfill_history(
            service=service,
            site=site,
            history_path=Path(args.history_out),
            backfill_days=args.backfill_days,
            interval_days=args.backfill_interval,
            lag_days=args.lag_days,
            end_date=args.end_date,
        )
        return

    periods = {}
    period_rows = {}

    for window in (7, 28, 90):
        w_start, w_end, w_ps, w_pe, w_cq, w_pq, w_cqp, w_pqp = fetch_period(
            service, site, window, args.lag_days, args.end_date
        )

        # Site-wide headline totals must not be derived from query rows.
        w_current_total = gsc.normalize_rows(
            gsc.fetch_rows(service, site, w_start, w_end, []), []
        )
        w_previous_total = gsc.normalize_rows(
            gsc.fetch_rows(service, site, w_ps, w_pe, []), []
        )
        current_summary = aggregate(w_current_total)
        previous_summary = aggregate(w_previous_total)

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

    action_center = build_action_center(
        query_movers,
        page_movers,
        cq,
        cqp,
        pqp,
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "source": "Google Search Console",
        "property": site,
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": 28},
        "previous_period": {"start": ps.isoformat(), "end": pe.isoformat(), "days": 28},
        "summary": periods["28"]["current"]["summary"],
        "previous_summary": periods["28"]["previous"]["summary"],
        "periods": periods,
        "tracked_keywords": tracked,
        "top_queries": discovered,
        "opportunities": opportunities,
        "cannibalization": cannibal,
        "query_movers": query_movers,
        "page_movers": page_movers,
        "action_center": action_center,
        "limitations": "GSC average position is impression-weighted performance data, not a deterministic live SERP rank. GSC does not provide competitor or Google Maps grid rankings."
    }
    write_daily_total_history(
        service=service,
        site=site,
        output_path=Path(args.daily_total_history_out),
        days=args.daily_total_history_days,
        lag_days=args.lag_days,
        end_date=args.end_date,
    )

    write_daily_query_history(
        service=service,
        site=site,
        output_path=Path(args.query_history_out),
        dashboard_payload=payload,
        days=args.query_history_days,
        lag_days=args.lag_days,
        end_date=args.end_date,
        refresh_days=args.query_history_refresh_days,
    )

    write_daily_page_history(
        service=service,
        site=site,
        output_path=Path(args.page_history_out),
        dashboard_payload=payload,
        days=args.page_history_days,
        lag_days=args.lag_days,
        end_date=args.end_date,
        refresh_days=args.page_history_refresh_days,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    history_path = Path(args.history_out)
    history = update_history_file(history_path, payload)

    print(
        f"History: {history_path} | "
        f"{history['snapshot_count']} snapshots | "
        f"latest {history['latest_date']}"
    )
    print(f"Wrote GSC dashboard data to {out}")
    print(f"Period: {start} to {end}")
    print(f"Queries: {len(cq)} | Query/page rows: {len(cqp)}")
    print(f"Tracked keywords with impressions: {sum(1 for x in tracked if x['current']['impressions'] > 0)}/{len(tracked)}")

if __name__ == "__main__":
    main()
