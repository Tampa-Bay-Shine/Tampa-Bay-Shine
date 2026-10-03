# Tampa Bay Shine Website Repository

This repository is the source of truth for the Tampa Bay Shine public marketing website.

- **Production site:** https://tampabayshine.com
- **Staging site:** https://tampa-bay-shine-staging.pages.dev
- **GitHub repository:** https://github.com/Tampa-Bay-Shine/Tampa-Bay-Shine
- **Deployable site directory:** `cloudflare-site/`
- **Staging branch:** `cloudflare-staging`
- **Production branch:** `cloudflare-production`
- **Public business email:** sales@tampabayshine.com
- **Phone:** +1-727-351-1779

> `cloudflare-staging` and `cloudflare-production` are the Cloudflare deployment branches. Do not use `main` as the production deployment branch unless the Cloudflare project configuration is deliberately changed.

---

## 1. Architecture at a glance

The public marketing site is a static Cloudflare Pages site. Important content must be present in the initial HTML response; do not make primary SEO content depend on client-side JavaScript.

BookingKoala remains the transactional application. These public routes redirect into BookingKoala:

- `/booknow`
- `/login`
- `/gift-card`
- `/referrals`
- `/floor-calculator`

The active transaction target is controlled by `site-management/release_targets.json`.

Current modes:

- `bookingkoala_fallback` -> `https://tampabayshine.bookingkoala.com`
- future `custom_booking` -> `https://booking.tampabayshine.com`

The custom booking hostname must not be activated merely because DNS exists. It must work, be made BookingKoala Primary when appropriate, and pass the manual transaction tests before switching modes.

### Cloudflare projects

| Environment | Cloudflare Pages project | Git branch | URL |
|---|---|---|---|
| Staging | `tampa-bay-shine-staging` | `cloudflare-staging` | https://tampa-bay-shine-staging.pages.dev |
| Production | `tampa-bay-shine` | `cloudflare-production` | https://tampabayshine.com |

The production Pages project serves the apex domain. `www` redirects to the apex at Cloudflare. The production `pages.dev` hostname redirects to the apex.

---

## 2. Repository layout

```text
Tampa-Bay-Shine/
|-- cloudflare-site/               Deployable static website
|   |-- index.html                 Homepage
|   |-- <slug>/index.html          Public pages
|   |-- assets/
|   |   |-- css/main.css           Shared CSS
|   |   |-- css/pages/             Page-specific CSS
|   |   |-- images/                Local site images
|   |   `-- js/main.js             Shared JavaScript
|   |-- _headers                   Cloudflare Pages headers
|   |-- _redirects                 Redirect rules, including transaction routes
|   |-- robots.txt
|   |-- sitemap.xml
|   |-- llms.txt
|   |-- site.webmanifest
|   `-- 3631fda1114542beac8b749d5ed827ad.txt   IndexNow key
|-- tools/                         Validation, preview, release, and maintenance tools
|-- site-management/               Architecture, release policy, SEO rules, and config
|-- reports/                       Local gate reports; ignored by Git
`-- README.md                      Primary developer runbook
```

`cloudflare-site/` is authoritative after cutover. Old BookingKoala captures or migration-pipeline output are archive/reference material only. Never overwrite current GitHub content by rerunning an old capture pipeline unless an intentional rebuild is being performed.

---

## 3. First-time developer setup

Requirements:

- Git
- Python 3
- `pip`
- `curl`
- access to this GitHub repository
- Cloudflare access only when deployment/DNS configuration must be inspected or changed

Clone and initialize:

```powershell
git clone https://github.com/Tampa-Bay-Shine/Tampa-Bay-Shine.git
cd Tampa-Bay-Shine
git fetch --all --prune
git switch cloudflare-staging
git pull origin cloudflare-staging
python.exe -m pip install beautifulsoup4
git status
```

Normal work starts from a clean `cloudflare-staging` branch.

---

## 4. Branch and deployment model

### `cloudflare-staging`

This is the integration/development branch used by the staging Cloudflare Pages project.

A push to `origin/cloudflare-staging` deploys staging.

Staging intentionally has a global `X-Robots-Tag: noindex` header. Do not remove it.

### `cloudflare-production`

This is the production deployment branch. Do not normally develop directly on it.

Production is generated from the exact remote staging revision by:

```powershell
python.exe .\tools\promote_cloudflare.py --repo . --push
```

The promotion tool:

1. requires `cloudflare-staging`;
2. requires a clean working tree;
3. runs the staging migration gate;
4. fetches `origin/cloudflare-staging`;
5. resets production content to that exact remote staging revision;
6. removes the staging global `noindex` header;
7. rewrites BookingKoala transaction redirects to the active configured target;
8. commits the transformed production tree;
9. runs the production gate;
10. pushes `cloudflare-production` only with `--push`;
11. returns the checkout to `cloudflare-staging`.

**Important:** push staging before promotion. The tool promotes `origin/cloudflare-staging`, not an unpushed local commit.

### Feature branches

Feature branches are optional for larger changes or peer review. Merge approved work into `cloudflare-staging`, push staging, QA staging, and then promote normally.

Do not assume a feature branch has a Cloudflare preview URL unless the Pages project is configured for branch previews.

---

## 5. Standard content or SEO change

Start clean:

```powershell
git switch cloudflare-staging
git pull origin cloudflare-staging
git status
```

Edit:

```text
cloudflare-site/<slug>/index.html
```

and, if needed:

```text
cloudflare-site/assets/css/pages/<slug>.css
```

Validate before commit:

```powershell
python.exe .\tools\validate_site.py .\cloudflare-site
python.exe .\tools\service_area_audit.py --repo .
git diff --check
git diff
```

For a materially changed indexable page:

```powershell
python.exe .\tools\update_sitemap.py .\cloudflare-site /<slug>
```

For the homepage:

```powershell
python.exe .\tools\update_sitemap.py .\cloudflare-site /
```

Commit:

```powershell
git add .
git commit -m "Describe the change"
```

The staging gate requires a clean working tree, so run it **after** committing:

```powershell
python.exe .\tools\migration_gate.py --repo . --phase staging
```

If GREEN:

```powershell
git push origin cloudflare-staging
```

Wait for Cloudflare to deploy staging, then inspect the affected URL.

Promote:

```powershell
python.exe .\tools\promote_cloudflare.py --repo . --push
```

After production deploys:

```powershell
python.exe .\tools\migration_gate.py --repo . --phase post-cutover
```

Spot-check live:

```powershell
curl.exe -I https://tampabayshine.com/<slug>
curl.exe -sS -L https://tampabayshine.com/<slug> -o live-page.html
```

Delete temporary local files when finished or keep them outside the repo.

---

## 6. Local preview

```powershell
python.exe .\tools\preview_site.py
```

Open `http://localhost:8080`.

The local preview redirects transactional routes to the live public domain. It is a static visual/content preview, not a local BookingKoala environment.

---

## 7. Tool reference

### `tools/validate_site.py`

```powershell
python.exe .\tools\validate_site.py .\cloudflare-site
```

Checks title, meta description, canonical, robots, H1 count, JSON-LD syntax, internal links, BookingKoala runtime/CDN leakage, and required support files. It exits nonzero on errors; H1-count findings are warnings.

### `tools/service_area_audit.py`

```powershell
python.exe .\tools\service_area_audit.py --repo .
```

Currently blocks St. Petersburg, Clearwater, and Carrollwood in public HTML.

This is a regression guard, not a complete geographic policy checker. Also avoid Town 'n' Country or Westchase as targeted locations unless explicitly approved.

### `tools/service_area_cleanup.py`

Dry run:

```powershell
python.exe .\tools\service_area_cleanup.py --repo .
```

Apply:

```powershell
python.exe .\tools\service_area_cleanup.py --repo . --apply
```

This is a special mechanical cleanup utility, not a normal formatter. Always dry-run and review the diff before committing.

### `tools/update_sitemap.py`

```powershell
python.exe .\tools\update_sitemap.py .\cloudflare-site /services /office-cleaning
```

Updates `<lastmod>` only for URLs already present in `sitemap.xml`. It does not add new sitemap entries.

### `tools/migration_gate.py`

```powershell
python.exe .\tools\migration_gate.py --repo . --phase staging
python.exe .\tools\migration_gate.py --repo . --phase production
python.exe .\tools\migration_gate.py --repo . --phase post-cutover
```

Staging/production phases require the expected branch and a clean tree. `promote_cloudflare.py` invokes staging and production phases automatically. Run `post-cutover` yourself after production deployment. Reports are written under `reports/`.

### `tools/promote_cloudflare.py`

Dry production preparation:

```powershell
python.exe .\tools\promote_cloudflare.py --repo .
```

Production push:

```powershell
python.exe .\tools\promote_cloudflare.py --repo . --push
```

### `tools/seo_regression.py`

Checks homepage/template SEO safeguards introduced from recurring external audits:

```powershell
python.exe .\tools\seo_regression.py .
```

It checks homepage title/description review thresholds, social image/card metadata, LCP image preload, skip-to-content behavior, heading-level continuity, JSON-LD syntax, and required security headers. Run it after homepage, shared-template, metadata, or `_headers` changes.

### `tools/submit_indexnow.py`

Validates the IndexNow setup and can explicitly submit the live production sitemap URLs.

Dry run:

```powershell
python.exe .\tools\submit_indexnow.py --repo .
```

Live submission, after production has deployed:

```powershell
python.exe .\tools\submit_indexnow.py --repo . --live
```

Live mode verifies the production key file, fetches the live production sitemap, refuses staging/non-canonical hosts, submits to `https://api.indexnow.org/indexnow`, accepts HTTP 200 or 202, and writes a JSON report under `reports/`.

To submit only selected sitemap URLs:

```powershell
python.exe .\tools\submit_indexnow.py --repo . --live `
  --url /move-out-cleaning-tampa `
  --url /move-out-cleaning-tampa-1
```

Selected URLs must already exist in the production sitemap. IndexNow acceptance confirms receipt, not guaranteed crawl timing, indexing, or ranking.

### `tools/gsc_index_audit.py`

Purpose: audit the index state of every canonical URL in `cloudflare-site/sitemap.xml` using the Google Search Console URL Inspection API.

Why it exists: the Search Console Pages report does not always make recent crawl timing obvious. This tool exposes Google's per-URL indexed-version fields, including `lastCrawlTime`, coverage state, fetch state, robots state, and Google/user canonicals, so Cloudflare migrations and later SEO releases can be verified page by page.

First-time prerequisites are documented in `site-management/GSC_AUDIT_TOOLS.md`. Normal run:

```powershell
python.exe .\tools\gsc_index_audit.py
```

Use a deployment freshness baseline when needed:

```powershell
python.exe .\tools\gsc_index_audit.py --baseline 2026-09-28
```

Reports are written under `reports/gsc-index-audit/` and are intentionally ignored by Git. The API reports Google's indexed-version data; it is not equivalent to Search Console's live URL test.

### `tools/gsc_performance_audit.py`

Purpose: pull Search Console page, query, and query/page performance for a current period and the immediately preceding comparison period, then surface data-driven SEO opportunities.

Why it exists: local/service optimization should be based on actual Search Console demand rather than generic keyword assumptions. The tool identifies query/page pairs in striking distance, low-CTR opportunities, page-level opportunity clusters, and queries that may warrant cannibalization review.

Normal 90-day comparison:

```powershell
python.exe .\tools\gsc_performance_audit.py
```

Shorter comparison:

```powershell
python.exe .\tools\gsc_performance_audit.py --days 28
```

The generated `opportunity_score` is a local prioritization heuristic only; it is not a Google metric or ranking factor. Reports are written under `reports/gsc-performance/`.

### SEO dashboard query metric semantics

The private SEO dashboard's Tracked Keywords and Top Queries tables use
the current 28-day GSC period: clicks/impressions are totals, CTR is
clicks divided by impressions, and position is the impression-weighted
average. Position change is positions gained/lost versus the previous
28-day period, not a percentage.

Expanded query/page charts use actual retained daily GSC observations
for the selected trend range. Their selected-period aggregate and
Latest reported day are displayed separately; the last daily chart
point is not expected to equal the parent table's 28-day aggregate.
Missing query dates are not interpolated or treated as confirmed zeros.

### `tools/opportunity_intelligence.py`

Builds the cross-source SEO/AEO Opportunity Intelligence queue used by
the private SEO dashboard.

Run:

    python.exe .\tools\opportunity_intelligence.py

Output:

    cloudflare-site/seo-dashboard/data/opportunity-intelligence.json

The generator combines existing aggregate evidence from Google Search
Console, GA4 Organic Search, identifiable AI referrals, controlled AI
answer-visibility observations, and the SEO Event Log.

Priority and confidence are separate. High priority is reserved for the
strongest current business-action signals. Medium-priority items remain
visible as an investigation queue.

The generator does not use an opaque composite SEO score, fabricate
missing observations, treat booking starts as confirmed bookings, or
claim that SEO event timing proves causation. Sitewide GA4 context must
not be presented as page-level attribution.

The GSC Action Center remains the Search Console diagnostic layer.
Opportunity Intelligence is the cross-source business decision layer.

### `tools/set_transaction_mode.py`

Fallback:

```powershell
python.exe .\tools\set_transaction_mode.py fallback --repo .
```

Future custom booking domain:

```powershell
python.exe .\tools\set_transaction_mode.py custom --repo .
```

This modifies `site-management/release_targets.json`. Commit/push that config change to staging, rerun all transaction/manual tests, then promote normally. Do not switch to custom while `https://booking.tampabayshine.com` is unhealthy.

### `tools/preview_site.py`

Starts the local static preview on `127.0.0.1:8080`.

---

## 8. Adding a new page

Create:

```text
cloudflare-site/<new-slug>/index.html
```

and, if needed:

```text
cloudflare-site/assets/css/pages/<new-slug>.css
```

A normal indexable page should have:

- one useful visible H1
- unique title
- useful meta description
- self-referencing production canonical
- correct robots directive
- important content in initial static HTML
- descriptive internal links
- meaningful image alt text
- valid factual JSON-LD
- shared header/footer
- no BookingKoala Angular/runtime assets

Add the canonical URL to `cloudflare-site/sitemap.xml` only if it is indexable and returns 200. Add internal links from relevant hubs; do not create orphan pages.

Then follow the standard validation, staging, and promotion workflow.

---

## 9. Removing or renaming a page

Do not simply delete an indexed URL.

1. Choose the best surviving destination.
2. Add a permanent redirect to `cloudflare-site/_redirects`.
3. Update internal links.
4. Remove the old URL from the sitemap.
5. Update structured-data references.
6. Delete the old page after the redirect plan exists.
7. Validate and test on staging and production.

Known aliases:

```text
/home -> /
/move-out-cleaning-cost-guide-tampa -> /move-out-cleaning-cost-time-guide-tampa-bay
```

These two URLs intentionally both exist:

```text
/move-out-cleaning-tampa-1   regional Tampa Bay hub
/move-out-cleaning-tampa     Tampa-specific landing page
```

Do not merge/canonicalize them together without an intentional SEO migration plan.

---

## 10. Shared navigation, footer, CSS, or JavaScript

A shared-component edit can affect every page.

For shared header/footer edits:

- apply consistently;
- validate internal links;
- test desktop/mobile navigation;
- test Book Now and Customer Login;
- verify primary content remains in raw HTML.

For `assets/css/main.css` or `assets/js/main.js`, inspect multiple page types and mobile behavior.

If cache-busting query strings change, update them consistently.

---

## 11. Images, favicon, and manifest

Store normal public images under `cloudflare-site/assets/images/`.

Current root site-icon assets:

```text
favicon.ico
favicon-16x16.png
favicon-32x32.png
favicon-48x48.png
apple-touch-icon.png
android-chrome-192x192.png
android-chrome-512x512.png
site.webmanifest
```

When replacing a brand icon, preserve filenames unless references are intentionally changed. Verify all assets return 200 on staging and production.

Organization `logo` schema should use the high-resolution brand logo, not the favicon.

---

## 12. Sitemap, robots, IndexNow, Google, and Bing

`robots.txt` must advertise:

```text
Sitemap: https://tampabayshine.com/sitemap.xml
```

The sitemap should contain only canonical, indexable HTTP-200 pages.

IndexNow key file:

```text
cloudflare-site/3631fda1114542beac8b749d5ed827ad.txt
```

Do not delete/rotate it accidentally.

Temporary files such as `live-sitemap.xml` and `indexnow-payload.json` are local working artifacts and should not be committed.

After a verified production deployment, run `python.exe .\tools\submit_indexnow.py --repo . --live` when an explicit IndexNow notification is warranted. Then verify important URLs in Google Search Console and Bing Webmaster Tools. A successful deployment or IndexNow acceptance does not guarantee reindexing.

---

## 13. BookingKoala transaction changes

Configuration:

```text
site-management/release_targets.json
```

Manual readiness state:

```text
site-management/release_gate_manual.json
```

Before changing BookingKoala Primary domain or transaction mode, test:

- admin login
- customer login
- provider app/session
- recurring booking/job visibility
- sender email
- links in system email
- links in SMS
- `/booknow`
- `/login`
- `/gift-card`
- `/referrals`
- `/floor-calculator`

The fallback domain remains active until the custom booking hostname is healthy and intentionally activated.

---

## 14. Service-area policy

Supported targeting currently includes:

- Tampa
- Downtown Tampa
- South Tampa
- Brandon
- Riverview
- Apollo Beach
- Ruskin
- Sun City Center
- Temple Terrace
- Wesley Chapel
- Lutz
- Bradenton
- Hillsborough County

Do not target:

- St. Petersburg
- Clearwater
- Carrollwood
- Town 'n' Country
- Westchase

unless the business explicitly changes the footprint.

Tampa Bay Shine is a service-area business. Do not represent the operational address as a walk-in storefront.

`/sms-opt-in` contains compliance-specific address/consent/form behavior. Do not casually rewrite its consent wording, Google Forms field names, or processing logic.

---

## 15. SEO and structured-data rules

Read `site-management/SEO_AI_SEARCH_RULES.md` before broad SEO work.

Stable IDs include:

```text
https://tampabayshine.com/#organization
https://tampabayshine.com/#website
https://tampabayshine.com/<slug>#webpage
https://tampabayshine.com/<slug>#service
https://tampabayshine.com/<slug>#faq
https://tampabayshine.com/<slug>#breadcrumb
```

Business identity:

```text
Tampa Bay Shine
Tampa Bay Shine, LLC
+1-727-351-1779
sales@tampabayshine.com
Founded 2025
```

Visible FAQ text must match FAQ schema. Do not publish unsupported reviews, prices, guarantees, credentials, service areas, or storefront claims.

---

## 16. Cloudflare and DNS changes

Routine site content releases do not require DNS changes.

DNS, nameserver, DNSSEC, Pages custom-domain, `www` redirect, and production `pages.dev` redirect work are separate infrastructure operations. Document the reason before changing them.

Current authoritative nameservers are Cloudflare. Do not switch nameservers back to GoDaddy as part of normal maintenance.

Do not alter BookingKoala DNS records merely to release content.

---

## 17. Release checklist

Before staging push:

```text
[ ] Branch is cloudflare-staging
[ ] Current files used, not old migration captures
[ ] validate_site.py passes
[ ] service_area_audit.py passes
[ ] git diff --check is clean
[ ] Sitemap lastmod updated when appropriate
[ ] Git diff reviewed
[ ] Commit created
[ ] staging migration gate is GREEN
```

After staging push:

```text
[ ] Staging deploy completed
[ ] Changed URLs/assets return 200
[ ] Desktop QA
[ ] Mobile QA
[ ] Raw HTML contains important content
[ ] Metadata/canonical/robots/schema checked
[ ] Transaction links tested if affected
```

Production:

```text
[ ] Staging commit pushed to origin
[ ] promote_cloudflare.py --push completed
[ ] Production deploy completed
[ ] post-cutover migration gate is GREEN
[ ] Live URLs/assets spot-checked
[ ] Search-engine follow-up performed when warranted
```

---

## 18. Rollback

For a bad content release:

1. identify the bad staging commit;
2. revert it on `cloudflare-staging`;
3. validate and push staging;
4. promote the corrected staging revision;
5. run the post-cutover gate.

Cloudflare deployment rollback may be used as an emergency measure, but Git must be reconciled afterward.

Never restore an old BookingKoala capture over current GitHub content.

---

## 19. Working with ChatGPT or another coding assistant

Use `site-management/CHATGPT_SITE_MAINTENANCE_PROMPT.md`.

Always retrieve/provide current files first. For multi-file work, preserve repository-relative paths and review generated changes with Git.

If a connected GitHub integration is read-only, use a generated ZIP/installer locally and then follow the staging -> production workflow here.

---

## 20. Additional documentation

- `site-management/ARCHITECTURE.md`
- `site-management/DEV_PROD_RELEASE_WORKFLOW.md`
- `site-management/UPDATE_WORKFLOW.md`
- `site-management/RELEASE_CHECKLIST.md`
- `site-management/SEO_AI_SEARCH_RULES.md`
- `site-management/CHATGPT_SITE_MAINTENANCE_PROMPT.md`
- `site-management/SSL_MIGRATION_GUIDE.md` — historical SSL/migration reference, not routine deployment procedure

The root README is the primary operational runbook. Supporting documents should be kept consistent with it.

- `site-management/SEO_SECOND_PASS_2026-09-30.md` — second-pass answerability and internal-link cleanup while post-release recrawl is pending
- `site-management/GSC_AUDIT_TOOLS.md` — Search Console index/performance audit purpose, OAuth setup, usage, outputs, and interpretation
- `site-management/SEO_AI_CRO_90_DAY_PLAN.md` — 90-day search, AI visibility, paid-search and conversion roadmap


### Conversion event hooks

`assets/js/main.js` emits `booknow_click`, `phone_click`, `contact_click`, `commercial_quote_start`, `coupon_click`, and `review_click` as `tbs:conversion` browser events. If `window.dataLayer` exists, the same event object is pushed into it.

GA4 is installed on production and these hooks are forwarded to GA4. Booking-start intent is measured with `booknow_click`, while completed BookingKoala bookings are measured separately with BookingKoala's native `BookingByCustomer` event.

## Conversion tracking and analytics

The public site has first-party CTA instrumentation in `cloudflare-site/assets/js/main.js`.

Tracked events:
- `booknow_click`
- `phone_click`
- `contact_click`
- `commercial_quote_start`
- `coupon_click`
- `review_click`

Each qualifying click dispatches a browser `tbs:conversion` CustomEvent. If `window.dataLayer` exists, the same payload is pushed into it.

The first-party event layer is forwarded to the production GA4 implementation. The browser CustomEvent/dataLayer hooks remain vendor-neutral, while GA4 provides persistence/reporting.

Full definitions, payloads, GTM/GA4 setup guidance, testing steps, privacy rules, and BookingKoala attribution limitations are in `site-management/CONVERSION_TRACKING.md`.

Do not treat `booknow_click` as a completed booking.

## Analytics implementation

Production analytics use GA4 `G-XK4CTL9KWM` and Google Ads tag `AW-17001979579`.

The Google tag initializes only on the production hostname, so Cloudflare staging traffic is excluded. Existing CTA events are sent directly to GA4 while preserving the `tbs:conversion` CustomEvent/dataLayer hooks.

Run `python.exe .\tools\analytics_regression.py .`.

See `site-management/ANALYTICS_IMPLEMENTATION.md` for event definitions, cross-domain setup, key-event recommendations, Google Ads guidance, testing, and BookingKoala limitations.

## Cross-domain transaction links

Staging HTML uses internal transaction routes (`/booknow`, `/login`, `/gift-card`, `/referrals`, `/floor-calculator`).

During production promotion, `tools/promote_cloudflare.py` rewrites transactional `<a>` links to the active BookingKoala base URL from `site-management/release_targets.json`. This allows Google's linker to decorate outbound BookingKoala navigation for GA4 cross-domain identity continuity.

The `_redirects` entries remain as fallback routes for manually entered/internal transaction URLs.

Do not manually hard-code BookingKoala hosts across source HTML. Change transaction mode through the existing release-target workflow.

## SEO and analytics dashboard

Internal dashboard:

https://seo.tampabayshine.com/

The dashboard combines Google Search Console visibility data with GA4
website/conversion data. It tracks search performance, historical
trends, SEO opportunities, booking starts, and BookingKoala's native
`BookingByCustomer` confirmed-booking event.

Documentation:

-   `site-management/SEO_DASHBOARD_USER_GUIDE.md` - nontechnical
    business-owner guide: what the dashboard means, how to review it,
    and how to interpret each metric.
-   `site-management/SEO_DASHBOARD_OPERATIONS.md` - technical
    operations, automation, credentials, credential rotation,
    troubleshooting, privacy, and recovery.
-   `site-management/ANALYTICS_IMPLEMENTATION.md` - production
    GA4/Google tag and BookingKoala cross-domain implementation.
-   `site-management/CONVERSION_TRACKING.md` - event definitions and
    conversion-funnel semantics.
-   `site-management/GSC_AUDIT_TOOLS.md` - Search Console audit tooling.

Important distinction:

`booknow_click` means a booking was started. It is not a completed
booking.

`BookingByCustomer` is the native BookingKoala confirmed-booking event
used by the dashboard.

The scheduled dashboard refresh is maintained by
`.github/workflows/gsc-dashboard.yml` on the repository default branch
and updates the `seo-dashboard` deployment branch.

### Daily GSC query and page trend explorer

The SEO dashboard maintains real daily Google Search Console history
for interactive query and page analysis:

- `cloudflare-site/seo-dashboard/data/query-history.json`
- `cloudflare-site/seo-dashboard/data/page-history.json`

Tracked keywords, top queries, query winners/losers, and page
winners/losers can be expanded into daily historical charts.

Chart periods: `1D | 7D | 30D | 90D | 180D | 1Y | Custom`

Metrics: `Clicks | Impressions | Position | CTR`

SEO Event Log entries provide change context on historical charts;
temporal proximity does not establish causation.

`tools/gsc_dashboard.py` creates an initial 365-day backfill and then
refreshes a recent overlap window. The history files contain real GSC
observations; missing query observations are not interpolated. GSC can
omit anonymized or low-volume query rows, and average position is an
aggregate metric rather than a deterministic live SERP rank.

The Winners & Losers tables use a fixed responsive layout on desktop so
query/page text wraps at word boundaries while numeric columns remain
compact. Trend-chart Y-axis labels use adaptive precision for low-volume
integer metrics; fractional axis ticks are display scale labels only and
do not imply fractional clicks or impressions.

### Phase 11: SEO Action Workflow

Opportunity Intelligence now has persistent workflow state. Each generated opportunity receives a deterministic ID and moves through:

`New -> Investigating -> Implemented -> Measuring -> Closed`

State is stored separately in `cloudflare-site/seo-dashboard/data/opportunity-workflow.json`, so a daily analytics refresh does not erase human decisions. Run `python tools/opportunity_workflow.py sync` after regenerating Opportunity Intelligence.

Use `python tools/opportunity_workflow.py list` to review IDs. Change state with `python tools/opportunity_workflow.py status --id <ID> --status <STATE>`. When work has actually been implemented, record the implementation summary and create/link an SEO Event with `opportunity_workflow.py event`. SEO Event timing is measurement context and does not prove causation.

The dashboard's Open Analysis view combines the current recommendation, retained GSC query/page history when available, Organic Search conversion context, related SEO Events, workflow state, and the 30/60/90-day measurement plan. A missing retained query/page history match is not treated as zero search activity.

The dashboard is static and intentionally does not write workflow state from the browser. Repository state remains the auditable source of truth.
