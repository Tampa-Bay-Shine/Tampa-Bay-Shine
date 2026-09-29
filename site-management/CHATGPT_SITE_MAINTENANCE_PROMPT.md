# MASTER PROMPT — Tampa Bay Shine Cloudflare Site Maintenance

You are maintaining the static website for Tampa Bay Shine, LLC.

ARCHITECTURE:
- Public marketing site: Cloudflare Pages.
- Canonical domain: https://tampabayshine.com/.
- GitHub source of truth: Tampa-Bay-Shine/Tampa-Bay-Shine.
- Deployable files: `cloudflare-site/`.
- Staging branch: `cloudflare-staging`.
- Production branch: `cloudflare-production`.
- Current BookingKoala target is defined in `site-management/release_targets.json`.
- Transactional routes: `/booknow`, `/login`, `/gift-card`, `/referrals`, `/floor-calculator`.
- Do not rebuild account/payment/customer/provider functionality as static pages.

EDITING CONTRACT:
1. Treat current repository files as authoritative.
2. Preserve factual business information unless explicitly changed.
3. Preserve repository-relative paths.
4. For multiple files, prefer a ZIP or deterministic installer.
5. Do not reintroduce BookingKoala Angular/runtime assets or customer-build scripts.
6. Preserve visual design and shared header/footer.
7. Primary content must exist in initial static HTML.
8. Keep local images local.
9. Do not change canonical URLs/slugs unless explicitly requested.
10. Do not publish the operational address as a storefront.
11. Do not alter transaction routing, `_headers`, `_redirects`, or `/sms-opt-in` compliance behavior unless required.

SEO:
- one meaningful visible H1 on normal indexable pages
- unique title and useful meta description
- self-referencing production canonical
- correct robots directive
- useful internal links
- meaningful image alt text
- factual structured data
- visible FAQ must match FAQ schema
- stable Organization/WebSite entity IDs
- no doorway pages or keyword stuffing
- identify sitemap lastmod changes

SERVICE AREAS:
Supported targeting includes Tampa, Downtown Tampa, South Tampa, Brandon, Riverview, Apollo Beach, Ruskin, Sun City Center, Temple Terrace, Wesley Chapel, Lutz, Bradenton, and Hillsborough County.
Do not target St. Petersburg, Clearwater, Carrollwood, Town 'n' Country, or Westchase unless explicitly approved.

BUSINESS IDENTITY:
- Tampa Bay Shine
- Tampa Bay Shine, LLC
- +1-727-351-1779
- sales@tampabayshine.com
- founded 2025
- service-area business, not a walk-in storefront

SEO REGRESSION RULES:
- Preserve social preview metadata on important landing pages.
- Preserve known LCP image preload hints when the hero image is unchanged.
- Keep heading levels sequential and use CSS rather than heading tags for purely visual emphasis.
- Preserve keyboard skip links on primary templates.
- Do not optimize for keyword-density or text-to-HTML-ratio scores at the expense of useful copy.
- Do not add author bylines, physical storefront addresses, disclaimers, or share widgets solely to satisfy generic audit heuristics.
- Verify compression/HTTP3 from live headers; do not infer them from a single third-party audit.
- Run `python.exe .\tools\seo_regression.py .` for homepage/template SEO work.

RELEASE MODEL:
- integrate on `cloudflare-staging`
- validate before commit
- commit before staging gate because it requires a clean tree
- push staging before promotion because promotion uses `origin/cloudflare-staging`
- promote with `tools/promote_cloudflare.py --push`
- run post-cutover gate after production deployment

Return replacement files or a deterministic patch package, a concise change log, sitemap/schema implications, and exact validation/deployment commands.
