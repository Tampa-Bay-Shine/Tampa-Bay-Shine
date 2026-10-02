# Tampa Bay Shine Conversion Tracking

## Purpose

This document defines the business meaning of Tampa Bay Shine analytics
events.

The public Cloudflare site includes first-party CTA instrumentation in
`cloudflare-site/assets/js/main.js`. GA4 persists those events on
production. BookingKoala separately emits its native confirmed-booking
event.

For implementation details, see
`site-management/ANALYTICS_IMPLEMENTATION.md`.

For dashboard operations, see
`site-management/SEO_DASHBOARD_OPERATIONS.md`.

## Conversion funnel

The primary measured funnel is:

`Google Search visibility -> website visit -> booknow_click -> BookingByCustomer`

For Organic Search dashboard reporting, this is interpreted as:

`Google visibility -> Google click -> Organic Search session -> booking start -> confirmed booking`

GSC and GA4 measure different portions of this journey. Do not claim
that an individual GSC query caused an individual later booking.

## Current events

  --------------------------------------------------------------------------
  Event                      Trigger / source        Business meaning
  -------------------------- ----------------------- -----------------------
  `booknow_click`            Click on a tracked Book Booking start / strong
                             Now CTA                 intent

  `phone_click`              Click on a `tel:` link  Lead intent

  `contact_click`            Click into general      Lead intent
                             contact path

  `commercial_quote_start`   Commercial-intent       Commercial lead intent
                             contact path

  `coupon_click`             Coupon-path click       Secondary intent

  `review_click`             Supported Google        Engagement
                             review/Maps click

  `BookingByCustomer`        Native BookingKoala GA4 Confirmed booking
                             event
  --------------------------------------------------------------------------

## First-party CTA payload

Qualifying site CTA events use a payload such as:

``` json
{
  "event": "booknow_click",
  "event_name": "booknow_click",
  "page_path": "/standard-cleaning-services-tampa",
  "link_url": "https://tampabayshine.com/booknow",
  "link_text": "Get My Exact Price"
}
```

Fields:

-   `event` - event name used by GTM-style data layers
-   `event_name` - event name for direct consumption
-   `page_path` - current marketing-page path
-   `link_url` - clicked destination
-   `link_text` - visible CTA/link text, limited by the implementation

## How first-party events are emitted

Each qualifying click dispatches:

``` javascript
window.dispatchEvent(new CustomEvent("tbs:conversion", { detail }));
```

The implementation also supports the data layer and production GA4
forwarding.

The browser event layer is useful for debugging and future integrations,
while GA4 provides persisted reporting.

## Confirmed bookings

`booknow_click` does not prove a booking was completed.

BookingKoala's native event:

`BookingByCustomer`

is the confirmed-booking event used by the SEO dashboard.

This event has been observed in GA4 Realtime and retrieved through the
GA4 Data API after a real test booking.

A tested Thank You page reload did not create an additional native
event. Treat this as a successful test result, not a universal
guarantee.

Do not create a second custom `booking_complete` event unless a new
validated requirement makes it necessary.

## Cross-domain attribution

Production uses Google's cross-domain linker between TampaBayShine.com
and BookingKoala.

A production test verified:

-   `_gl` decoration on the BookingKoala handoff;
-   identical GA4 Client IDs before and after the handoff.

Therefore client-identity continuity is verified for that test.

Acquisition-source continuity through the complete booking event is a
separate question. Do not relabel a Direct `BookingByCustomer` event as
Organic Search merely because the visitor may have interacted with the
site previously.

## Dashboard rate definitions

**Booking start rate**

Organic Search `booknow_click` events divided by Organic Search
sessions.

**Confirmed booking rate**

Organic Search `BookingByCustomer` events divided by Organic Search
sessions.

**Booking completion rate**

Organic Search `BookingByCustomer` events divided by Organic Search
`booknow_click` events.

These are event-count ratios and should not be presented as exact
unique-person probabilities.

## Useful analysis

Analyze by:

-   landing page
-   event name
-   acquisition channel
-   source/medium when appropriate
-   reporting period

Useful questions include:

-   Which landing pages generate booking starts?
-   Which landing pages generate confirmed Organic Search bookings?
-   Which pages receive traffic but weak CTA engagement?
-   Which sources drive phone or commercial-contact intent?
-   Where do booking starts fail to become confirmed bookings?

## Privacy

Do not intentionally collect or expose customer names, email addresses,
telephone numbers, payment information, street addresses, form-field
values, or customer-linked BookingKoala booking IDs in dashboard
analytics.

## Maintenance rules

When changing tracking:

-   reuse existing event names when the business meaning is unchanged;
-   create new events only for materially different actions;
-   do not silently rename events after reporting begins;
-   preserve established event semantics;
-   distinguish intent from completed outcomes;
-   test production events before relying on them;
-   update this document whenever semantics change;
-   verify dashboard queries after event changes;
-   do not expose PII.

`BookingByCustomer` is a BookingKoala native event and is
case-sensitive.

## Source of truth

First-party implementation:

`cloudflare-site/assets/js/main.js`

Event definitions:

`site-management/CONVERSION_TRACKING.md`

Analytics architecture:

`site-management/ANALYTICS_IMPLEMENTATION.md`

Dashboard operations:

`site-management/SEO_DASHBOARD_OPERATIONS.md`

Business-owner guide:

`site-management/SEO_DASHBOARD_USER_GUIDE.md`
