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

BookingKoala remains transactional. The active target is defined in `release_targets.json`:
- fallback: https://tampabayshine.bookingkoala.com
- future custom: https://booking.tampabayshine.com

Transactional routes:
- `/booknow`
- `/login`
- `/gift-card`
- `/referrals`
- `/floor-calculator`

Primary public content must be in initial static HTML.

## Source of truth

GitHub `cloudflare-site/` is authoritative. Old BookingKoala captures and the migration pipeline are archive/reference systems only.

## Deployment invariants

- `cloudflare-staging` deploys staging and carries global noindex.
- `cloudflare-production` deploys production.
- Production is generated from `origin/cloudflare-staging` with `tools/promote_cloudflare.py`.
- Promotion strips staging noindex and rewrites transaction redirects.
- Push staging before promotion.

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

Preserve shared static header/footer, page-specific CSS, responsive layouts, and local assets. Do not reintroduce BookingKoala Angular/runtime CSS or customer-build JavaScript.

## Functional boundary

Cloudflare Pages serves public information. BookingKoala owns accounts, booking, payments, provider functions, and dashboards.
