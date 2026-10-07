# Competitor Intelligence and Authority Data

## Purpose
This is the operating guide for the Tampa Bay Shine SEO Dashboard Competitors tab.

The system answers three separate questions:
1. Which domains occupy the organic Top 10 for tracked searches?
2. Which cleaning companies are relevant competitors for each query intent?
3. Do observed authority/link-profile differences help explain persistent ranking gaps?

Third-party authority scores are not Google ranking metrics.

## Data sources
SERP observations are stored in `cloudflare-site/seo-dashboard/data/competitor-rankings.json`. They are human-browser organic-result observations; Google Maps/Local Pack is not included and anti-bot/CAPTCHA controls must not be bypassed.

Authority data is stored in `cloudflare-site/seo-dashboard/data/competitor-authority.json` and is imported from `site-management/competitor-authority-template.csv`.

Supported fields: `moz_da`, `ahrefs_dr`, `semrush_authority`, `referring_domains`, `backlinks`, `organic_keywords`, `organic_traffic`, `source`, `observed_at`, and `notes`. Missing values remain null.

## Competitor taxonomy
The dashboard separates:
- Residential/local cleaning
- Commercial/facility cleaning
- Directories/marketplaces/social
- Irrelevant/adjacent results

The Keyword Battle Board shows both the top organic result and the top relevant competitor for query intent.

## Authority watchlists
The authority template contains Tampa Bay Shine plus the current top 10 residential/local and top 10 commercial/facility competitors from observed SERPs. Do not collect authority metrics for every domain ever seen.

## Collection procedure
1. Open `site-management/competitor-authority-template.csv`.
2. Use free/available Moz, Ahrefs, and/or Semrush checks.
3. Record only values actually shown.
4. Record the tool/source name and observation date when practical.
5. Leave unavailable metrics blank.
6. Never substitute DA, DR, or Authority Score for one another.

Import and rebuild:
```powershell
python.exe .\tools\competitor_authority_import.py
python.exe .\tools\competitor_intelligence.py
```

Validate:
```powershell
python.exe .\tools\validate_site.py .\cloudflare-site
python.exe .\tools\seo_regression.py .
python.exe .\tools\analytics_regression.py
git diff --check
```

## Interpretation
Moz Domain Authority, Ahrefs Domain Rating, and Semrush Authority Score are vendor-specific comparative metrics. They are not Google metrics and use different methodologies.

Use them as supporting evidence:
- Competitor outranks TBS with similar/weaker authority: inspect relevance, local intent, page structure, internal links, title/snippet, content depth, citations, and SERP fit.
- Competitor outranks TBS with a materially stronger referring-domain profile: authority/link acquisition may be part of the gap.
- One vendor score differs but the rest of the evidence does not: do not overreact.
- Low-volume or unstable SERP: wait for repeated observations.

Authority data must not override stabilization/HOLD logic for recently changed pages.

<!-- v20.6.1 authority-baseline -->
## Free-data operating mode

As of 2026-10-07, the free-tool workflow produced a reliable Tampa Bay Shine baseline but did not provide consistent competitor authority metrics without paid access.

The dashboard therefore stores Tampa Bay Shine's observed baseline, leaves competitor authority metrics null, does not treat missing competitor data as zero, and continues to use the manually captured organic SERP dataset as the primary competitive-analysis source.

Current Tampa Bay Shine baseline:
- Moz DA 13
- Semrush Authority Score 6
- Semrush referring domains 362
- Semrush backlinks 1.1K
- Semrush organic keywords 56
- Semrush organic traffic 6

Moz also reported 190 Linking Root Domains, 22 Ranking Keywords, 13% Spam Score, and homepage PA 32. These are retained as notes rather than substituted into Semrush fields.

## Publishing
After importing authority values and rebuilding intelligence:
```powershell
git add cloudflare-site/seo-dashboard/data/competitor-authority.json
git add cloudflare-site/seo-dashboard/data/competitor-intelligence.json
git add site-management/competitor-authority-template.csv
git commit -m "Refresh competitor authority observations"
git push origin seo-dashboard
```

SERP capture weekly is sufficient during active SEO work. Authority metrics monthly is generally sufficient.
