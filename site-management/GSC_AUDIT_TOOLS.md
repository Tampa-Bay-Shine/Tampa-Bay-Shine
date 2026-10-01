# Google Search Console Audit Tools

This repository includes two read-only Google Search Console utilities used to separate indexing/crawl diagnostics from performance-driven SEO decisions.

## Why these tools were built

During the Cloudflare Pages migration, the Search Console interface did not always make it obvious when Google had last crawled an individual URL. A site-wide URL Inspection audit was needed to answer a concrete question: **has Google actually seen the new Cloudflare version of each page?**

After the crawl/indexing state was verified, the next need was different: choose local and service-page SEO work from **real query/page performance**, not from guessed keywords. The performance audit was built to compare periods and surface pages already receiving impressions in positions where targeted improvements may be useful.

The two tools intentionally solve different problems:

- `gsc_index_audit.py` = crawl/index status and canonical diagnostics.
- `gsc_performance_audit.py` = query/page performance and optimization prioritization.

Neither tool changes Search Console, requests indexing, modifies the website, or changes analytics tags.

## Shared authentication

Both tools use the Search Console read-only OAuth scope:

```text
https://www.googleapis.com/auth/webmasters.readonly
```

The expected local credential files are:

```text
%USERPROFILE%\.tbs-gsc\client_secret.json
%USERPROFILE%\.tbs-gsc\token.json
```

These files must stay outside the repository and must not be committed.

Required Python packages:

```powershell
python.exe -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

The Google account used for OAuth must have access to the Search Console property.

## Index audit

Run:

```powershell
python.exe .\tools\gsc_index_audit.py
```

The script reads `cloudflare-site/sitemap.xml` and inspects every URL through the Search Console URL Inspection API.

Useful fields include:

```text
verdict
coverage_state
indexing_state
robots_txt_state
page_fetch_state
last_crawl_time_utc
user_canonical
google_canonical
canonical_match
status
```

Important classifications include:

```text
INDEXED_FRESH
INDEXED_STALE
UNKNOWN_TO_GOOGLE
DISCOVERED_NOT_CRAWLED
CRAWLED_NOT_INDEXED
ALTERNATE_CANONICAL
DUPLICATE_CANONICAL
BLOCKED_NOINDEX_META
BLOCKED_NOINDEX_HEADER
BLOCKED_BY_ROBOTS
CANONICAL_MISMATCH
```

`INDEXING_STATE_UNSPECIFIED` must not be interpreted as an indexing block by itself.

Use a deployment date as the freshness baseline when checking whether Google has recrawled after a release:

```powershell
python.exe .\tools\gsc_index_audit.py --baseline 2026-09-28
```

Output:

```text
reports\gsc-index-audit\
```

The URL Inspection API returns Google's indexed-version information. It does not perform the same live fetch as the Search Console **Test Live URL** function.

## Performance audit

Run the default 90-day comparison:

```powershell
python.exe .\tools\gsc_performance_audit.py
```

By default the script ends the period three days before the run date to reduce reliance on the freshest potentially incomplete Search Console data.

Useful options:

```powershell
python.exe .\tools\gsc_performance_audit.py --days 28
python.exe .\tools\gsc_performance_audit.py --end-date 2026-09-28
python.exe .\tools\gsc_performance_audit.py --include-branded
```

Output:

```text
reports\gsc-performance\
```

Key files:

```text
pages-current.csv
queries-current.csv
query-page-current.csv
pages-comparison.csv
queries-comparison.csv
query-page-comparison.csv
opportunities.csv
page-opportunities.csv
cannibalization-review.csv
summary.json
summary.txt
```

The opportunity report flags query/page pairs such as:

```text
PAGE_ONE_LOW_CTR
NEAR_PAGE_ONE
STRIKING_DISTANCE
HIGH_IMPRESSIONS_LOW_CTR
```

The generated `opportunity_score` is only a repository-local prioritization heuristic. It is not a Google score, ranking factor, or prediction.

## Recommended workflow

1. After a significant production migration or SEO release, run `gsc_index_audit.py`.
2. Confirm important URLs are crawlable, canonicalized correctly, and being recrawled.
3. Use `gsc_performance_audit.py` to identify pages already receiving measurable search demand.
4. Prefer a small batch of 5-10 targeted pages rather than mass rewriting the site.
5. Validate, push staging, visually inspect, and promote through the normal release workflow.
6. Re-run the index audit after Google recrawls.
7. Re-run the performance audit after enough new Search Console data accumulates to evaluate the release.

Do not interpret a successful crawl as proof that a content change improved rankings, and do not interpret a short-term ranking movement as causal without enough post-release data.
