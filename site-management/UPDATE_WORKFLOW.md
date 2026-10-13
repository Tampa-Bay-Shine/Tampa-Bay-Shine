# Ongoing Site Update Workflow

Use the root `README.md` as the primary runbook.

## Single page

1. Pull current `cloudflare-staging`.
2. Edit `cloudflare-site/<slug>/index.html`.
3. Edit page CSS only if needed.
4. Preserve canonical, robots, schema, H1, internal links, shared navigation, and local assets.
5. Run `validate_site.py`, `service_area_audit.py`, and `git diff --check`.
6. Update sitemap lastmod for material indexable changes.
7. Review diff.
8. Commit.
9. Run staging gate.
10. Push staging.
11. QA staging.
12. Promote with `promote_cloudflare.py --push`.
13. Run post-cutover gate.

## Multi-page/shared change

Use the same flow, but inspect representative page types on desktop/mobile and test shared navigation plus transaction links.

## New page

Create `cloudflare-site/<slug>/index.html`, add relevant internal links, and add the URL to the sitemap only if indexable.

## Rename/remove URL

Create a redirect first, update internal links/schema/sitemap, then remove the old page.

## ChatGPT-assisted work

Use `site-management/CHATGPT_SITE_MAINTENANCE_PROMPT.md` and current files as authoritative.

## Sensitive areas

Do not casually change transaction routes, `_headers`, `_redirects`, `/sms-opt-in` consent/form behavior, IndexNow key, entity IDs, or DNS/Cloudflare infrastructure.

## Rollback

Revert the bad staging commit, validate, push staging, and promote the corrected revision.

## SEO / CRO shared-change checks

For changes to priority landing pages, shared CSS, shared JavaScript, or conversion CTAs:
1. preserve Quick Answer blocks and CTA hierarchy;
2. preserve social metadata and stable hero-image preload rules;
3. run `python.exe .\tools\seo_regression.py .`;
4. verify conversion events in browser DevTools when CTA markup or `main.js` changes;
5. preserve event names unless an intentional analytics migration is planned;
6. update `CONVERSION_TRACKING.md` if event semantics or payloads change;
7. after production, notify IndexNow only for materially changed canonical pages.

## Updating the Cleaning Resource Center

For a new or materially revised guide:

1. Confirm the informational topic does not duplicate an existing article or cannibalize a transactional service/location page.
2. Prefer consolidation when BookingKoala, Medium, or existing Cloudflare sources cover substantially the same intent.
3. Use an answer-first structure: descriptive H1, concise Quick Answer, optional table of contents, substantive sections, useful tables/checklists where warranted, visible FAQ when warranted, and Related Resources.
4. Add contextual links to the primary service/location page and genuinely related guides.
5. Use local optimized images from `cloudflare-site/assets/images/`; do not hotlink BookingKoala CDN assets.
6. Keep the hub card, sitemap, `llms.txt`, canonical, Open Graph metadata, breadcrumb, and structured data synchronized with the article.
7. Run both blog audits and the normal site release validation suite.
8. Visually QA desktop and mobile staging before production promotion.

Do not invent historical publication dates. Use a publication date only when supported by the source record. A rebuild may use an accurate modification date when the template calls for it.
