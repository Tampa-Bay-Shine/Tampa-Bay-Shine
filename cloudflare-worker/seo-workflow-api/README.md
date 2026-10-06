# One-click Opportunity Intelligence workflow

This Worker lets the static SEO dashboard safely update Opportunity Intelligence workflow state without exposing a GitHub token in browser JavaScript.

## Security model

- Dashboard origin allowed: `https://seo.tampabayshine.com`
- Worker custom domain: `https://seo-api.tampabayshine.com`
- Protect the Worker custom domain with Cloudflare Access.
- The Worker requires the `Cf-Access-Authenticated-User-Email` header and can restrict it to one email with `ALLOWED_EMAIL`.
- `GITHUB_TOKEN` exists only as a Worker secret.
- Never put the GitHub token in dashboard HTML/JavaScript.

## GitHub token

Create a fine-grained GitHub personal access token restricted to repository:

`Tampa-Bay-Shine/Tampa-Bay-Shine`

Repository permission required:

- Contents: Read and write

No other repository permission is needed by this Worker.

## Deploy

From `cloudflare-worker/seo-workflow-api`:

```powershell
npx wrangler login
npx wrangler secret put GITHUB_TOKEN
npx wrangler secret put ALLOWED_EMAIL
npx wrangler deploy
```

For `ALLOWED_EMAIL`, enter the email address you will use to authenticate to Cloudflare Access.

In Cloudflare Workers & Pages, open the `tbs-seo-workflow-api` Worker and add the custom domain:

`seo-api.tampabayshine.com`

## Cloudflare Access

In Cloudflare Zero Trust / Access, create a self-hosted application for:

`seo-api.tampabayshine.com/*`

Create an Allow policy containing only the email address you want to use for dashboard workflow changes. Keep the application protected. The Worker intentionally rejects mutation requests that did not pass through Access.

## Dashboard behavior

- New → Start Investigation
- Investigating → Mark Implemented
- Implemented → Start Measuring
- Measuring → Close Opportunity

Implemented requires an SEO Event category and implementation summary. The Worker commits `opportunity-workflow.json` and `events.json` together in one Git commit.

Closed requires a measurement-outcome note.

The dashboard updates immediately after a successful API response and then reloads after the repository/deployment has time to refresh.
