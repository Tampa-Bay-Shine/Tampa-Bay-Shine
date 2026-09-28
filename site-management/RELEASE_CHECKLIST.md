# Release Checklist

- [ ] Work on a feature/content branch
- [ ] Review git diff
- [ ] Run `python tools/validate_site.py cloudflare-site`
- [ ] Update sitemap lastmod for materially changed indexable pages
- [ ] Open Cloudflare preview deployment
- [ ] Desktop visual QA
- [ ] Mobile visual QA
- [ ] Test Book Now / Customer Login if shared navigation changed
- [ ] Check title/meta/canonical/robots
- [ ] Validate JSON-LD
- [ ] Check internal links
- [ ] Confirm no BookingKoala CDN/runtime leakage
- [ ] Confirm changed page content exists in raw HTML
- [ ] Merge
- [ ] Confirm production Pages deployment
- [ ] Spot-check production URL
- [ ] Confirm sitemap remains accessible
