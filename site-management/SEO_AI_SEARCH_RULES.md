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
