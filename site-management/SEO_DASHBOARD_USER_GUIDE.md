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

**Weekly:** use the 28-day view and review Action Center, core search
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

Preservation of the original acquisition source through complete booking
is a separate measurement question and is being verified independently.

## Revenue

The dashboard does not currently report validated booking revenue. Do
not multiply booking counts by an assumed average price and call it
tracked revenue.

## A useful weekly review

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
