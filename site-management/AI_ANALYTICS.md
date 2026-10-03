# AI Analytics and Visibility

Phase 8 adds two separate measurement layers to the private SEO dashboard.

**AI referral analytics** uses GA4 acquisition data to identify measurable visits from AI assistants. It tracks 7-, 28-, and 90-day sessions, users, engagement, booking starts (`booknow_click`), intent actions, confirmed BookingKoala bookings (`BookingByCustomer`), platform/source breakdowns, and historical 28-day snapshots.

**AI answer visibility** is a separate controlled-prompt dataset for mentions and citations that may never produce a website visit. Do not combine answer visibility and GA4 referral traffic into a synthetic score.

## Classification
The initial conservative classifier recognizes clear source/referrer signals for ChatGPT/OpenAI, Perplexity, Claude, Microsoft Copilot, and Gemini. Ordinary Google Organic Search is not reclassified as AI merely because Google may show an AI-generated search feature. Ambiguous sources stay outside AI totals until verified.

## Generated data
- `cloudflare-site/seo-dashboard/data/ai.json`
- `cloudflare-site/seo-dashboard/data/ai-history.json`

Both are aggregate-only. Never publish PII, BookingKoala booking IDs, OAuth credentials, API keys, form contents, payment data, or private conversations.

## Run
```powershell
python.exe .\tools\ai_dashboard.py `
  --client-secret "$env:USERPROFILE\.tbs-gsc\client_secret.json" `
  --token "$env:USERPROFILE\.tbs-ga4\token.json" `
  --property "487638948"
```

The tool uses the existing GA4 read-only OAuth credential.

## Semantics
`booknow_click` is booking start/intent. Exact case-sensitive `BookingByCustomer` is the confirmed-booking signal. Never relabel Direct, Organic Search, Organic Social, or generic Referral conversions as AI without an identifiable AI acquisition source.

`ai-history.json` stores rolling 28-day snapshots. If source-classification rules materially change, document the change and regenerate history where feasible.

## Controlled AI-answer monitoring
Store fixed-prompt observations separately with fields such as date, provider/model family, stable prompt ID, service/category, geography, mentioned yes/no, cited yes/no, and cited Tampa Bay Shine URL. Missing test periods are missing data, not zero visibility. Record prompt/model/methodology changes in the SEO event log because they affect trend comparability.

## Workflow integration
After `ga4_dashboard.py`, run `tools/ai_dashboard.py` with the same GA4 credential and property. Add only `ai.json` and `ai-history.json` to the scheduled workflow safety allowlist and explicit `git add` list. Scheduled refreshes must never auto-commit code, HTML, documentation, credentials, or unrelated files.
