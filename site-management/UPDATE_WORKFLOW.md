# Ongoing Page Update Workflow

## Single-page update with ChatGPT
1. Open the current HTML file under `cloudflare-site/<slug>/index.html`.
2. If the page has page-specific CSS, also provide `cloudflare-site/assets/css/pages/<slug>.css`.
3. Give those complete current files to ChatGPT.
4. Tell ChatGPT to follow `site-management/CHATGPT_SITE_MAINTENANCE_PROMPT.md`.
5. Describe the requested changes.
6. Request complete replacement files, not snippets.
7. Replace only the returned files.
8. Run:
   `python tools/validate_site.py cloudflare-site`
9. For materially changed indexable pages, update sitemap lastmod:
   `python tools/update_sitemap.py cloudflare-site /<slug>`
10. Work on a branch, push, inspect the Cloudflare preview deployment, then merge.

## Updating several pages
Provide ChatGPT the complete current HTML/CSS files for every affected page and request a ZIP preserving paths beneath `cloudflare-site/`. After extracting: validate, update sitemap lastmod, review `git diff`, push a feature branch, inspect the Pages preview, then merge.

## Small edit directly in GitHub
For a typo or tiny content edit, use GitHub's editor on a branch/PR, inspect the Pages preview, and merge after QA.

## Never overwrite accidentally
Do not remove or alter without a specific reason:
- canonical tag
- title/meta description
- robots directive
- JSON-LD
- visible H1
- internal links
- local image paths
- shared header/footer
- /assets/css/main.css
- page-specific stylesheet
- booking/account route behavior
- SMS consent wording and Google Forms field names on /sms-opt-in

## Rollback
Use Git history or Cloudflare's known-good deployment. Do not restore an old BookingKoala capture over newer GitHub content.
