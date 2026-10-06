# Tampa Bay Shine SEO Dashboard - Business Owner's Guide

## What it is

The Tampa Bay Shine SEO Dashboard is an internal business-performance
dashboard for Google Search and website conversion activity.

**Dashboard:** https://seo.tampabayshine.com/

It combines Google Search Console and Google Analytics 4 to answer:

1.  Are more potential customers finding Tampa Bay Shine in Google?
2.  Are those visitors taking actions that can become customers?

It does not replace BookingKoala, accounting, or a CRM.

## The funnel to remember

`Google visibility -> Google clicks -> website sessions -> booking starts -> confirmed bookings`

Each stage answers a different question. High impressions but few clicks
can indicate a search-result/ranking opportunity. Good traffic but few
booking starts can indicate a landing-page, offer, pricing, or CTA
issue. Many starts but few confirmed bookings can indicate booking
friction or an attribution issue.

## How often to review it

**Daily:** use the email brief and Performance Intelligence for triage. Do not make broad SEO changes from one day alone.

**Weekly:** use the 28-day view and review Opportunity Intelligence, Action Center, core search
metrics, Conversions, Winners & Losers, and tracked keywords.

**Monthly:** use 90 days to judge strategic direction. Ask whether
visibility, clicks, important queries, booking starts, and confirmed
bookings are improving.

Use 7 days for recent changes and early warnings, not major strategic
conclusions.

## Search metrics

**Impressions** = times a Tampa Bay Shine result was shown in Google.
This is visibility.

**Clicks** = Google Search clicks to the site. This is stronger than
visibility because the searcher actually visited.

**CTR** = clicks / impressions. Weak CTR can relate to position, title,
description, intent, competitors, SERP features, or brand familiarity.

**Average position** = Google's aggregate Search Console position
metric. Lower is better. It is not a guaranteed live rank; results vary
by query, location, device, time, and other factors.

## Conversion metrics

**Organic sessions** = visits GA4 attributes to Organic Search.

**Organic users** = users associated with Organic Search. One user can
have multiple sessions.

**Engaged sessions / engagement rate** = GA4 measures of meaningful
interaction. They are quality indicators, not sales.

**Booking starts** = tracked Book Now clicks (`booknow_click`). This is
strong intent, not a completed booking.

**Booking start rate** = Organic Search booking starts / Organic Search
sessions.

**Confirmed bookings** = BookingKoala's native `BookingByCustomer`
event. This is the dashboard's confirmed-booking signal.

**Confirmed booking rate** = Organic Search confirmed bookings / Organic
Search sessions.

**Booking completion rate** = Organic Search confirmed bookings /
Organic Search booking starts. Be cautious with small counts because one
booking can cause a large percentage swing.

**Primary intent actions** combine important commercial actions such as
Book Now, phone, commercial quote, and contact activity. They are not
all sales.

**Phone clicks** indicate a telephone-link click; the dashboard cannot
tell whether the call was answered or became a customer.

## Landing pages

The landing-page table shows where Organic Search visitors entered and
what happened afterward.

Look for high-traffic pages with weak commercial activity, which may
need conversion optimization, and lower-traffic pages with strong
booking activity, which may deserve more SEO attention. Avoid strong
conclusions from tiny samples.

## Tracked keywords and Top Queries

Tracked keywords are important Tampa searches monitored consistently
over time. Use them for direction, not as a complete picture.

Top Queries shows actual searches associated with Tampa Bay Shine
visibility. Look for local/service demand, unexpected searches,
high-impression/low-click queries, and searches approaching stronger
positions.

The Tracked Keywords and Top Queries table values are **current 28-day
aggregates**, not the latest day's values. Clicks and impressions are
28-day totals. CTR is total 28-day clicks divided by total 28-day
impressions. Average position is the impression-weighted GSC average for
the 28-day period. Position change is the number of positions gained or
lost versus the previous 28-day period; it is not a percentage.

## Interactive query and page trends

Tracked Keywords, Top Queries, Query Winners/Losers, and Page
Winners/Losers can be expanded to show daily Google Search Console
history. Use the arrow beside a query or page to open its chart. Only
one row is expanded at a time.

Timeframes are **1D**, **7D**, **30D**, **90D**, **180D**, **1Y**, and
**Custom**. Metrics are **Clicks**, **Impressions**, **Position**, and
**CTR**. The **Selected-period** summary above the chart recalculates
clicks, impressions, CTR, and impression-weighted average position for
the selected chart range.

The expanded row also shows **Latest reported day** metrics: the date,
position, impressions, clicks, and CTR from the final actual GSC daily
observation in that selected range. These latest-day values are separate
from the parent table's 28-day aggregates. For example, a table average
position of 15.8 and a latest chart point of 7.0 can both be correct.

SEO Event Log entries appear when their dates fall inside the selected
range. They provide context, not proof of causation.

Daily query charts use observations actually returned by GSC. Missing
low-volume/anonymized query dates should not be treated as confirmed
zeros. Low-volume queries can also produce large daily CTR swings; one
click from one impression is 100% daily CTR. Average position is an
aggregate GSC metric, not an exact live rank.

## Winners & Losers

These highlight meaningful period-over-period movement. A winner is not
automatically a business success and a loser is not automatically a
problem. Consider actual impression/click volume, relevance, ranking
movement, page purpose, and the reporting window.

## Opportunities and Cannibalization

Opportunities surface queries/pages near stronger positions, gaining
visibility, showing weak CTR, or losing visibility. They are
prioritization signals, not guarantees.

Cannibalization flags queries where multiple pages may compete. Multiple
pages appearing for one query is not automatically bad; review search
intent before consolidating or redirecting anything.

## Trends and SEO Events

Trends preserve historical snapshots. Use them to distinguish temporary
movement from sustained direction.

SEO Events record meaningful work such as technical changes, page
launches, content updates, and analytics changes. Event timing provides
context; it does not prove causation.

## Opportunity Intelligence

Opportunity Intelligence is the dashboard's cross-source weekly decision
queue. It combines evidence from Google Search Console, GA4 Organic
Search, identifiable AI referrals, controlled AI answer-visibility
observations, and the SEO Event Log.

**Act first** contains the small number of high-priority items supported
by the strongest current evidence.

**Investigation queue** contains medium-priority opportunities, anomalies,
and measurement gaps that deserve review but do not yet justify urgent
changes.

**Priority** describes business urgency. **Confidence** describes evidence
strength. They are not the same thing.

Read the Why flagged and Evidence fields before acting. A recommended
action is a reasoned next step, not proof that an edit will improve
rankings.

### Conversion context

**Ranking URL attribution** means matching GA4 Organic Search landing-page
evidence exists for the affected URL.

**Sitewide Organic Search context** means no matching landing-page row was
available. Those sessions, booking starts, and confirmed bookings describe
overall Organic Search and must not be attributed to that page.

Booking starts are intent, not confirmed sales. Confirmed bookings use
`BookingByCustomer`.

### AI context

Identifiable AI referral traffic and AI answer visibility are separate.
Zero identifiable AI referrals does not prove that AI systems never
mentioned Tampa Bay Shine. No-click AI exposure is not visible in GA4.

Controlled answer-visibility observations are needed to measure mentions
and citations. Until observations exist, the dashboard reports the
measurement gap rather than estimating visibility.

### 30 / 60 / 90 day measurement

Expand the measurement plan on an intelligence card when investigating
or changing something. Use 30 days for early evidence, 60 days for a
meaningful subsequent comparison, and 90 days for sustained visibility
plus Organic Search booking intent and confirmed-booking evidence.

Record material SEO changes in the SEO Event Log. Event timing provides
context but does not prove causation.

## Performance Intelligence

Performance Intelligence is the fast Daily, Weekly, and Monthly summary. Daily compares the latest complete GSC day with the prior day; Weekly compares the latest 7 complete days with the previous 7; Monthly compares the latest 28 days with the previous 28.

Headline impressions, clicks, CTR, and average position use authoritative date-only Search Console totals. Query/page movers use retained query/page histories, so they are evidence about specific searches and URLs rather than complete site-wide totals. Treat large percentage changes on tiny volumes cautiously.

## Daily SEO Performance Brief

After the successful scheduled 8 AM Eastern dashboard refresh, a concise email brief is sent to `marketing@tampabayshine.com`. It contains Daily, 7-day, and 28-day headline comparisons, up to three items that matter today, and a dashboard link.

The email is a triage summary, not a replacement for the dashboard. Use the dashboard for query/page evidence, conversion context, Opportunity Intelligence, SEO Events, and 30/60/90-day measurement.

## Action Center

**Striking distance:** useful visibility near a stronger position.

**Emerging opportunity:** Google is beginning to expose the site for a
potentially useful search.

**Visibility decline:** search visibility fell versus the comparison
period.

**CTR watch:** visibility exists but click-through behavior deserves
review.

**Page visibility decline:** a page lost visibility and deserves
investigation.

## Reading metric combinations

**Impressions up + clicks up:** visibility and traffic are expanding.

**Impressions up + clicks flat:** visibility expanded, but CTR/ranking
quality may need attention.

**Clicks up + booking starts up:** added search traffic is creating more
commercial intent.

**Sessions up + booking starts flat:** traffic grew without
corresponding booking intent.

**Booking starts up + confirmed bookings flat:** investigate booking
completion and attribution before blaming SEO.

**Confirmed Organic Search bookings rising over a meaningful period:**
strong evidence Organic Search is contributing to customer acquisition.

## Do not overreact to

One day, one unusual query, one manual ranking check, a percentage based
on tiny counts, one booking, or one week of normal position volatility.
Look for sustained patterns.

## Attribution limitation

GSC and GA4 measure different parts of the journey. GSC can show which
queries/pages generated search visibility and clicks. GA4 can show that
an Organic Search session later generated booking-related events.

The dashboard should not claim that a specific GSC query caused a
specific customer's booking.

## BookingKoala handoff

Customers leave TampaBayShine.com for BookingKoala. Google's
cross-domain linker is used to maintain analytics identity.

A production test verified the same GA4 Client ID before and after the
TampaBayShine.com -\> BookingKoala handoff. That confirms
client-identity continuity for the tested handoff.

Cross-domain client-identity continuity has been verified, and GA4 is
successfully assigning confirmed bookings to acquisition channels. A confirmed
Organic Search booking has not yet been observed in the available data. The
dashboard will automatically identify the first Organic Search
`BookingByCustomer` event when one occurs.

## Revenue

The dashboard does not currently report validated booking revenue. Do
not multiply booking counts by an assumed average price and call it
tracked revenue.

## A useful weekly review

For important tracked keywords and meaningful Winners/Losers, expand
the row and review the 30-day or 90-day chart before deciding whether a
change is sustained. Use 1Y when longer-term context is useful.


Ask:

-   Are 28-day impressions and clicks moving in the right direction?
-   Which queries/pages gained meaningful visibility?
-   Which pages are shown but not earning enough clicks?
-   How many Organic Search sessions occurred?
-   How many generated booking starts?
-   How many generated confirmed bookings?
-   Is booking completion improving?
-   Does Action Center identify something worth changing?
-   Did a recent SEO event occur near a trend worth monitoring?

## Access

Dashboard: https://seo.tampabayshine.com/

It is protected with Cloudflare Access and should be treated as internal
business-performance information.

## Seven questions the dashboard should answer

1.  Are we becoming more visible in Google?
2.  Are searchers clicking us?
3.  Are visitors engaging?
4.  Are they starting bookings?
5.  Are they completing bookings?
6.  Which pages/searches deserve attention?
7.  Are SEO improvements producing sustained business results?

Use the full funnel and longer-term trends rather than any single
metric.

On desktop, Winners & Losers tables are sized to remain within the
dashboard viewport. Longer queries, URLs, reasons, and headings wrap
rather than forcing the page wider. Low-volume Clicks and Impressions
charts may show decimal Y-axis scale labels so adjacent tick labels are
distinct; the actual GSC observations are still whole clicks/impressions.

### Phase 11: SEO Action Workflow

Opportunity Intelligence now has persistent workflow state. Each generated opportunity receives a deterministic ID and moves through:

`New -> Investigating -> Implemented -> Measuring -> Closed`

State is stored separately in `cloudflare-site/seo-dashboard/data/opportunity-workflow.json`, so a daily analytics refresh does not erase human decisions. Run `python tools/opportunity_workflow.py sync` after regenerating Opportunity Intelligence.

Use `python tools/opportunity_workflow.py list` to review IDs. Use `status` for ordinary lifecycle changes such as `investigating`, `measuring`, or `closed`. Direct `status --status implemented` changes are blocked. When work has actually been implemented, use `python tools/opportunity_workflow.py implement --id <ID> --category <CATEGORY> --summary "<SUMMARY>"`; that command records the Implemented state and creates/links the SEO Event together. The `event` command remains available for additional later events. SEO Event timing is measurement context and does not prove causation.

The dashboard's Open Analysis view combines the current recommendation, retained GSC query/page history when available, Organic Search conversion context, related SEO Events, workflow state, and the 30/60/90-day measurement plan. A missing retained query/page history match is not treated as zero search activity.

The dashboard is static and intentionally does not write workflow state from the browser. Repository state remains the auditable source of truth.
