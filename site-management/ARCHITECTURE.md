# Tampa Bay Shine Static Site Architecture

## Current architecture

- Public marketing website: Cloudflare Pages
- Canonical domain: https://tampabayshine.com/
- GitHub source of truth: https://github.com/Tampa-Bay-Shine/Tampa-Bay-Shine
- Deployable directory: `cloudflare-site/`
- Staging branch: `cloudflare-staging`
- Production branch: `cloudflare-production`
- Staging Pages project: `tampa-bay-shine-staging`
- Production Pages project: `tampa-bay-shine`
- Active transaction mode: `first_party_embeds`

Primary public content must be present in the initial static HTML response.

## Functional boundary

Tampa Bay Shine owns:

- marketing and SEO landing pages;
- service discovery and service-intent routing;
- the first-party `/book/` booking wrapper;
- branded customer-facing login, gift-card, contact, guide, and service experiences;
- CTA instrumentation and booking-intent analytics emitted by the Cloudflare site.

BookingKoala remains the transaction engine for:

- service pricing and pricing parameters;
- scheduling and availability;
- customer and payment records;
- transaction completion;
- provider/operational functions;
- account functions not intentionally wrapped by a first-party Tampa Bay Shine page.

The goal is not to recreate BookingKoala. The Cloudflare site should provide the shortest possible bridge from customer intent to the BookingKoala transaction engine.

## Transaction configuration

`site-management/release_targets.json` is authoritative.

Current targets:

- fallback: https://tampabayshine.bookingkoala.com
- future custom: https://booking.tampabayshine.com

Current first-party routes include:

- `/book/`
- `/booknow` -> `/book/`
- `/login`
- `/gift-card`
- `/contact-us/`

External/support routes may still hand off to BookingKoala:

- `/referrals`
- `/floor-calculator`

The custom booking hostname must not be activated merely because DNS exists. It must work, be intentionally configured in BookingKoala, and pass transaction/login/analytics tests.

## Guided booking rules

Known residential service intents are expressed with friendly first-party parameters:

- `/book/?cleaning=standard` -> BookingKoala `service_id=6`
- `/book/?cleaning=deep` -> `service_id=18`
- `/book/?cleaning=move-out` -> `service_id=17`, one-time `frequency_id=1`
- `/book/?cleaning=deep-moving` -> `service_id=23`, one-time `frequency_id=1`
- `/book/` without a known `cleaning` value -> generic booking experience

Known Standard Cleaning frequency IDs:

- one-time `1`
- weekly `9`
- bi-weekly `4`
- every 3 weeks `5`
- every 4 weeks `2`

Customer-experience rule: if page context already identifies the cleaning type, do not ask the customer to choose it again.

Frequency selection may be offered as a convenience when it removes a later BookingKoala choice, but it must not become an unnecessary pre-booking gate. Do not duplicate bedrooms, bathrooms, square footage, extras, address, date, contact, or payment questions outside BookingKoala unless a later verified integration proves the duplicate question is eliminated downstream.

## Source of truth

GitHub `cloudflare-site/` is authoritative. Old BookingKoala captures and migration-pipeline output are archive/reference systems only.

## Deployment invariants

- `cloudflare-staging` deploys staging and carries global `X-Robots-Tag: noindex`.
- `cloudflare-production` deploys production.
- Production is generated from `origin/cloudflare-staging` with `tools/promote_cloudflare.py`.
- Promotion strips staging `noindex` and applies environment-specific transaction transformations.
- Push staging before promotion.
- Never copy staging `_headers` directly to production without the production transform.

## URL rules

Known aliases:

- `/home` -> `/`
- `/move-out-cleaning-cost-guide-tampa` -> `/move-out-cleaning-cost-time-guide-tampa-bay`

Intentional move-out pair:

- `/move-out-cleaning-tampa-1` = regional Tampa Bay hub
- `/move-out-cleaning-tampa` = Tampa-specific landing page

## Service-area rules

Supported targeting includes Tampa, Downtown Tampa, South Tampa, Brandon, Riverview, Apollo Beach, Ruskin, Sun City Center, Temple Terrace, Wesley Chapel, Lutz, Bradenton, and Hillsborough County.

Do not target St. Petersburg, Clearwater, Carrollwood, Town 'n' Country, or Westchase without explicit approval.

Tampa Bay Shine is a service-area business, not a walk-in storefront.

## Design rules

Preserve responsive behavior, local assets, accessible navigation, initial-HTML SEO content, and the shared visual system. Do not reintroduce BookingKoala Angular/runtime CSS or customer-build JavaScript into marketing pages.

The booking experience should reduce friction:

- infer service intent from the current page when known;
- use low-commitment residential CTAs such as `See My Price` where appropriate;
- avoid asking the same question in the wrapper and BookingKoala;
- keep commercial walkthrough/contact flows separate from residential instant-pricing flows.

## Analytics boundary

`cloudflare-site/assets/js/main.js` owns shared CTA event generation and emits `tbs:conversion`, dataLayer payloads when available, and direct GA4 events on production.

The `/book/` page also emits first-party guided-booking events for known service intent.

A booking CTA or guided-booking event is not proof of a completed booking. Completed-booking and revenue attribution require transaction-side or verified cross-domain measurement.

See:

- `site-management/ANALYTICS_IMPLEMENTATION.md`
- `site-management/CONVERSION_TRACKING.md`

## Cloudflare Resource Center (`/blog/`)

The public Cleaning Resource Center is Cloudflare-owned content.

- Hub: `cloudflare-site/blog/index.html`
- Articles: `cloudflare-site/blog/<slug>/index.html`
- Shared presentation: `cloudflare-site/assets/css/pages/blog.css`
- Canonical form: `https://tampabayshine.com/blog/<slug>/`
- Legacy BookingKoala/Medium material is source material only.
- Rebuild or consolidate overlapping topics instead of publishing near-duplicates.

Resource articles should preserve informational intent and link contextually to the appropriate service/location pages. They must not be used to create duplicate transactional landing pages.
