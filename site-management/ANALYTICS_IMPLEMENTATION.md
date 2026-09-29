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

`booknow_click` is a handoff into BookingKoala, not a completed booking.

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

## Cross-domain BookingKoala handoff

Production promotion rewrites static transactional anchors from same-origin routes such as `/booknow` to the active BookingKoala base URL.

Example:

```text
/booknow
→ https://tampabayshine.bookingkoala.com/booknow
```

This is intentional. Google's linker needs the clicked anchor itself to be outbound to a configured linker domain so it can decorate the destination with `_gl` before navigation.

Staging source HTML continues to use internal transaction routes. `tools/promote_cloudflare.py` performs the absolute-link rewrite only while generating `cloudflare-production`.

The destination comes from `site-management/release_targets.json`; do not hard-code the fallback host across source page HTML.

After production deployment:
1. Click Book Now from `tampabayshine.com`.
2. Confirm the BookingKoala navigation is decorated with `_gl`.
3. Compare GA4 client IDs on both domains with:

```javascript
gtag('get', 'G-XK4CTL9KWM', 'client_id', console.log)
```

The client IDs should match. Matching identity continuity does not itself measure a completed booking.
