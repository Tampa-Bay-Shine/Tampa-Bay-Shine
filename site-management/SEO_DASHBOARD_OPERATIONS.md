# Tampa Bay Shine SEO Dashboard and Analytics Operations Guide

## Purpose

Technical runbook for the Tampa Bay Shine SEO/analytics dashboard. It
covers Google Search Console (GSC), Google Analytics 4 (GA4),
BookingKoala conversion tracking, cross-domain measurement, automation,
credentials, rotation, testing, troubleshooting, privacy, and change
management.

For the nontechnical guide, see
`site-management/SEO_DASHBOARD_USER_GUIDE.md`.

## Production dashboard

-   Dashboard: https://seo.tampabayshine.com/
-   Cloudflare Pages project: `tbs-seo-dashboard`
-   Deployment branch: `seo-dashboard`
-   Build output: `cloudflare-site/seo-dashboard`
-   Access: Cloudflare Access

The dashboard deploys separately from the public website.

## Data architecture

**GSC** measures Google visibility: impressions, clicks, CTR, average
position, queries, pages, query/page combinations, and tracked-keyword
trends. GSC does not report BookingKoala bookings and cannot reliably
connect an individual query to an individual later booking.

**GA4** measures activity after arrival: Organic Search sessions/users,
engagement, booking starts, lead-intent events, and confirmed
BookingKoala bookings.

-   GA4 Property ID: `487638948`
-   GA4 Measurement ID: `G-XK4CTL9KWM`
-   Google Ads tag: `AW-17001979579`

Primary funnel:

`Google visibility -> Google click -> Organic Search session -> booking start -> confirmed BookingKoala booking`

## Event definitions

  -------------------------------------------------------------------------------
  Event                      Meaning                      Classification
  -------------------------- ---------------------------- -----------------------
  `booknow_click`            Tracked Book Now CTA click   Booking start / intent

  `phone_click`              Telephone-link click         Lead intent

  `commercial_quote_start`   Commercial contact path      Lead intent
                             initiated

  `contact_click`            General contact path entered Lead intent

  `coupon_click`             Coupon interaction           Secondary intent

  `review_click`             Supported review/Maps link   Engagement
                             click

  `BookingByCustomer`        BookingKoala native          Confirmed booking
                             completed-customer-booking
                             event
  -------------------------------------------------------------------------------

`booknow_click` is not a completed booking. `BookingByCustomer` is the
authoritative confirmed-booking event used by the dashboard and is
case-sensitive. Do not create a second completion event without a
validated need. Do not expose customer identifiers or BookingKoala
booking IDs in the dashboard.

## Rates

-   Booking start rate = Organic Search `booknow_click` / Organic Search
    sessions.
-   Confirmed booking rate = Organic Search `BookingByCustomer` /
    Organic Search sessions.
-   Booking completion rate = Organic Search `BookingByCustomer` /
    Organic Search `booknow_click`.

These are event-count ratios, not exact unique-person probabilities.

## Verified cross-domain behavior

Google's linker is configured for `tampabayshine.com`,
`tampabayshine.bookingkoala.com`, and `booking.tampabayshine.com`.

A production test verified `_gl` decoration on the BookingKoala handoff
and returned the identical GA4 Client ID, `1806746636.1790971052`,
before and after the TampaBayShine.com -\> BookingKoala transition.
Cross-domain GA4 client-identity continuity is therefore verified for
that test.

This does not by itself prove acquisition-source preservation through
booking completion. Organic Search -\> BookingKoala -\>
`BookingByCustomer` remains a separate attribution-quality test.

A real booking test also produced `BookingByCustomer` in GA4 Realtime
and the GA4 Data API. Refreshing the existing Thank You page once did
not increase the event count in that test. This supports duplicate
protection for that tested workflow but is not a universal guarantee.

## Dashboard files

-   `cloudflare-site/seo-dashboard/index.html`
-   `cloudflare-site/seo-dashboard/data/gsc.json`
-   `cloudflare-site/seo-dashboard/data/history.json`
-   `cloudflare-site/seo-dashboard/data/ga4.json`
-   `cloudflare-site/seo-dashboard/data/ga4-history.json`
-   `cloudflare-site/seo-dashboard/data/events.json`
-   `cloudflare-site/seo-dashboard/data/query-history.json`
-   `cloudflare-site/seo-dashboard/data/page-history.json`

## Tools

-   `tools/gsc_dashboard.py`
-   `tools/ga4_dashboard.py`
-   `tools/ga4_conversion_audit.py`
-   `tools/gsc_performance_audit.py`
-   `tools/gsc_index_audit.py`
-   `tools/seo_event.py`

Reuse these tools instead of rebuilding equivalent API clients.

## Automated refresh

The authoritative scheduled workflow is
`.github/workflows/gsc-dashboard.yml` on the default branch. It runs
daily at cron `15 11 * * *`, checks out `seo-dashboard`, installs Google
API dependencies, reconstructs temporary credentials from GitHub
secrets, refreshes GSC and GA4, rejects unexpected changes, and commits
approved generated dashboard datasets to `seo-dashboard`.

Phase 9 requires the scheduled workflow to include
`query-history.json` and `page-history.json` in its approved/staged
dashboard data files in addition to the existing GSC, GA4, AI, and
history datasets.

Do not use the public-site promotion script to refresh dashboard data.

## Daily GSC query and page history

Phase 9 adds real daily Search Console history for individual queries
and pages:

- `data/query-history.json` - daily query-level GSC observations.
- `data/page-history.json` - daily page-level GSC observations.

Both retain a rolling 365-day window. Initial generation performs a
full backfill. Normal runs refresh the most recent 7-day overlap and
merge it into retained history.

Query history retains queries with at least 20 impressions over the
retained window, plus configured tracked keywords and queries currently
needed by the dashboard. Page history retains pages with at least 20
impressions, plus pages currently needed by dashboard analysis.

Compact points use `[date, clicks, impressions, ctr, position]`.

Do not interpret a missing query/date row as a measured zero. Search
Console may omit anonymized or low-volume query observations. Average
position is impression-weighted for retained summaries and is not a
deterministic live Google ranking.

Normal generation:

    python.exe .\tools\gsc_dashboard.py --query-history-days 365 --page-history-days 365

Incremental overlap defaults to 7 days and can be changed with
`--query-history-refresh-days` and `--page-history-refresh-days`.

The explorer supports `1D | 7D | 30D | 90D | 180D | 1Y | Custom` and
`Clicks | Impressions | Position | CTR`. SEO Event Log entries inside
the selected period are overlaid as annotations. Event timing provides
context only and does not prove causation.

### Query/page metric semantics

Tracked Keywords and Top Queries table rows use the current 28-day GSC
period. Clicks and impressions are period totals. CTR is period clicks
divided by period impressions. Average position is the
impression-weighted GSC average for the period. Position change is an
absolute number of positions versus the previous 28-day period, not a
percentage.

Expanded charts use retained daily GSC observations and the global trend
range. The selected-period summary recomputes totals, CTR, and
impression-weighted average position from the observations in that
range. The Latest reported day block shows the final actual retained
daily observation separately.

Therefore, the final plotted daily position/CTR/click/impression value
does not need to equal the parent row's 28-day aggregate. Do not replace
either value with the other or interpolate missing query dates.


## Opportunity Intelligence

Phase 10 adds a cross-source SEO/AEO decision layer generated by:

    python.exe .\tools\opportunity_intelligence.py

The generator reads:

- `gsc.json`
- `ga4.json`
- `ai.json`
- `ai-visibility.json`
- `events.json`

and writes:

    cloudflare-site/seo-dashboard/data/opportunity-intelligence.json

The queue combines deterministic search opportunities with conversion,
AI, and SEO Event Log context. It surfaces GSC Action Center evidence,
commercial striking-distance and CTR opportunities, Organic Search
booking follow-through, identifiable AI-referral visibility, and AI
answer-visibility measurement gaps.

### Priority and confidence

Priority describes business urgency. Confidence describes the strength
of the available evidence. They are intentionally separate.

Phase 10 applies a stricter high-priority threshold than the diagnostic
GSC Action Center. Medium-confidence evidence remains visible for
investigation rather than automatically entering the top action queue.

Overlapping search recommendations are deduplicated when an existing GSC
Action Center item already represents the same query or page.

### Conversion context

When a ranking URL has matching GA4 Organic Search landing-page evidence,
the intelligence card may show landing-page conversion context.

When no matching landing-page row exists, the generator may show
sitewide Organic Search context. That must remain explicitly labeled
sitewide and must not be interpreted as page-level attribution.

`booknow_click` remains booking intent. `BookingByCustomer` remains the
confirmed-booking signal.

### AI and event context

Identifiable AI referrals and no-click AI answer visibility are different
measurements. Zero GA4 AI referrals does not establish zero AI mentions.
Controlled answer-visibility observations are required for mention and
citation measurement. If none exist, report the measurement gap rather
than estimating visibility.

SEO Event Log timing provides context only and does not prove causation.

### Review and measurement

Each action contains a 30/60/90-day measurement plan. Investigate the
underlying evidence before making broad page changes and record material
SEO changes in the SEO Event Log.

The generator can refresh daily with the source datasets while the
recommended business review cadence remains weekly.

The scheduled workflow must run `tools/opportunity_intelligence.py` after
the GSC, GA4, and AI generators and must allow/stage
`opportunity-intelligence.json` as an approved generated dataset.

## Credentials

Never commit OAuth credentials.

Local files:

-   `%USERPROFILE%\.tbs-gsc\client_secret.json`
-   `%USERPROFILE%\.tbs-gsc\token.json`
-   `%USERPROFILE%\.tbs-ga4\token.json`

Scopes:

-   GSC: `https://www.googleapis.com/auth/webmasters.readonly`
-   GA4: `https://www.googleapis.com/auth/analytics.readonly`

GitHub Actions secrets:

-   `TBS_GSC_CLIENT_SECRET_B64`
-   `TBS_GSC_TOKEN_B64`
-   `TBS_GA4_TOKEN_B64`

Base64 is encoding, not encryption. Never place decoded credentials or
encoded secret values in the repository, documentation, issues, commit
messages, dashboard JSON, or chat transcripts.

## Credential rotation

### OAuth token

1.  Preserve the working token until its replacement is verified.
2.  Reauthorize the appropriate Google API scope locally.
3.  Run the applicable generator with the replacement.
4.  Confirm expected data.
5.  Base64-encode the replacement.
6.  Replace the corresponding GitHub Actions secret.
7.  Manually run the dashboard workflow.
8.  Verify workflow success and fresh dashboard data.
9.  Retire obsolete copies only after verification.

### OAuth client

1.  Obtain the authorized replacement OAuth client.
2.  Store it outside the repository.
3.  Reauthorize GSC/GA4 if required.
4.  Test both generators locally.
5.  Replace `TBS_GSC_CLIENT_SECRET_B64`.
6.  Replace token secrets if new tokens were issued.
7.  Manually run the workflow.
8.  Verify GSC, GA4, commit, push, and deployment.
9.  Retire the old client only after successful verification.

PowerShell base64 example:

``` powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\.tbs-ga4\token.json"))
```

Treat the output as a secret.

## Local GA4 refresh

``` powershell
python.exe .\tools\ga4_dashboard.py `
  --property 487638948 `
  --client-secret "$HOME\.tbs-gsc\client_secret.json" `
  --token "$HOME\.tbs-ga4\token.json" `
  --out ".\cloudflare-site\seo-dashboard\data\ga4.json" `
  --history-out ".\cloudflare-site\seo-dashboard\data\ga4-history.json"
```

## GA4 diagnostic audit

``` powershell
python.exe .\tools\ga4_conversion_audit.py `
  --property 487638948 `
  --client-secret "$HOME\.tbs-gsc\client_secret.json" `
  --token "$HOME\.tbs-ga4\token.json" `
  --start-date YYYY-MM-DD `
  --end-date YYYY-MM-DD
```

Use `site-management/GSC_AUDIT_TOOLS.md` and the existing GSC tools for
Search Console operations.

## Privacy and change management

Keep the dashboard aggregate-only. Do not expose customer names, emails,
phone numbers, street addresses, payment information, form contents, or
customer-linked booking IDs.

When changing analytics: define the business meaning, identify the
authoritative source, distinguish intent from completed outcomes,
exclude PII, test locally, inspect generated JSON, test the dashboard,
update documentation, commit only expected files, and verify scheduled
automation. Never silently change an established metric's meaning.

## Troubleshooting

If the dashboard stops updating, inspect GitHub Actions and isolate
credential creation, GSC generation, GA4 generation, safety validation,
commit, or push.

If GSC succeeds but GA4 fails, check `TBS_GA4_TOKEN_B64`, GA4 API
access, property `487638948`, OAuth scope, and `google-analytics-data`.

If GA4 succeeds but GSC fails, check `TBS_GSC_TOKEN_B64`, Search Console
property/API access, and scope.

If booking starts appear but confirmed bookings do not, first check GA4
for exact `BookingByCustomer` events by acquisition channel. A start
does not guarantee completion.

If confirmed bookings appear as Direct, do not relabel them as Organic
Search. Investigate session/source continuity.

## Known limitations

GSC average position is an aggregate metric, not a deterministic live
rank. GSC cannot attribute an individual query to a specific later GA4
booking. GA4 attribution depends on session/acquisition continuity.
Revenue attribution is not currently validated; do not infer revenue
from booking counts.

## Phase 7 status

Verified:

- production GA4 measurement is active;
- Book Now intent tracking is active;
- BookingKoala emits native `BookingByCustomer`;
- `BookingByCustomer` is available through the GA4 Data API;
- outbound BookingKoala navigation receives Google's `_gl` linker;
- the tested TampaBayShine.com and BookingKoala pages returned the same GA4 Client ID;
- a tested Thank You page refresh did not duplicate the native booking event;
- GA4 is assigning `BookingByCustomer` events to acquisition channels.

Observed for September 1 through October 2, 2026:

- Organic Search sessions: 3;
- Organic Search `booknow_click` events: 2;
- Organic Search `BookingByCustomer` events: 0;
- Direct `BookingByCustomer` events: 1;
- Organic Social `BookingByCustomer` events: 1.

Conclusion:

Cross-domain client-identity continuity is verified and confirmed-booking channel attribution is operational. A confirmed Organic Search booking has not yet been observed in the available data.

The dashboard automatically checks `events_by_channel` for a case-sensitive `BookingByCustomer` event whose channel is `Organic Search`. Until one is present, it reports that Organic Search confirmed-booking attribution has not yet been observed. When the first such event appears, the status automatically changes to verified.

Do not relabel Direct or Organic Social bookings as Organic Search. No additional test booking is required solely to force this condition.

The Winners & Losers tables are constrained to the dashboard viewport on
desktop. Query/page and reason text may wrap at word boundaries; metric
columns remain compact. For low-volume Clicks/Impressions charts, Y-axis
tick labels may use decimals to prevent duplicate-looking labels. The
underlying GSC click/impression observations remain whole-number values.
