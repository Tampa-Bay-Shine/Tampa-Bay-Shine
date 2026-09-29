# Release Checklist

## Before commit
- [ ] On `cloudflare-staging`
- [ ] Pulled latest `origin/cloudflare-staging`
- [ ] `validate_site.py` passes
- [ ] `service_area_audit.py` passes
- [ ] `git diff --check` is clean
- [ ] Sitemap lastmod updated when appropriate
- [ ] Git diff reviewed

## Before staging push
- [ ] Commit created
- [ ] Working tree clean
- [ ] Staging migration gate GREEN
- [ ] Push `cloudflare-staging`

## Staging QA
- [ ] Deployment complete
- [ ] Changed URLs/assets return 200
- [ ] Desktop/mobile QA
- [ ] Raw HTML contains important content
- [ ] Metadata/canonical/robots/schema correct
- [ ] Booking/account routes tested when relevant

## Production
- [ ] Staging commit exists on `origin/cloudflare-staging`
- [ ] Run `promote_cloudflare.py --push`
- [ ] Production deployment complete
- [ ] Post-cutover gate GREEN
- [ ] Live pages/assets spot-checked
- [ ] Search Console/Bing follow-up when warranted
