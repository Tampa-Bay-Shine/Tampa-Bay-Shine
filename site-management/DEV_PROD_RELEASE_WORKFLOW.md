
# Dev / Production release workflow

Use two Cloudflare Pages projects and two Git branches.

Development:
- Pages project: `tampa-bay-shine-staging`
- Branch: `cloudflare-staging`
- URL: `https://tampa-bay-shine-staging.pages.dev`
- Global `X-Robots-Tag: noindex`
- Normal pushes deploy only to development.

Production:
- Pages project: `tampa-bay-shine`
- Branch: `cloudflare-production`
- Custom domain: `https://tampabayshine.com`
- No global noindex.
- BK routes point to `https://booking.tampabayshine.com`.

Cloudflare production project settings:
- Repository: `Tampa-Bay-Shine/Tampa-Bay-Shine`
- Production branch: `cloudflare-production`
- Framework: None
- Build command: `exit 0`
- Build output: `cloudflare-site`

Keep the existing staging project connected to `cloudflare-staging`.

## Gate

From the repo:

    python.exe .\tools\migration_gate.py --repo . --phase staging

GREEN means all automatic checks and recorded manual BK checks pass.
YELLOW means automatic checks passed but a manual operational gate is still pending.
RED means do not cut over.

Manual gates are in:

    site-management\release_gate_manual.json

Only change a value to `true` after the test was actually performed.

## Promotion

Prepare production locally, but do not push:

    python.exe .\tools\promote_cloudflare.py --repo .

When ready to release:

    python.exe .\tools\promote_cloudflare.py --repo . --push

The promotion script takes the exact tracked state of `cloudflare-staging`, creates/updates
`cloudflare-production`, removes the staging-only global noindex header, rewrites BK transaction
routes to `booking.tampabayshine.com`, commits, runs the production gate, and pushes only when
`--push` was requested and the gate is GREEN.

After launch:

    python.exe .\tools\migration_gate.py --repo . --phase post-cutover

## Normal development after launch

    git switch cloudflare-staging
    git pull origin cloudflare-staging

Edit, validate, commit, and push. The staging Pages project updates. Production does not.

Production changes only when the release script promotes an approved staging state to
`cloudflare-production` and pushes that branch.
