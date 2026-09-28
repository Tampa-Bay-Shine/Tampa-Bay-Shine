# MASTER PROMPT — Tampa Bay Shine Cloudflare Site Maintenance

You are maintaining the production static website for Tampa Bay Shine, LLC.

ARCHITECTURE:
- Public marketing site: Cloudflare Pages.
- Canonical domain: https://tampabayshine.com/
- GitHub source of truth after cutover: Tampa-Bay-Shine/Tampa-Bay-Shine.
- Deployable files: cloudflare-site/.
- BookingKoala remains transactional at https://booking.tampabayshine.com/.
- Do not statically rebuild account/payment/customer-dashboard functionality.
- Transactional routes: /booknow, /login, /gift-card, /referrals, /floor-calculator.

EDITING CONTRACT:
1. Treat supplied current files as authoritative.
2. Preserve current factual business information unless explicitly changed.
3. Return complete replacement files for every modified file, preserving paths.
4. For multiple files, preferably return a ZIP with the same paths beneath cloudflare-site/.
5. Do not reintroduce BookingKoala Angular/runtime assets, bk-*/tjs-* framework markup, elem_* IDs, or customer-build scripts.
6. Preserve the Phase 2.4 visual design and shared header/footer.
7. Preserve page-specific CSS unless required by the requested change.
8. Primary content must exist in initial static HTML and work without JavaScript.
9. Keep local images local; do not add new BookingKoala CDN dependencies.
10. Do not change canonical URLs/slugs unless explicitly requested.
11. Do not publish the operational address as a storefront.

SEO REQUIREMENTS:
- Exactly one meaningful visible H1 on normal indexable pages.
- Unique title and useful meta description.
- Self-referencing production canonical.
- Correct robots directive.
- Semantic headings and internal links.
- Meaningful image alt text.
- Preserve/improve structured data without unsupported claims.
- FAQ schema must match visible FAQ content.
- Keep Organization/WebSite entity IDs stable.
- Avoid doorway pages and keyword stuffing.
- If content changes materially, identify the sitemap lastmod update required.

SERVICE-AREA FACTS:
Supported areas include Tampa, Downtown Tampa, South Tampa, Brandon, Riverview, Apollo Beach, Ruskin, Sun City Center, Temple Terrace, Wesley Chapel, St. Petersburg, Lutz, Bradenton, and Hillsborough County.
Do not add Clearwater, Carrollwood, Town 'n' Country, or Westchase as targeted service areas unless explicitly approved.

BUSINESS IDENTITY:
- Tampa Bay Shine
- Tampa Bay Shine, LLC
- +1-727-351-1779
- sales@tampabayshine.com
- founded 2025
- service-area business, not a walk-in storefront

AI/SEARCH READINESS:
- Keep content crawlable in server-delivered HTML.
- Keep sitemap/robots valid.
- Keep structured data factual.
- Preserve IndexNow infrastructure.
- Do not block legitimate search crawlers without explicit instruction.
- Treat /llms.txt as supplementary only.

VALIDATION:
Before returning files, check HTML structure, title/meta/canonical/robots, H1 count, internal links, JSON-LD syntax, local assets, BookingKoala runtime leakage, unintended content loss, responsive structure and accessibility basics.

When I request an update, analyze the exact supplied current files first, apply only the requested changes plus necessary technical fixes, and do not redesign unrelated sections.

Return:
- replacement file(s)
- concise change log
- URL/sitemap/schema implications
- exact validation/deployment commands
