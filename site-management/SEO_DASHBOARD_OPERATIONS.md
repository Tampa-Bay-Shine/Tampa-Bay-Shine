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

### Competitor authority data workflow

Competitor Intelligence additionally uses:
- `cloudflare-site/seo-dashboard/data/competitor-config.json`
- `cloudflare-site/seo-dashboard/data/competitor-rankings.json`
- `cloudflare-site/seo-dashboard/data/competitor-rankings-history.json`
- `cloudflare-site/seo-dashboard/data/competitor-authority.json`
- `cloudflare-site/seo-dashboard/data/competitor-intelligence.json`
- `site-management/competitor-authority-template.csv`

SERP capture is manual and must not bypass Google CAPTCHA/anti-bot controls. Authority/backlink observations are also manual. Populate the CSV from free/available Moz, Ahrefs, and/or Semrush checks; leave unavailable vendor metrics blank.

Import and rebuild:
```powershell
python.exe .\tools\competitor_authority_import.py
python.exe .\tools\competitor_intelligence.py
```

Moz DA, Ahrefs DR, and Semrush Authority Score stay separate because they use different methodologies and are not Google metrics. The authority watchlist is split between residential/local and commercial/facility competitors.

See `site-management/COMPETITOR_INTELLIGENCE.md` for the full workflow.

-   `cloudflare-site/seo-dashboard/index.html`
-   `cloudflare-site/seo-dashboard/data/gsc.json`
-   `cloudflare-site/seo-dashboard/data/history.json`
-   `cloudflare-site/seo-dashboard/data/ga4.json`
-   `cloudflare-site/seo-dashboard/data/ga4-history.json`
-   `cloudflare-site/seo-dashboard/data/events.json`
-   `cloudflare-site/seo-dashboard/data/query-history.json`
-   `cloudflare-site/seo-dashboard/data/page-history.json`
-   `cloudflare-site/seo-dashboard/data/daily-total-history.json`
-   `cloudflare-site/seo-dashboard/data/performance-intelligence.json`
-   `cloudflare-site/seo-dashboard/data/opportunity-intelligence.json`
-   `cloudflare-site/seo-dashboard/data/opportunity-workflow.json`

## Tools

-   `tools/gsc_dashboard.py`
-   `tools/ga4_dashboard.py`
-   `tools/ga4_conversion_audit.py`
-   `tools/gsc_performance_audit.py`
-   `tools/gsc_index_audit.py`
-   `tools/seo_event.py`
-   `tools/performance_intelligence.py`
-   `tools/opportunity_intelligence.py`
-   `tools/opportunity_workflow.py`
-   `tools/send_seo_email.py`

Reuse these tools instead of rebuilding equivalent API clients.

## Automated refresh

The authoritative workflow is `.github/workflows/gsc-dashboard.yml` on `main`. It uses UTC cron entries `0 12 * * *` and `0 13 * * *` plus a U.S. Eastern DST selector so the appropriate occurrence runs at approximately 8:00 AM Eastern. Manual `workflow_dispatch` remains available.

The workflow checks out `seo-dashboard`, reconstructs temporary Google credentials, refreshes GSC including authoritative date-only daily totals and retained query/page histories, runs Performance Intelligence, refreshes GA4 and AI referral data, refreshes Opportunity Intelligence, syncs Opportunity Workflow, validates the generated-file allowlist, and commits/pushes generated dashboard data.

After the successful scheduled refresh/commit stage, the workflow sends the Daily SEO Performance Brief through Resend. Manual runs do not send email unless `send_email` is explicitly enabled.

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


## Performance Intelligence and authoritative GSC totals

Performance Intelligence is generated by `tools/performance_intelligence.py` and written to `data/performance-intelligence.json`.

Site-wide headline metrics use `data/daily-total-history.json`, populated from Search Console date-only daily totals. Do not reconstruct site-wide totals by summing query rows: Search Console can omit anonymized or low-volume queries, materially undercounting visibility.

The dashboard compares the latest complete day with the prior day, latest 7 complete days with the previous 7, and latest 28 days with the previous 28. CTR change is percentage points. Positive position change means improvement because lower average position is better.

Query/page movers use retained daily query/page histories and are not exhaustive site-wide totals. Branded/nonbranded query summaries are retained-query views, not authoritative site-wide segmentation.

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
-   `RESEND_API_KEY`

Base64 is encoding, not encryption. Never place decoded credentials or
encoded secret values in the repository, documentation, issues, commit
messages, dashboard JSON, or chat transcripts.

### Resend email delivery

Resend is configured with the verified sending subdomain `updates.tampabayshine.com`. The scheduled brief sends from `Tampa Bay Shine SEO <seo@updates.tampabayshine.com>` to `marketing@tampabayshine.com`; replies go to `marketing@tampabayshine.com`.

The API key is stored only as the GitHub Actions repository secret `RESEND_API_KEY`. Documentation records the secret name and configuration, never its value. Do not commit or log the key. Receiving is not required for this workflow.

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

<!-- v20.6.1 authority-baseline -->
## Competitor authority baseline policy

Free-tool access currently provides a reliable Tampa Bay Shine baseline but not a consistent comparable dataset for all competitor domains. The dashboard therefore loads the known Tampa Bay Shine Moz/Semrush baseline and defers competitor-authority comparison until comparable observations are available.

Do not populate missing competitor values by inference, search snippets, or cross-vendor substitution. The competitive SERP snapshot, category split, overlap, Top-3/Top-10 counts, visibility share, and Keyword Battle Board remain valid without competitor DA/DR data.

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

### Phase 11: SEO Action Workflow

Opportunity Intelligence now has persistent workflow state. Each generated opportunity receives a deterministic ID and moves through:

`New -> Investigating -> Implemented -> Measuring -> Closed`

State is stored separately in `cloudflare-site/seo-dashboard/data/opportunity-workflow.json`, so a daily analytics refresh does not erase human decisions. Run `python tools/opportunity_workflow.py sync` after regenerating Opportunity Intelligence.

Use `python tools/opportunity_workflow.py list` to review IDs. Use `status` for ordinary lifecycle changes such as `investigating`, `measuring`, or `closed`. Direct `status --status implemented` changes are blocked. When work has actually been implemented, use `python tools/opportunity_workflow.py implement --id <ID> --category <CATEGORY> --summary "<SUMMARY>"`; that command records the Implemented state and creates/links the SEO Event together. The `event` command remains available for additional later events. SEO Event timing is measurement context and does not prove causation.

The dashboard's Open Analysis view combines the current recommendation, retained GSC query/page history when available, Organic Search conversion context, related SEO Events, workflow state, and the 30/60/90-day measurement plan. A missing retained query/page history match is not treated as zero search activity.

The dashboard is static and intentionally does not write workflow state from the browser. Repository state remains the auditable source of truth.
