# SEO and AI Search Rules

## Core principle
Important content, headings, links and structured data must be present in server-delivered static HTML.

## On-page SEO
For every indexable page:
- one descriptive visible H1
- unique useful title
- useful meta description
- self-referencing canonical
- index,follow unless deliberately noindexed
- useful internal links
- meaningful image alt text
- descriptive anchor text
- no thin doorway/location pages
- visible FAQ content must match FAQ schema

## Structured data
Stable entity IDs:
- https://tampabayshine.com/#organization
- https://tampabayshine.com/#website
- /slug#webpage
- /slug#service
- /slug#faq
- /slug#breadcrumb

Keep Organization identity consistent:
- Tampa Bay Shine
- Tampa Bay Shine, LLC
- +1-727-351-1779
- sales@tampabayshine.com
- founded 2025

Do not publish a storefront address. Only use schema supported by visible content.

## Sitemap and robots
robots.txt must include:
Sitemap: https://tampabayshine.com/sitemap.xml

Keep sitemap.xml limited to canonical indexable HTTP-200 pages. Use <lastmod> when a page changes materially.

## IndexNow / Bing
Keep root file:
3631fda1114542beac8b749d5ed827ad.txt

Contents:
3631fda1114542beac8b749d5ed827ad

After Cloudflare becomes authoritative, enable Cloudflare Crawler Hints. Cloudflare documents that Crawler Hints uses IndexNow signals when content is likely to have changed.

## AI search readiness
Use static crawlable HTML, strong headings, stable business entities, internal links, complete sitemap, structured data, fast pages and consistent service/location relationships. Do not block legitimate search crawlers unless intentionally required.

An optional /llms.txt is maintained as a machine-readable site guide. Treat it as experimental and not a guaranteed ranking/indexing signal.

## Cloudflare AI Search
Cloudflare AI Search is separate from public search ranking. If enabled for this website, use the website data source with sitemap parsing because this site publishes a complete sitemap. Keep sitemap <lastmod> current so changes can be recrawled efficiently.

## Content quality
Prefer useful service details, scope, pricing context, process, FAQs, service-area context and original business information over repetitive keyword text. Do not add unsupported cities, services, reviews, prices, guarantees or credentials.

## Regression testing
After material update batches:
1. validate source HTML
2. crawl internal links
3. validate JSON-LD
4. refresh sitemap
5. check important URLs in Google Search Console and Bing Webmaster Tools
6. rerun the existing AI-search benchmark periodically

## IndexNow release procedure

Hosting the root key file proves ownership, but does not itself notify search engines of changed URLs.

Dry validation:

```powershell
python.exe .\tools\submit_indexnow.py --repo .
```

After production is deployed and verified, submit the live production sitemap:

```powershell
python.exe .\tools\submit_indexnow.py --repo . --live
```

The tool verifies the live key file, fetches the live sitemap, submits canonical production URLs to IndexNow, and stores a report under `reports/`. Use repeated `--url` arguments for a small set of changed URLs already present in the sitemap.

Cloudflare Crawler Hints may also send IndexNow signals when enabled. The explicit tool provides a deterministic release-time submission and HTTP-status record.

IndexNow does not replace Google Search Console. Keep the sitemap submitted to Google and use URL Inspection / Request Indexing for a small number of high-priority URLs when appropriate.

## Homepage and template regression rules
For important landing pages and shared templates:
- keep titles concise; use 60 characters as a practical review threshold, not a ranking rule
- keep meta descriptions concise enough to avoid obvious SERP truncation
- provide Open Graph image metadata and a Twitter/X card for intentional social sharing
- preload the actual above-the-fold LCP image when it is stable and known
- keep heading levels sequential; do not use heading tags merely for visual styling
- provide a keyboard-accessible skip-to-content link on primary templates
- retain HSTS, X-Frame-Options, Permissions-Policy, and the conservative CSP in `_headers`
- do not chase keyword-density or text-to-HTML percentages as ranking targets; prioritize natural, useful copy
- treat author/date/editorial-policy warnings in generic audit tools contextually; they are appropriate for editorial content, not automatically for service homepages
- do not publish the service-area business address merely to satisfy an audit score
- do not add social-share widgets solely to satisfy an automated audit
- `@id`-only JSON-LD references are valid graph references and do not need a redundant `@type` solely to appease generic checkers
- Cloudflare compression/HTTP3 should be verified from live response headers rather than inferred from a third-party audit warning

Run:
`python.exe .\tools\seo_regression.py .`
after homepage/template SEO changes.


## Priority landing-page standard
Priority commercial-intent pages should preserve a production canonical, unique title and meta description, one H1, a factual answer-ready summary near the top, Open Graph image metadata, a Twitter/X card, stable hero-image preload, clear CTA hierarchy, contextual internal links, and current `dateModified`/sitemap `lastmod` after material changes.

Run `python.exe .\tools\seo_regression.py .` after changing a priority page.

## Conversion measurement
Shared JavaScript emits first-party CTA events and pushes them to `window.dataLayer` only when a data layer exists. Do not claim GA4/GTM or completed BookingKoala conversion measurement until explicitly configured and tested.

## Pre-indexing enhancement set

Priority landing pages currently use:
- static server-delivered primary content;
- unique title and meta description;
- production canonical;
- Open Graph image/title/description;
- Twitter/X large-image card;
- preload of the actual rendered above-the-fold hero image when present;
- concise visible Quick Answer blocks near the top;
- residential vs. commercial CTA hierarchy;
- contextual internal links;
- factual Organization / WebPage / Service / FAQ graph relationships;
- material-change `dateModified` synchronization;
- sitemap `lastmod` synchronization;
- targeted IndexNow submission after verified production changes;
- `tools/seo_regression.py` checks across the homepage plus priority landing pages.

The Standard Cleaning page is intentionally text/card-first and does not preload a non-rendered hero image.

Do not add image preloads solely to satisfy an audit when the image is not rendered above the fold.

The shared Quick Answer component uses explicit component-level button colors to protect contrast from older page-specific link styles.
