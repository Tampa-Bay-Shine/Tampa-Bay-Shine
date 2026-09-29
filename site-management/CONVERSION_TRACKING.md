# Tampa Bay Shine Conversion Tracking

## Purpose

The public Cloudflare site includes first-party click instrumentation in `cloudflare-site/assets/js/main.js`.

The code exposes high-intent visitor actions so GTM, GA4, another analytics platform, or custom browser code can consume them.

The tracking code does **not** by itself store analytics data or send data to Google.

## Current events

| Event | Trigger |
|---|---|
| `booknow_click` | Click on `/booknow` |
| `phone_click` | Click on a `tel:` link |
| `contact_click` | Click on `/contact-us` from a non-commercial page |
| `commercial_quote_start` | Click on `/contact-us` from a commercial-intent page |
| `coupon_click` | Click on `/coupons` |
| `review_click` | Click on supported Google review/Maps links |

Commercial-intent path matching currently includes office-cleaning, commercial-cleaning, medical-office, common-area, floor-, gym-cleaning, post-construction, and post-event.

## Event payload

Each event contains:

```json
{
  "event": "booknow_click",
  "event_name": "booknow_click",
  "page_path": "/standard-cleaning-services-tampa",
  "link_url": "https://tampabayshine.com/booknow",
  "link_text": "Get My Exact Price"
}
```

Fields:
- `event` — event name used by GTM-style data layers
- `event_name` — duplicate event name for direct consumption
- `page_path` — current marketing-page path
- `link_url` — clicked destination
- `link_text` — visible CTA/link text, limited to 120 characters

## How events are emitted

Every qualifying click dispatches:

```javascript
window.dispatchEvent(new CustomEvent("tbs:conversion", { detail }));
```

If `window.dataLayer` already exists and is an array, the same payload is also pushed:

```javascript
window.dataLayer.push(detail);
```

Without GTM, GA4, or another collector, the event is not persisted.

## How to test now

Open DevTools Console and run:

```javascript
window.addEventListener("tbs:conversion", e => console.log(e.detail));
```

Then click a tracked CTA.

If GTM or another data-layer implementation exists, inspect:

```javascript
window.dataLayer
```

## Recommended GTM / GA4 setup

1. Create GTM Custom Event triggers for:
   - `booknow_click`
   - `phone_click`
   - `contact_click`
   - `commercial_quote_start`
   - `coupon_click`
   - `review_click`
2. Create Data Layer Variables for:
   - `page_path`
   - `link_url`
   - `link_text`
3. Send those values to GA4 as event parameters.
4. Test in GTM Preview / Tag Assistant.
5. Verify in GA4 DebugView / Realtime.
6. Mark only real business outcomes as GA4 key events.

Recommended key-event candidates:
- `booknow_click`
- `commercial_quote_start`
- `phone_click`

`coupon_click` and `review_click` are useful engagement events but should not automatically be treated as conversions.

## BookingKoala limitation

`booknow_click` measures only the handoff from the marketing site to BookingKoala. It does **not** prove a booking was completed.

A complete residential funnel should eventually measure:

```text
landing page
→ booknow_click
→ booking_start
→ booking_complete
```

Do not report `booknow_click` as a completed booking.

## Useful reports

Once GA4 is collecting these events, analyze by:
- landing page
- event name
- CTA text
- device
- source / medium
- campaign
- service/location page

Useful questions:
- Which pages generate the most Book Now clicks?
- Which pages get traffic but weak CTA engagement?
- Which commercial pages generate walkthrough interest?
- Which sources drive phone clicks?
- Which CTA wording performs best?

## Privacy

Current click instrumentation does not intentionally collect names, email addresses, phone numbers, payment information, or form-field values.

Do not add PII to analytics payloads.

## Maintenance rules

When changing CTAs or tracking:
- reuse existing event names when intent is unchanged;
- create new events only for materially different business actions;
- keep names lowercase with underscores;
- preserve `page_path`, `link_url`, and `link_text`;
- do not silently rename events after reporting begins;
- update this document when semantics change;
- verify events in DevTools before release.

## Source of truth

Implementation: `cloudflare-site/assets/js/main.js`

Documentation: `site-management/CONVERSION_TRACKING.md`
