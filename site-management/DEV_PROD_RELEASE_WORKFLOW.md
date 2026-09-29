# Development and Production Release Workflow

The root `README.md` is the primary operational runbook.

## Environments

Staging:
- branch `cloudflare-staging`
- project `tampa-bay-shine-staging`
- URL https://tampa-bay-shine-staging.pages.dev
- global noindex required

Production:
- branch `cloudflare-production`
- project `tampa-bay-shine`
- URL https://tampabayshine.com

## Standard release

```powershell
git switch cloudflare-staging
git pull origin cloudflare-staging

python.exe .\tools\validate_site.py .\cloudflare-site
python.exe .\tools\service_area_audit.py --repo .
git diff --check

# update lastmod if appropriate
python.exe .\tools\update_sitemap.py .\cloudflare-site /slug

git add .
git commit -m "Describe the change"

python.exe .\tools\migration_gate.py --repo . --phase staging
git push origin cloudflare-staging
```

Wait for and QA staging, then:

```powershell
python.exe .\tools\promote_cloudflare.py --repo . --push
```

After production deploys:

```powershell
python.exe .\tools\migration_gate.py --repo . --phase post-cutover
```

## Critical detail

`promote_cloudflare.py` promotes `origin/cloudflare-staging`. Push staging before promotion.

## Dry production preparation

```powershell
python.exe .\tools\promote_cloudflare.py --repo .
```

This prepares production locally but does not push it.

## Transaction mode

Current fallback target:

```text
https://tampabayshine.bookingkoala.com
```

Future custom target:

```text
https://booking.tampabayshine.com
```

Only switch after the custom host is healthy and BookingKoala manual gates are retested:

```powershell
python.exe .\tools\set_transaction_mode.py custom --repo .
```

To restore fallback:

```powershell
python.exe .\tools\set_transaction_mode.py fallback --repo .
```

Commit/push the config change on staging and promote normally.

## Never

- develop directly on `cloudflare-production`
- remove staging noindex
- manually copy only part of staging into production
- promote an unpushed staging commit
- switch BookingKoala mode solely because DNS resolves
