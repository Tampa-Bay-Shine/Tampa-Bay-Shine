# MASTER PROMPT — Tampa Bay Shine Cloudflare Site Maintenance

You are maintaining the static website for Tampa Bay Shine, LLC.

ARCHITECTURE:
- Public marketing site: Cloudflare Pages.
- Canonical domain: https://tampabayshine.com/.
- GitHub source of truth: Tampa-Bay-Shine/Tampa-Bay-Shine.
- Deployable files: `cloudflare-site/`.
- Staging branch: `cloudflare-staging`.
- Production branch: `cloudflare-production`.
- Transaction mode and BookingKoala targets are defined in `site-management/release_targets.json`.
- Current production mode is `first_party_embeds`.
- `/book/` is the first-party residential booking wrapper; `/booknow` is a compatibility route into it.
- Known residential intent is passed with friendly `cleaning` parameters and translated to BookingKoala service/frequency IDs inside `/book/`.
- `/login`, `/gift-card`, and `/contact-us/` have first-party branded experiences; `/referrals` and `/floor-calculator` may still hand off externally.
- Do not rebuild pricing, scheduling, payment, customer-record, provider, or transaction-completion functionality outside BookingKoala.

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

PRIORITY PAGE / CRO RULES:
- Preserve visible answer-ready summaries, social image/card metadata, stable primary-image preload, and CTA hierarchy on priority pages.
- Treat the first-party booking layer as a friction reducer, not a second booking form.
- If page context already identifies the cleaning type, do not ask the customer to choose it again.
- Do not require pre-booking questions unless the answer reliably eliminates a later BookingKoala step.
- Prefer low-friction residential CTA wording such as `See My Price` where the visitor is still evaluating cost.
- Preserve first-party `tbs:conversion` click instrumentation in shared JavaScript.
- Do not claim GA4/GTM or completed BookingKoala conversion tracking is active unless verified.

TRACKING DOCUMENTATION:
- Read `site-management/CONVERSION_TRACKING.md` before changing CTA instrumentation.
- Preserve existing event names and payload fields unless an intentional analytics migration is requested.
- `booknow_click` is a handoff signal, not proof of a completed BookingKoala booking.
- Do not add PII to analytics payloads.
- When modifying CTAs, verify `tbs:conversion` behavior in addition to visual styling.

ANALYTICS:
- GA4 Measurement ID: G-XK4CTL9KWM.
- Google Ads tag ID: AW-17001979579.
- Production host only; do not pollute staging analytics.
- Preserve direct GA4 CTA events and existing `tbs:conversion` / dataLayer hooks.
- `booknow_click` is not a completed booking.
- Do not add PII to analytics events.
- Read `site-management/ANALYTICS_IMPLEMENTATION.md` before changing analytics.

## Resource Center maintenance context

The Cloudflare Cleaning Resource Center at `/blog/` is now an actively maintained part of the production marketing/SEO site.

When editing it:
- Treat current GitHub `cloudflare-staging` as the development source of truth.
- Preserve the approved Resource Center visual system in `assets/css/pages/blog.css`.
- New hub cards should use a local responsive image and maintain equal-height card/CTA alignment.
- Article components should align to the shared content width: contextual image, Quick Answer, TOC, tables, body copy, FAQ cards, and Related Resources.
- Use responsive local WebP/AVIF assets when available, with intrinsic dimensions, `srcset`, `sizes`, descriptive alt text, and lazy loading below the fold.
- Do not hotlink BookingKoala article imagery.
- Check inherited metadata/schema carefully when cloning an article template.
- Run `blog_content_audit.py` and `blog_link_audit.py` in addition to the normal site validators.
- Consolidate duplicate BK/Medium topics rather than generating thin or competing articles.
