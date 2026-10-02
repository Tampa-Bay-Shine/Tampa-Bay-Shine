from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    FilterExpressionList,
    Metric,
    RunReportRequest,
)

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUT = (
    ROOT
    / "cloudflare-site"
    / "seo-dashboard"
    / "data"
    / "ga4.json"
)

DEFAULT_HISTORY_OUT = (
    ROOT
    / "cloudflare-site"
    / "seo-dashboard"
    / "data"
    / "ga4-history.json"
)

DEFAULT_CLIENT_SECRET = Path.home() / ".tbs-gsc" / "client_secret.json"
DEFAULT_TOKEN = Path.home() / ".tbs-ga4" / "token.json"
DEFAULT_PROPERTY = "487638948"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

INTENT_EVENTS = [
    "booknow_click",
    "phone_click",
    "commercial_quote_start",
    "contact_click",
    "coupon_click",
]

PRIMARY_INTENT_EVENTS = [
    "booknow_click",
    "phone_click",
    "commercial_quote_start",
    "contact_click",
]

CONFIRMED_BOOKING_EVENT = "BookingByCustomer"


def get_credentials(client_secret: Path, token_path: Path):
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(
            str(token_path),
            SCOPES,
        )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secret),
            SCOPES,
        )
        creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

    return creds


def organic_filter():
    return FilterExpression(
        filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(
                match_type=Filter.StringFilter.MatchType.EXACT,
                value="Organic Search",
                case_sensitive=False,
            ),
        )
    )


def event_filter(event_names):
    expressions = []

    for event_name in event_names:
        expressions.append(
            FilterExpression(
                filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(
                        match_type=Filter.StringFilter.MatchType.EXACT,
                        value=event_name,
                        case_sensitive=True,
                    ),
                )
            )
        )

    return FilterExpression(
        or_group=FilterExpressionList(
            expressions=expressions
        )
    )


def organic_and_event_filter(event_names):
    return FilterExpression(
        and_group=FilterExpressionList(
            expressions=[
                organic_filter(),
                event_filter(event_names),
            ]
        )
    )


def run_report(
    client,
    property_id,
    dimensions,
    metrics,
    date_ranges,
    dimension_filter=None,
    limit=10000,
):
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name=name)
            for name in dimensions
        ],
        metrics=[
            Metric(name=name)
            for name in metrics
        ],
        date_ranges=[
            DateRange(
                start_date=start,
                end_date=end,
            )
            for start, end in date_ranges
        ],
        dimension_filter=dimension_filter,
        limit=limit,
    )

    return client.run_report(request)


def rows(response):
    dimension_headers = [
        item.name
        for item in response.dimension_headers
    ]

    metric_headers = [
        item.name
        for item in response.metric_headers
    ]

    result = []

    for row in response.rows:
        item = {}

        for header, value in zip(
            dimension_headers,
            row.dimension_values,
        ):
            item[header] = value.value

        for header, value in zip(
            metric_headers,
            row.metric_values,
        ):
            item[header] = value.value

        result.append(item)

    return result


def number(value):
    if value in (None, ""):
        return 0.0

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def rounded(value, places=2):
    return round(number(value), places)


def clean_count(value):
    value = number(value)

    if value.is_integer():
        return int(value)

    return round(value, 2)


def period_definition(days):
    return {
        "days": days,
        "current": (
            f"{days}daysAgo",
            "yesterday",
        ),
        "previous": (
            f"{days * 2}daysAgo",
            f"{days + 1}daysAgo",
        ),
    }


def overview_for_range(client, property_id, date_range):
    response = run_report(
        client,
        property_id,
        dimensions=[],
        metrics=[
            "sessions",
            "activeUsers",
            "engagedSessions",
            "engagementRate",
        ],
        date_ranges=[date_range],
        dimension_filter=organic_filter(),
        limit=10,
    )

    data = rows(response)
    row = data[0] if data else {}

    return {
        "sessions": clean_count(
            row.get("sessions")
        ),
        "active_users": clean_count(
            row.get("activeUsers")
        ),
        "engaged_sessions": clean_count(
            row.get("engagedSessions")
        ),
        "engagement_rate": rounded(
            number(row.get("engagementRate")) * 100
        ),
    }


def overview_for_period(client, property_id, definition):
    return {
        "current": overview_for_range(
            client,
            property_id,
            definition["current"],
        ),
        "previous": overview_for_range(
            client,
            property_id,
            definition["previous"],
        ),
    }


def intent_for_range(client, property_id, date_range):
    response = run_report(
        client,
        property_id,
        dimensions=["eventName"],
        metrics=["eventCount"],
        date_ranges=[date_range],
        dimension_filter=organic_and_event_filter(
            INTENT_EVENTS
        ),
        limit=100,
    )

    result = {
        name: 0
        for name in INTENT_EVENTS
    }

    for row in rows(response):
        event_name = row.get("eventName")

        if event_name in result:
            result[event_name] = clean_count(
                row.get("eventCount")
            )

    result["primary_intent_actions"] = sum(
        result[name]
        for name in PRIMARY_INTENT_EVENTS
    )

    result["all_intent_actions"] = sum(
        result[name]
        for name in INTENT_EVENTS
    )

    return result


def intent_for_period(client, property_id, definition):
    return {
        "current": intent_for_range(
            client,
            property_id,
            definition["current"],
        ),
        "previous": intent_for_range(
            client,
            property_id,
            definition["previous"],
        ),
    }


def confirmed_bookings_for_range(client, property_id, date_range):
    response = run_report(
        client,
        property_id,
        dimensions=[],
        metrics=["eventCount"],
        date_ranges=[date_range],
        dimension_filter=organic_and_event_filter(
            [CONFIRMED_BOOKING_EVENT]
        ),
        limit=10,
    )

    data = rows(response)
    row = data[0] if data else {}

    return {
        "confirmed_bookings": clean_count(
            row.get("eventCount")
        )
    }


def confirmed_bookings_for_period(client, property_id, definition):
    return {
        "current": confirmed_bookings_for_range(
            client,
            property_id,
            definition["current"],
        ),
        "previous": confirmed_bookings_for_range(
            client,
            property_id,
            definition["previous"],
        ),
    }


def landing_pages(client, property_id):
    traffic_response = run_report(
        client,
        property_id,
        dimensions=["landingPagePlusQueryString"],
        metrics=[
            "sessions",
            "activeUsers",
            "engagedSessions",
        ],
        date_ranges=[
            ("28daysAgo", "yesterday")
        ],
        dimension_filter=organic_filter(),
        limit=500,
    )

    event_response = run_report(
        client,
        property_id,
        dimensions=[
            "landingPagePlusQueryString",
            "eventName",
        ],
        metrics=["eventCount"],
        date_ranges=[
            ("28daysAgo", "yesterday")
        ],
        dimension_filter=organic_and_event_filter(
            INTENT_EVENTS + [CONFIRMED_BOOKING_EVENT]
        ),
        limit=5000,
    )

    pages = {}

    for row in rows(traffic_response):
        page = (
            row.get("landingPagePlusQueryString")
            or "(not set)"
        )

        pages[page] = {
            "landing_page": page,
            "sessions": clean_count(
                row.get("sessions")
            ),
            "active_users": clean_count(
                row.get("activeUsers")
            ),
            "engaged_sessions": clean_count(
                row.get("engagedSessions")
            ),
            **{
                name: 0
                for name in INTENT_EVENTS
            },
            "confirmed_bookings": 0,
        }

    for row in rows(event_response):
        page = (
            row.get("landingPagePlusQueryString")
            or "(not set)"
        )

        event_name = row.get("eventName")

        item = pages.setdefault(
            page,
            {
                "landing_page": page,
                "sessions": 0,
                "active_users": 0,
                "engaged_sessions": 0,
                **{
                    name: 0
                    for name in INTENT_EVENTS
                },
                "confirmed_bookings": 0,
            },
        )

        if event_name in INTENT_EVENTS:
            item[event_name] = clean_count(
                row.get("eventCount")
            )
        elif event_name == CONFIRMED_BOOKING_EVENT:
            item["confirmed_bookings"] = clean_count(
                row.get("eventCount")
            )

    result = []

    for item in pages.values():
        item["primary_intent_actions"] = sum(
            item[name]
            for name in PRIMARY_INTENT_EVENTS
        )

        item["all_intent_actions"] = sum(
            item[name]
            for name in INTENT_EVENTS
        )

        sessions = number(item["sessions"])

        item["booking_start_rate"] = (
            round(
                number(item["booknow_click"])
                / sessions
                * 100,
                2,
            )
            if sessions
            else None
        )

        item["confirmed_booking_rate"] = (
            round(
                number(item["confirmed_bookings"])
                / sessions
                * 100,
                2,
            )
            if sessions
            else None
        )

        booking_starts = number(item["booknow_click"])

        item["booking_completion_rate"] = (
            round(
                number(item["confirmed_bookings"])
                / booking_starts
                * 100,
                2,
            )
            if booking_starts
            else None
        )

        result.append(item)

    result.sort(
        key=lambda item: (
            number(item["primary_intent_actions"]),
            number(item["sessions"]),
        ),
        reverse=True,
    )

    return result


def conversion_events_by_channel(client, property_id):
    response = run_report(
        client,
        property_id,
        dimensions=[
            "eventName",
            "sessionDefaultChannelGroup",
        ],
        metrics=["eventCount"],
        date_ranges=[
            ("28daysAgo", "yesterday")
        ],
        dimension_filter=event_filter(
            INTENT_EVENTS + [CONFIRMED_BOOKING_EVENT]
        ),
        limit=1000,
    )

    result = []

    for row in rows(response):
        result.append({
            "event_name": row.get("eventName"),
            "channel": row.get(
                "sessionDefaultChannelGroup"
            ),
            "event_count": clean_count(
                row.get("eventCount")
            ),
        })

    result.sort(
        key=lambda item: (
            item["event_name"] or "",
            item["channel"] or "",
        )
    )

    return result


def add_rates(period):
    for bucket in ("current", "previous"):
        sessions = number(
            period["overview"][bucket]["sessions"]
        )

        booking_starts = number(
            period["intent"][bucket][
                "booknow_click"
            ]
        )

        primary_actions = number(
            period["intent"][bucket][
                "primary_intent_actions"
            ]
        )

        confirmed_bookings = number(
            period["confirmed_bookings"][bucket][
                "confirmed_bookings"
            ]
        )

        period["overview"][bucket][
            "booking_start_rate"
        ] = (
            round(
                booking_starts / sessions * 100,
                2,
            )
            if sessions
            else None
        )

        period["overview"][bucket][
            "primary_intent_rate"
        ] = (
            round(
                primary_actions / sessions * 100,
                2,
            )
            if sessions
            else None
        )


        period["overview"][bucket][
            "confirmed_booking_rate"
        ] = (
            round(
                confirmed_bookings / sessions * 100,
                2,
            )
            if sessions
            else None
        )

        period["overview"][bucket][
            "booking_completion_rate"
        ] = (
            round(
                confirmed_bookings / booking_starts * 100,
                2,
            )
            if booking_starts
            else None
        )


def build_history_snapshot(payload):
    period = payload["periods"]["28"]

    return {
        "date": payload["data_through"],
        "sessions": period["overview"][
            "current"
        ]["sessions"],
        "active_users": period["overview"][
            "current"
        ]["active_users"],
        "engaged_sessions": period["overview"][
            "current"
        ]["engaged_sessions"],
        "engagement_rate": period["overview"][
            "current"
        ]["engagement_rate"],
        "booknow_click": period["intent"][
            "current"
        ]["booknow_click"],
        "phone_click": period["intent"][
            "current"
        ]["phone_click"],
        "commercial_quote_start": period[
            "intent"
        ]["current"]["commercial_quote_start"],
        "contact_click": period["intent"][
            "current"
        ]["contact_click"],
        "coupon_click": period["intent"][
            "current"
        ]["coupon_click"],
        "primary_intent_actions": period[
            "intent"
        ]["current"]["primary_intent_actions"],
        "confirmed_bookings": period[
            "confirmed_bookings"
        ]["current"]["confirmed_bookings"],
        "booking_start_rate": period[
            "overview"
        ]["current"]["booking_start_rate"],
        "primary_intent_rate": period[
            "overview"
        ]["current"]["primary_intent_rate"],
        "confirmed_booking_rate": period[
            "overview"
        ]["current"]["confirmed_booking_rate"],
        "booking_completion_rate": period[
            "overview"
        ]["current"]["booking_completion_rate"],
    }


def update_history(path: Path, payload):
    history = {
        "schema_version": 1,
        "snapshots": [],
    }

    if path.exists():
        try:
            existing = json.loads(
                path.read_text(encoding="utf-8-sig")
            )

            if (
                existing.get("schema_version") == 1
                and isinstance(
                    existing.get("snapshots"),
                    list,
                )
            ):
                history = existing
        except Exception:
            pass

    snapshot = build_history_snapshot(payload)

    snapshots = [
        item
        for item in history["snapshots"]
        if item.get("date") != snapshot["date"]
    ]

    snapshots.append(snapshot)

    snapshots.sort(
        key=lambda item: item.get("date", "")
    )

    history["snapshots"] = snapshots[-400:]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            history,
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return history


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Generate Tampa Bay Shine GA4 "
            "conversion dashboard data."
        )
    )

    ap.add_argument(
        "--property",
        default=DEFAULT_PROPERTY,
    )

    ap.add_argument(
        "--client-secret",
        default=str(DEFAULT_CLIENT_SECRET),
    )

    ap.add_argument(
        "--token",
        default=str(DEFAULT_TOKEN),
    )

    ap.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
    )

    ap.add_argument(
        "--history-out",
        default=str(DEFAULT_HISTORY_OUT),
    )

    args = ap.parse_args()

    client_secret = Path(args.client_secret)
    token_path = Path(args.token)
    out_path = Path(args.out)
    history_path = Path(args.history_out)

    if not client_secret.exists():
        raise SystemExit(
            "Google OAuth client secret not found: "
            f"{client_secret}"
        )

    creds = get_credentials(
        client_secret,
        token_path,
    )

    client = BetaAnalyticsDataClient(
        credentials=creds
    )

    periods = {}

    for days in (7, 28, 90):
        definition = period_definition(days)

        print(
            f"Fetching GA4 Organic Search "
            f"{days}-day comparison..."
        )

        period = {
            "days": days,
            "current_range": {
                "start": definition["current"][0],
                "end": definition["current"][1],
            },
            "previous_range": {
                "start": definition["previous"][0],
                "end": definition["previous"][1],
            },
            "overview": overview_for_period(
                client,
                args.property,
                definition,
            ),
            "intent": intent_for_period(
                client,
                args.property,
                definition,
            ),
            "confirmed_bookings": confirmed_bookings_for_period(
                client,
                args.property,
                definition,
            ),
        }

        add_rates(period)

        periods[str(days)] = period

    print("Fetching organic landing pages...")

    page_rows = landing_pages(
        client,
        args.property,
    )

    print("Fetching intent events by channel...")

    channel_rows = conversion_events_by_channel(
        client,
        args.property,
    )

    generated_at = datetime.now(
        timezone.utc
    ).replace(
        microsecond=0
    ).isoformat()

    data_through = (
        datetime.now(timezone.utc).date()
        - timedelta(days=1)
    ).isoformat()

    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "data_through": data_through,
        "property_id": args.property,
        "property_name": "tampabayshine.com",
        "channel": "Organic Search",
        "periods": periods,
        "landing_pages": page_rows,
        "events_by_channel": channel_rows,
        "definitions": {
            "booking_start": (
                "booknow_click - visitor clicked "
                "a Book Now link. This is not a "
                "confirmed booking."
            ),
            "primary_intent_actions": (
                "booknow_click + phone_click + "
                "commercial_quote_start + "
                "contact_click."
            ),
            "booking_start_rate": (
                "booknow_click events divided by "
                "Organic Search sessions. Multiple "
                "events can occur in one session."
            ),
            "confirmed_bookings": (
                "BookingByCustomer - native BookingKoala event "
                "recorded after a customer creates a booking."
            ),
            "confirmed_booking_rate": (
                "Organic Search BookingByCustomer events divided "
                "by Organic Search sessions."
            ),
            "booking_completion_rate": (
                "Organic Search BookingByCustomer events divided "
                "by Organic Search booknow_click events."
            ),
            "revenue": (
                "Not currently available from the "
                "verified GA4 events."
            ),
        },
    }

    out_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    out_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    history = update_history(
        history_path,
        payload,
    )

    print()
    print(f"Wrote: {out_path}")
    print(f"Wrote: {history_path}")
    print(
        "GA4 history snapshots: "
        f"{len(history['snapshots'])}"
    )

    current = periods["28"]

    print()
    print("28-day Organic Search validation")
    print(
        "Sessions:",
        current["overview"]["current"]["sessions"],
    )
    print(
        "Active users:",
        current["overview"]["current"][
            "active_users"
        ],
    )
    print(
        "Engaged sessions:",
        current["overview"]["current"][
            "engaged_sessions"
        ],
    )
    print(
        "Booking starts:",
        current["intent"]["current"][
            "booknow_click"
        ],
    )
    print(
        "Booking start rate:",
        current["overview"]["current"][
            "booking_start_rate"
        ],
    )


if __name__ == "__main__":
    main()




