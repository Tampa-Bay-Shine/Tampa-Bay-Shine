from __future__ import annotations

import argparse
import json
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
    Metric,
    RunReportRequest,
)

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

DEFAULT_CLIENT_SECRET = Path.home() / ".tbs-gsc" / "client_secret.json"
DEFAULT_TOKEN = Path.home() / ".tbs-ga4" / "token.json"
DEFAULT_PROPERTY = "487638948"


def get_credentials(client_secret: Path, token_path: Path) -> Credentials:
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

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
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return creds


def report_rows(response):
    dimension_headers = [x.name for x in response.dimension_headers]
    metric_headers = [x.name for x in response.metric_headers]

    rows = []

    for row in response.rows:
        item = {}

        for header, value in zip(dimension_headers, row.dimension_values):
            item[header] = value.value

        for header, value in zip(metric_headers, row.metric_values):
            item[header] = value.value

        rows.append(item)

    return rows


def run_report(
    client,
    property_id,
    dimensions,
    metrics,
    start_date="28daysAgo",
    end_date="yesterday",
    organic_only=False,
    limit=100,
):
    dimension_filter = None

    if organic_only:
        dimension_filter = FilterExpression(
            filter=Filter(
                field_name="sessionDefaultChannelGroup",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.EXACT,
                    value="Organic Search",
                    case_sensitive=False,
                ),
            )
        )

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=x) for x in dimensions],
        metrics=[Metric(name=x) for x in metrics],
        date_ranges=[
            DateRange(
                start_date=start_date,
                end_date=end_date,
            )
        ],
        dimension_filter=dimension_filter,
        limit=limit,
    )

    return client.run_report(request)


def print_section(title, rows):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)

    if not rows:
        print("No rows returned.")
        return

    for row in rows:
        print(json.dumps(row, ensure_ascii=True))


def main():
    ap = argparse.ArgumentParser(
        description="Audit Tampa Bay Shine GA4 organic traffic and conversion events."
    )
    ap.add_argument("--property", default=DEFAULT_PROPERTY)
    ap.add_argument(
        "--client-secret",
        default=str(DEFAULT_CLIENT_SECRET),
    )
    ap.add_argument(
        "--token",
        default=str(DEFAULT_TOKEN),
    )
    ap.add_argument("--start-date", default="28daysAgo")
    ap.add_argument("--end-date", default="yesterday")
    args = ap.parse_args()

    client_secret = Path(args.client_secret)
    token_path = Path(args.token)

    if not client_secret.exists():
        raise SystemExit(
            f"Google OAuth client secret not found: {client_secret}"
        )

    creds = get_credentials(client_secret, token_path)
    client = BetaAnalyticsDataClient(credentials=creds)

    print()
    print("Tampa Bay Shine GA4 audit")
    print(f"Property: {args.property}")
    print(f"Period: {args.start_date} through {args.end_date}")
    print("Channel filter: Organic Search")

    overview = run_report(
        client,
        args.property,
        dimensions=["sessionDefaultChannelGroup"],
        metrics=[
            "sessions",
            "activeUsers",
            "engagedSessions",
            "eventCount",
        ],
        start_date=args.start_date,
        end_date=args.end_date,
        organic_only=True,
        limit=10,
    )

    print_section(
        "ORGANIC SEARCH OVERVIEW",
        report_rows(overview),
    )

    landing_pages = run_report(
        client,
        args.property,
        dimensions=["landingPagePlusQueryString"],
        metrics=[
            "sessions",
            "activeUsers",
            "engagedSessions",
            "eventCount",
        ],
        start_date=args.start_date,
        end_date=args.end_date,
        organic_only=True,
        limit=50,
    )

    print_section(
        "ORGANIC LANDING PAGES",
        report_rows(landing_pages),
    )

    events = run_report(
        client,
        args.property,
        dimensions=["eventName"],
        metrics=["eventCount"],
        start_date=args.start_date,
        end_date=args.end_date,
        organic_only=True,
        limit=100,
    )

    event_rows = report_rows(events)
    event_rows.sort(
        key=lambda x: int(float(x.get("eventCount", 0) or 0)),
        reverse=True,
    )

    print_section(
        "ORGANIC SEARCH EVENTS",
        event_rows,
    )

    all_channels_events = run_report(
        client,
        args.property,
        dimensions=["eventName", "sessionDefaultChannelGroup"],
        metrics=["eventCount"],
        start_date=args.start_date,
        end_date=args.end_date,
        organic_only=False,
        limit=250,
    )

    interesting = {
        "booknow_click",
        "phone_click",
        "commercial_quote_start",
        "contact_click",
        "coupon_click",
        "review_click",
        "purchase",
        "generate_lead",
        "form_submit",
        "booking",
        "booking_complete",
        "BookingByCustomer",
        "booking_completed",
    }

    conversion_rows = [
        row
        for row in report_rows(all_channels_events)
        if row.get("eventName") in interesting
    ]

    conversion_rows.sort(
        key=lambda x: (
            x.get("eventName", ""),
            x.get("sessionDefaultChannelGroup", ""),
        )
    )

    print_section(
        "KNOWN / POSSIBLE CONVERSION EVENTS BY CHANNEL",
        conversion_rows,
    )

    print()
    print("GA4 audit complete.")


if __name__ == "__main__":
    main()
