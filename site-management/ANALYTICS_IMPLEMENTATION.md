# Tampa Bay Shine Analytics Implementation

## Purpose

This document describes the production website analytics implementation:
GA4, Google Ads base tagging, CTA events, BookingKoala cross-domain
measurement, confirmed-booking measurement, testing, and regression
safeguards.

For dashboard operations, credentials, automation, and troubleshooting,
see `site-management/SEO_DASHBOARD_OPERATIONS.md`.

For a nontechnical dashboard explanation, see
`site-management/SEO_DASHBOARD_USER_GUIDE.md`.

## Active identifiers

-   GA4 Measurement ID: `G-XK4CTL9KWM`
-   GA4 Property ID: `487638948`
-   Google Ads tag ID: `AW-17001979579`

## Architecture

The public Cloudflare site loads the Google tag only on
`tampabayshine.com` / `www.tampabayshine.com`, so normal staging QA does
not pollute production analytics.

Configured linker domains:

-   `tampabayshine.com`
-   `tampabayshine.bookingkoala.com`
-   `booking.tampabayshine.com`

Production promotion rewrites transactional anchors from internal routes
such as `/booknow` to the active BookingKoala base URL. This allows
Google's linker to decorate outbound navigation with `_gl`.

Do not hard-code BookingKoala hosts throughout source HTML. Continue
using the existing transaction-target workflow.

## CTA events

The shared JavaScript sends these events to GA4 while preserving the
`tbs:conversion` CustomEvent/dataLayer behavior:

-   `booknow_click`
-   `phone_click`
-   `contact_click`
-   `commercial_quote_start`
-   `coupon_click`
-   `review_click`

Event parameters include:

-   `page_path`
-   `link_url`
-   `link_text`

`booknow_click` means the visitor started the BookingKoala handoff. It
is not a completed booking.

## Confirmed BookingKoala bookings

BookingKoala natively emits the case-sensitive GA4 event:

`BookingByCustomer`

A real test booking verified that this event appears in GA4 Realtime and
is available through the GA4 Data API.

The SEO dashboard uses `BookingByCustomer` as the confirmed-booking
signal.

Do not replace it with `booknow_click`, a Thank You page view, or an
assumed completion.

Do not add a duplicate custom booking-complete event unless a specific
requirement is validated.

A one-time test refresh of the existing BookingKoala Thank You page did
not increase the native event count. This supports duplicate protection
for that tested workflow but is not a universal guarantee.

## Event semantics

  Event                      Meaning
  -------------------------- --------------------------------
  `booknow_click`            Booking start / intent
  `phone_click`              Lead intent
  `commercial_quote_start`   Lead intent
  `contact_click`            Lead intent
  `coupon_click`             Secondary intent
  `review_click`             Engagement
  `BookingByCustomer`        Confirmed BookingKoala booking

Never report a booking-start event as a completed booking.

## Cross-domain verification

A production test verified the following handoff:

`TampaBayShine.com -> Google _gl linker -> BookingKoala`

The BookingKoala destination contained the `_gl` parameter.

GA4 returned Client ID:

`1806746636.1790971052`

on TampaBayShine.com and the identical Client ID on BookingKoala.

This verifies GA4 client-identity continuity for that tested handoff.

It does not by itself prove that every acquisition source is preserved
through booking completion. Controlled acquisition-source continuity
through `BookingByCustomer`, especially Organic Search, remains a
separate attribution-quality verification.

## Google Ads

The production site loads base tag `AW-17001979579`.

Do not assume a Google Ads conversion merely because the base tag is
present. Conversion configuration should be verified separately before
reporting Ads conversions.

## Testing

Production console:

``` javascript
window.addEventListener("tbs:conversion", e => console.log("TBS", e.detail));
typeof window.gtag
```

`typeof window.gtag` should be `function` on production and normally
remain undefined on staging unless another tool loads it.

Client-ID check:

``` javascript
gtag('get', 'G-XK4CTL9KWM', 'client_id', console.log)
```

For a cross-domain test:

1.  open TampaBayShine.com in a clean browser session;
2.  capture the GA4 Client ID;
3.  click an actual Book Now link;
4.  confirm BookingKoala receives `_gl`;
5.  capture the BookingKoala GA4 Client ID;
6.  verify the IDs match.

Matching IDs verify identity continuity, not necessarily acquisition
attribution.

## GA4 Data API

Dashboard GA4 reporting uses property:

`487638948`

and the readonly scope:

`https://www.googleapis.com/auth/analytics.readonly`

The dashboard generator is:

`tools/ga4_dashboard.py`

Diagnostic event/channel auditing is available through:

`tools/ga4_conversion_audit.py`

## Regression

Run:

``` powershell
python.exe .\tools\analytics_regression.py .
```

The site migration gate also runs analytics regression in staging and
production phases.

For dashboard-specific generation and automation procedures, see
`site-management/SEO_DASHBOARD_OPERATIONS.md`.

## Privacy

Do not send or expose customer names, email addresses, telephone
numbers, payment details, form values, street addresses, or other PII in
analytics payloads or dashboard output.

BookingKoala may provide booking context to its native event, but
customer-linked booking IDs must not be surfaced in the SEO dashboard.

## Source-of-truth hierarchy

Website instrumentation:

`cloudflare-site/assets/js/main.js`

Analytics implementation documentation:

`site-management/ANALYTICS_IMPLEMENTATION.md`

Conversion-event definitions:

`site-management/CONVERSION_TRACKING.md`

Dashboard operations:

`site-management/SEO_DASHBOARD_OPERATIONS.md`

Business-owner dashboard guide:

`site-management/SEO_DASHBOARD_USER_GUIDE.md`
