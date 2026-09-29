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
