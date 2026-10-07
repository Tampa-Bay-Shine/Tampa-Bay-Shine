from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "cloudflare-site" / "seo-dashboard" / "data"

DEFAULT_GSC = DATA_DIR / "gsc.json"
DEFAULT_GA4 = DATA_DIR / "ga4.json"
DEFAULT_AI = DATA_DIR / "ai.json"
DEFAULT_AI_VISIBILITY = DATA_DIR / "ai-visibility.json"
DEFAULT_EVENTS = DATA_DIR / "events.json"
DEFAULT_QUERY_HISTORY = DATA_DIR / "query-history.json"
DEFAULT_OUT = DATA_DIR / "opportunity-intelligence.json"

MEASUREMENT_BOUNDARY = "2026-10-05"
DEPRIORITIZED_QUERY_TERMS = ("floor cleaning", "floor stripping", "floor waxing", "stripping and waxing")

COMMERCIAL_TERMS = (
    "cleaning",
    "cleaner",
    "cleaners",
    "maid",
    "maids",
    "housekeeping",
    "janitorial",
)

SERVICE_TERMS = (
    "house",
    "home",
    "deep",
    "move out",
    "move-out",
    "move in",
    "move-in",
    "office",
    "commercial",
    "apartment",
    "airbnb",
    "restroom",
    "post construction",
    "post-construction",
)


def load_json(path: Path, default=None):
    if default is None:
        default = {}

    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def number(value, default=0.0):
    if value in (None, ""):
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_path(value):
    if not value:
        return None

    if value.startswith("http://") or value.startswith("https://"):
        value = urlparse(value).path or "/"

    if not value.startswith("/"):
        value = "/" + value

    if len(value) > 1:
        value = value.rstrip("/")

    return value


def is_commercial_query(query):
    text = str(query or "").lower()
    return (
        any(term in text for term in COMMERCIAL_TERMS)
        and any(term in text for term in SERVICE_TERMS)
    )


def post_boundary_context(query, query_history, boundary=MEASUREMENT_BOUNDARY):
    """Summarize observed query rows on/after the measurement boundary."""
    if not query:
        return None
    rows = {str(x.get("query") or "").strip().lower(): x for x in query_history.get("queries", [])}
    row = rows.get(str(query).strip().lower())
    history_end = (query_history.get("period") or {}).get("end")
    points = [p for p in ((row or {}).get("points") or []) if p and str(p[0]) >= boundary]
    impressions = sum(number(p[2]) for p in points)
    clicks = sum(number(p[1]) for p in points)
    position = (sum(number(p[4]) * number(p[2]) for p in points) / impressions) if impressions else None
    if history_end and history_end < boundary:
        status = "awaiting_post_boundary_data"
    elif not row:
        status = "query_not_retained"
    elif not points:
        status = "no_observed_post_boundary_rows"
    elif impressions < 15:
        status = "insufficient_post_boundary_volume"
    else:
        status = "post_boundary_evidence_available"
    return {"boundary": boundary, "history_end": history_end, "status": status,
            "observed_days": len(points), "impressions": impressions, "clicks": clicks,
            "ctr_percent": round(clicks / impressions * 100, 2) if impressions else None,
            "position": round(position, 2) if position is not None else None}


def business_priority_context(query=None, page=None):
    page_text = (normalize_path(page) or "").lower()
    page_text = page_text.replace("-", " ").replace("_", " ").replace("/", " ")
    text = " ".join([
        str(query or "").lower(),
        page_text,
    ])
    text = " ".join(text.split())
    matched = next((term for term in DEPRIORITIZED_QUERY_TERMS if term in text), None)
    return {"status": "deprioritized" if matched else "active", "matched_term": matched,
            "reason": "Service is not a current business focus." if matched else None}


def landing_page_map(ga4):
    result = {}

    for row in ga4.get("landing_pages", []):
        path = normalize_path(row.get("landing_page"))

        if path:
            result[path] = row

    return result


def conversion_context(page, ga4_pages, ga4):
    path = normalize_path(page)
    row = ga4_pages.get(path)

    if row:
        sessions = number(row.get("sessions"))
        starts = number(row.get("booknow_click"))
        confirmed = number(row.get("confirmed_bookings"))

        return {
            "scope": "landing_page",
            "path": path,
            "sessions": sessions,
            "booking_starts": starts,
            "confirmed_bookings": confirmed,
            "booking_start_rate": row.get("booking_start_rate"),
            "confirmed_booking_rate": row.get("confirmed_booking_rate"),
            "note": (
                "GA4 Organic Search landing-page evidence for the ranking URL. "
                "Event counts are not unique-user probabilities."
            ),
        }

    period = ga4.get("periods", {}).get("28", {})
    overview = period.get("overview", {}).get("current", {})
    intent = period.get("intent", {}).get("current", {})
    confirmed = period.get("confirmed_bookings", {}).get("current", {})

    return {
        "scope": "organic_sitewide",
        "path": path,
        "sessions": number(overview.get("sessions")),
        "booking_starts": number(intent.get("booknow_click")),
        "confirmed_bookings": number(confirmed.get("confirmed_bookings")),
        "booking_start_rate": overview.get("booking_start_rate"),
        "confirmed_booking_rate": overview.get("confirmed_booking_rate"),
        "note": (
            "No matching GA4 Organic Search landing-page row was available, "
            "so this is sitewide Organic Search context rather than page attribution."
        ),
    }


def measurement_plan(query=None, page=None):
    subject = query or page or "the affected search opportunity"

    return {
        "30_days": (
            f"Recheck impressions, clicks, CTR, and average position for {subject}. "
            "Confirm that Google is still selecting the intended landing page."
        ),
        "60_days": (
            "Compare the next 28-day period with the prior period. Review Organic "
            "Search landing-page sessions and booking-start intent without treating "
            "a small sample as proof of causation."
        ),
        "90_days": (
            "Evaluate sustained search visibility plus Organic Search booking starts "
            "and confirmed bookings. Keep, refine, or reverse the change based on "
            "the combined evidence."
        ),
    }


def event_context(events, page=None):
    page = page or ""
    matches = []

    for event in events.get("events", []):
        urls = event.get("urls", []) or []

        if page and page in urls:
            matches.append({
                "date": event.get("date"),
                "category": event.get("category"),
                "title": event.get("title"),
            })

    return matches[-3:]


def stable_opportunity_id(
    opportunity_type,
    subject,
    query=None,
    page=None,
):
    identity = "|".join([
        str(opportunity_type or "").strip().lower(),
        str(query or "").strip().lower(),
        normalize_path(page) or "",
        str(subject or "").strip().lower(),
    ])

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()[:16]

    return f"opp-{digest}"


def build_intelligence(gsc, ga4, ai, ai_visibility, events, query_history):
    ga4_pages = landing_page_map(ga4)
    items = []
    seen = set()

    def add(
        opportunity_type,
        priority,
        subject,
        why_flagged,
        evidence,
        recommended_action,
        query=None,
        page=None,
        confidence="medium",
    ):
        key = (opportunity_type, query or "", page or "", subject)

        if key in seen:
            return

        seen.add(key)

        post_change = post_boundary_context(query, query_history)
        business_priority = business_priority_context(query=query, page=page)
        decision_status = "actionable"
        if query and post_change and post_change["status"] != "post_boundary_evidence_available":
            decision_status = "awaiting_post_change_evidence"
            if priority == "high":
                priority = "medium"
            if confidence in ("high", "medium"):
                confidence = "low"
            recommended_action = (
                f"Awaiting post-change evidence. Hold site changes until enough GSC "
                f"evidence exists after the {MEASUREMENT_BOUNDARY} measurement boundary. "
                + recommended_action
            )
        if business_priority["status"] == "deprioritized":
            priority = "low"
            confidence = "low"
            recommended_action = (
                "Retain measurement, but do not optimize this query while the service is "
                "not a current business focus."
            )

        items.append({
            "id": stable_opportunity_id(
                opportunity_type,
                subject,
                query=query,
                page=page,
            ),
            "type": opportunity_type,
            "priority": priority,
            "confidence": confidence,
            "subject": subject,
            "query": query,
            "page": page,
            "why_flagged": why_flagged,
            "evidence": evidence,
            "post_change_evidence": post_change,
            "decision_status": decision_status,
            "business_priority": business_priority,
            "conversion_context": conversion_context(page, ga4_pages, ga4),
            "recommended_action": recommended_action,
            "measurement": measurement_plan(query=query, page=page),
            "seo_events": event_context(events, page=page),
        })

    # ---------------------------------------------------------
    # 1. Commercial striking-distance queries
    # ---------------------------------------------------------
    for row in gsc.get("top_queries", []):
        query = row.get("query")
        impressions = number(row.get("current_impressions"))
        clicks = number(row.get("current_clicks"))
        position = row.get("current_position")
        position = number(position) if position not in (None, "") else None
        improvement = number(row.get("position_improvement"))
        ctr = number(row.get("current_ctr_percent"))

        if (
            query
            and is_commercial_query(query)
            and position is not None
            and 4 <= position <= 20
            and impressions >= 15
        ):
            page = None

            for tracked in gsc.get("tracked_keywords", []):
                if tracked.get("query") == query:
                    page = tracked.get("ranking_page")
                    break

            priority = "high" if position <= 15 and impressions >= 20 else "medium"

            add(
                "commercial_striking_distance",
                priority,
                query,
                (
                    "Commercial-intent query is already within positions 4-20 and "
                    "has enough current impressions to justify focused optimization."
                ),
                {
                    "gsc_period": gsc.get("period"),
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr_percent": ctr,
                    "position": position,
                    "position_change": improvement,
                },
                (
                    "Inspect the ranking page for exact intent coverage, title/snippet "
                    "alignment, service proof, and relevant internal links. Strengthen "
                    "the existing page before creating another URL for the same intent."
                ),
                query=query,
                page=page,
                confidence="high" if impressions >= 25 else "medium",
            )

    # ---------------------------------------------------------
    # 2. High-visibility / weak-CTR opportunities
    # ---------------------------------------------------------
    for row in gsc.get("top_queries", []):
        query = row.get("query")
        impressions = number(row.get("current_impressions"))
        clicks = number(row.get("current_clicks"))
        ctr = number(row.get("current_ctr_percent"))
        position = row.get("current_position")
        position = number(position) if position not in (None, "") else None

        if (
            query
            and is_commercial_query(query)
            and impressions >= 20
            and position is not None
            and position <= 15
            and ctr < 2.0
            and not (position <= 3 and impressions < 50)
        ):
            add(
                "ctr_opportunity",
                "high" if impressions >= 50 and position <= 10 else "medium",
                query,
                (
                    "The query has meaningful impressions and useful average position "
                    "but is generating little or no click-through."
                ),
                {
                    "gsc_period": gsc.get("period"),
                    "clicks": clicks,
                    "impressions": impressions,
                    "ctr_percent": ctr,
                    "position": position,
                },
                (
                    "Review the search-result title and meta description against the "
                    "query's intent. Verify the landing page immediately confirms the "
                    "service and Tampa-area relevance. Do not change content solely "
                    "because of a low-volume CTR fluctuation."
                ),
                query=query,
                confidence="high" if impressions >= 50 else "medium",
            )

    # ---------------------------------------------------------
    # 3. Existing deterministic Action Center evidence
    # ---------------------------------------------------------
    for row in gsc.get("action_center", {}).get("actions", []):
        source_priority = str(row.get("priority") or "medium").lower()
        confidence = str(row.get("data_level") or "medium").lower()
        category = row.get("category") or "GSC action"

        if source_priority not in ("high", "medium"):
            continue

        # Phase 10 uses a stricter business-action threshold than the
        # diagnostic GSC Action Center. High priority requires high-confidence
        # evidence. Medium-confidence observations remain visible for
        # investigation but do not enter the top weekly action queue.
        priority = (
            "high"
            if source_priority == "high" and confidence == "high"
            else "medium"
        )

        query = row.get("query")
        page = row.get("page") or row.get("previous_page")

        add(
            "gsc_action",
            priority,
            row.get("subject") or query or page or category,
            (
                f"The existing deterministic GSC Action Center classified this as "
                f"{category}."
            ),
            {
                "category": category,
                "gsc_evidence": row.get("evidence"),
                "data_level": row.get("data_level"),
            },
            row.get("recommended_action")
            or "Review the GSC evidence before making a change.",
            query=query,
            page=page,
            confidence=row.get("data_level") or "medium",
        )

    # ---------------------------------------------------------
    # 4. Search demand with no confirmed Organic Search booking
    # ---------------------------------------------------------
    organic_28 = ga4.get("periods", {}).get("28", {})
    organic_overview = organic_28.get("overview", {}).get("current", {})
    organic_confirmed = number(
        organic_28.get("confirmed_bookings", {})
        .get("current", {})
        .get("confirmed_bookings")
    )
    organic_starts = number(
        organic_28.get("intent", {})
        .get("current", {})
        .get("booknow_click")
    )
    organic_sessions = number(organic_overview.get("sessions"))

    if organic_sessions > 0 and organic_starts > 0 and organic_confirmed == 0:
        add(
            "conversion_follow_through",
            "medium",
            "Organic booking follow-through",
            (
                "Organic Search generated booking-start intent during the current "
                "28-day GA4 window, but no confirmed Organic Search booking was recorded."
            ),
            {
                "organic_sessions": organic_sessions,
                "booking_starts": organic_starts,
                "confirmed_bookings": organic_confirmed,
                "booking_start_rate": organic_overview.get("booking_start_rate"),
                "confirmed_booking_rate": organic_overview.get(
                    "confirmed_booking_rate"
                ),
            },
            (
                "Do not assume the traffic failed to convert. Verify BookingKoala "
                "cross-domain attribution and then review the booking flow for friction. "
                "Keep booking starts and confirmed bookings as separate funnel stages."
            ),
            confidence="low" if organic_sessions < 20 else "medium",
        )

    # ---------------------------------------------------------
    # 5. AI referral opportunity
    # ---------------------------------------------------------
    ai_28 = (
        ai.get("periods", {})
        .get("28", {})
        .get("current", {})
        .get("summary", {})
    )
    ai_sessions = number(ai_28.get("sessions"))

    if ai_sessions == 0:
        add(
            "ai_referral_visibility",
            "medium",
            "Identifiable AI referral visibility",
            (
                "GA4 recorded no identifiable AI-assistant referral sessions in the "
                "current 28-day period."
            ),
            {
                "ai_sessions": 0,
                "measurement_definition": ai.get("definition"),
            },
            (
                "Improve answer-ready service content, entity consistency, and "
                "citation-worthy local/service facts. Treat this as a discoverability "
                "signal only: GA4 cannot observe no-click AI answers."
            ),
            confidence="medium",
        )

    # ---------------------------------------------------------
    # 6. AI answer-observation coverage
    # ---------------------------------------------------------
    observations = ai_visibility.get("observations", []) or []

    if not observations:
        add(
            "ai_measurement_gap",
            "medium",
            "AI answer visibility measurement",
            (
                "No controlled AI answer-visibility observations are currently stored, "
                "so mentions and citations cannot yet be trended."
            ),
            {
                "observations": 0,
            },
            (
                "Run a controlled, repeatable set of commercial and local prompts and "
                "record whether Tampa Bay Shine is mentioned, cited, and which URL is "
                "used. Keep this separate from GA4 AI referral traffic."
            ),
            confidence="high",
        )

    # ---------------------------------------------------------
    # Consolidate overlapping recommendations.
    #
    # The Opportunity Intelligence queue is intended to be a
    # decision queue, not a count of every rule that fired.
    # Prefer the existing GSC Action Center item when the same
    # query/page is also detected by a Phase 10 search rule.
    # ---------------------------------------------------------

    gsc_query_subjects = {
        str(item.get("query") or item.get("subject") or "").strip().lower()
        for item in items
        if item.get("type") == "gsc_action"
    }

    gsc_pages = {
        normalize_path(item.get("page"))
        for item in items
        if item.get("type") == "gsc_action" and item.get("page")
    }

    consolidated = []

    for item in items:
        item_type = item.get("type")

        if item_type in {
            "commercial_striking_distance",
            "ctr_opportunity",
        }:
            query_key = str(
                item.get("query") or item.get("subject") or ""
            ).strip().lower()

            page_key = normalize_path(item.get("page"))

            if query_key and query_key in gsc_query_subjects:
                continue

            if page_key and page_key in gsc_pages:
                continue

        consolidated.append(item)

    items = consolidated

    preference = {"gsc_action": 0, "commercial_striking_distance": 1, "ctr_opportunity": 2}
    by_query = {}
    no_query = []
    for item in items:
        q = str(item.get("query") or "").strip().lower()
        if not q:
            no_query.append(item)
            continue
        current = by_query.get(q)
        if current is None or preference.get(item.get("type"), 9) < preference.get(current.get("type"), 9):
            by_query[q] = item
    items = no_query + list(by_query.values())

    priority_order = {"high": 0, "medium": 1, "low": 2}
    confidence_order = {"high": 0, "medium": 1, "low": 2}

    items.sort(
        key=lambda row: (
            priority_order.get(row.get("priority"), 9),
            confidence_order.get(row.get("confidence"), 9),
            row.get("type", ""),
            row.get("subject", ""),
        )
    )

    counts = {
        "total": len(items),
        "high": sum(1 for x in items if x["priority"] == "high"),
        "medium": sum(1 for x in items if x["priority"] == "medium"),
        "low": sum(1 for x in items if x["priority"] == "low"),
    }

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": gsc.get("period"),
        "counts": counts,
        "methodology": {
            "purpose": (
                "Evidence-based weekly SEO/AEO opportunity queue using existing "
                "dashboard datasets."
            ),
            "sources": [
                "Google Search Console",
                "GA4 Organic Search",
                "GA4 identifiable AI referrals",
                "controlled AI answer-visibility observations",
                "SEO Event Log",
            ],
            "principles": [
                "No opaque composite SEO score.",
                "No fabricated or interpolated search observations.",
                "Booking starts are not confirmed bookings.",
                "AI referrals do not measure no-click AI answers.",
                "SEO event timing is context, not proof of causation.",
                "Small samples reduce confidence.",
                "GSC query actions are explicitly marked awaiting_post_change_evidence until enough post-2026-10-05 evidence exists.",
                "Low-volume #1-3 rankings are protected from premature CTR optimization.",
                "Business-deprioritized services remain measurable but rank low.",
                "Duplicate exact-query recommendations are consolidated.",
            ],
        },
        "actions": items,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build the SEO/AEO Opportunity Intelligence dataset."
    )
    parser.add_argument("--gsc", type=Path, default=DEFAULT_GSC)
    parser.add_argument("--ga4", type=Path, default=DEFAULT_GA4)
    parser.add_argument("--ai", type=Path, default=DEFAULT_AI)
    parser.add_argument(
        "--ai-visibility",
        type=Path,
        default=DEFAULT_AI_VISIBILITY,
    )
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--query-history", type=Path, default=DEFAULT_QUERY_HISTORY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    payload = build_intelligence(
        load_json(args.gsc),
        load_json(args.ga4),
        load_json(args.ai),
        load_json(args.ai_visibility, {"observations": []}),
        load_json(args.events, {"events": []}),
        load_json(args.query_history, {"queries": [], "period": {}}),
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(
        f"Opportunity intelligence: {args.out} | "
        f"{payload['counts']['total']} actions | "
        f"{payload['counts']['high']} high | "
        f"{payload['counts']['medium']} medium"
    )


if __name__ == "__main__":
    main()