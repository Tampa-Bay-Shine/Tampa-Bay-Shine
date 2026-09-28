# Tampa Bay Shine Static Site Architecture

## Production architecture
- Public marketing website: Cloudflare Pages
- Canonical domain: https://tampabayshine.com/
- GitHub source of truth after cutover: Tampa-Bay-Shine/Tampa-Bay-Shine
- Deployable directory: cloudflare-site/
- Production branch after cutover: main
- Staging branch during migration: cloudflare-staging
- BookingKoala remains the transactional application at https://booking.tampabayshine.com/

Transactional routes:
- /booknow
- /login
- /gift-card
- /referrals
- /floor-calculator

Important public content must be present in the initial HTML response and must not depend on JavaScript rendering.

## Source of truth after cutover
After production cutover, GitHub `cloudflare-site/` is the source of truth for the public website. The old BookingKoala captures and migration pipeline remain a migration archive/reference system. Do not rerun the old capture-based migration pipeline over newer GitHub content unless intentionally rebuilding from the archive.

## URL rules
Preserve existing canonical public URLs unless there is a documented redirect plan.

Known aliases:
- /home -> /
- /move-out-cleaning-cost-guide-tampa -> /move-out-cleaning-cost-time-guide-tampa-bay

Move-out pages intentionally both exist:
- /move-out-cleaning-tampa-1 = general/hub
- /move-out-cleaning-tampa = Tampa-specific

## Service-area rules
Confirmed service footprint includes Tampa, Downtown Tampa, South Tampa, Brandon, Riverview, Apollo Beach, Ruskin, Sun City Center, Temple Terrace, Wesley Chapel, St. Petersburg, Lutz, Bradenton, and Hillsborough County.

Do not add Clearwater, Carrollwood, Town 'n' Country, or Westchase as targeted service areas without an explicit business decision.

Tampa Bay Shine is a service-area business. Do not publish the operational address as a storefront location.

## Design rules
Preserve the Phase 2.4 visual language:
- Royal blue primary: #0f0889
- Yellow accent: #f4c613
- Shared static header/footer
- Page-specific CSS under /assets/css/pages/
- Keep page-specific layouts, cards, grids, heroes, CTAs, spacing and responsive behavior
- Do not reintroduce BookingKoala Angular/runtime CSS, bk-*, tjs-*, generated elem_* IDs, or BookingKoala customer-build JavaScript

## Functional rule
Public informational pages are served by Cloudflare Pages. Account/booking/payment/customer-dashboard functions stay on BookingKoala.
