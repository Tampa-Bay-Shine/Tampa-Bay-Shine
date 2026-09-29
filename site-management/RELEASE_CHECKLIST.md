# Release Checklist

## Before commit
- [ ] `seo_regression.py` passes for SEO/template/CRO changes
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
- [ ] CTA tracking events tested when CTA/shared JavaScript changed
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
- [ ] Explicit IndexNow submission run after production deployment when warranted
- [ ] Search Console/Bing follow-up when warranted

## Analytics release checks

When analytics, CTA markup, or shared JavaScript changes:
- [ ] `python.exe .\tools\analytics_regression.py .` passes
- [ ] staging does not initialize production Google Analytics
- [ ] production initializes `window.gtag`
- [ ] tracked CTA emits `tbs:conversion`
- [ ] GA4 Realtime / DebugView receives the expected event
- [ ] no PII appears in event parameters
