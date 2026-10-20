# Tampa Bay Shine Analytics Implementation

## Active identifiers
- GA4 Measurement ID: `G-XK4CTL9KWM`
- Google Ads tag ID: `AW-17001979579`

## Architecture
The public Cloudflare site loads Google tag only on `tampabayshine.com` / `www.tampabayshine.com`, so staging QA does not pollute production analytics.

Linker domains:
- `tampabayshine.com`
- `tampabayshine.bookingkoala.com`
- `booking.tampabayshine.com`

## CTA events
The shared JavaScript sends these events directly to GA4 and preserves the existing `tbs:conversion` CustomEvent/dataLayer behavior:
- `booknow_click`
- `phone_click`
- `contact_click`
- `commercial_quote_start`
- `coupon_click`
- `review_click`

Event parameters:
- `page_path`
- `link_url`
- `link_text`

`booknow_click` measures entry into the residential booking path (`/book/` or `/booknow`) and is not a completed booking.

The first-party `/book/` guided layer also emits:

- `booking_guided_start` — a known `cleaning` intent was recognized;
- `booking_guided_continue` — the customer continued from the intent layer into the embedded BookingKoala workspace.

Guided-booking parameters currently include:

- `booking_intent`
- `booking_source`
- `guided_action` on continue/skip actions

These remain pre-transaction signals, not proof of booking completion.

## Recommended GA4 key events
Recommended:
- `booknow_click`
- `commercial_quote_start`
- `phone_click`

Keep `contact_click`, `coupon_click`, and `review_click` as engagement unless reporting needs change.

## Google Ads
The production site loads base tag `AW-17001979579`. No Google Ads conversion label is hard-coded. Preferred workflow is to collect events in GA4, mark important events as key events, link GA4 with Google Ads, and import those GA4 key events into Google Ads.

## Testing
Production console:
```javascript
window.addEventListener("tbs:conversion", e => console.log("TBS", e.detail));
typeof window.gtag
```

`typeof window.gtag` should be `function` on production and remain undefined on staging unless another tool loads it.

## Regression
Run:
```powershell
python.exe .\tools\analytics_regression.py .
```

The migration gate also runs the analytics regression in staging and production phases.

## Privacy
Do not add names, email addresses, phone numbers, payment details, form values, or other PII to analytics payloads.

## First-party booking and cross-domain BookingKoala measurement

The current production mode is `first_party_embeds`.

Residential CTAs normally stay on `tampabayshine.com` and enter `/book/`, optionally with a friendly service-intent parameter such as `?cleaning=deep`. The `/book/` page translates that intent into BookingKoala parameters and embeds `https://tampabayshine.bookingkoala.com/booknow?embed=true`.

`/booknow` is retained as a compatibility route into the first-party booking experience rather than as the normal direct BookingKoala handoff.

Google linker configuration still includes the BookingKoala domains because customers may use the fallback/open-in-new-page flow and transaction completion may cross domains.

Do not hard-code the fallback host across marketing page CTAs. The first-party booking wrapper owns normal residential entry.

After production deployment, verify:

1. Residential CTAs enter `/book/` and preserve known service intent.
2. The iframe/fallback target uses the expected BookingKoala host.
3. Guided events fire only on production.
4. If a customer leaves the iframe for a BookingKoala page, cross-domain identity continuity is preserved.
5. A booking CTA or guided event is never reported as a completed booking.

Where direct cross-domain navigation occurs, client identity can be compared with:

```javascript
gtag('get', 'G-XK4CTL9KWM', 'client_id', console.log)
```

Matching identity continuity does not itself measure a completed booking.
