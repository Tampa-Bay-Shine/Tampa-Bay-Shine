# Tampa Bay Shine — 90-Day SEO, AI Visibility & Conversion Plan

## Objective
Grow qualified organic, local, AI-assisted, voice-search, and paid-search visibility while improving the percentage of visitors who become booked residential customers or qualified commercial leads. The primary KPI is qualified conversions, not raw traffic.

## Core KPIs
Residential: organic booking starts, Book Now clicks, completed bookings once BookingKoala cross-domain measurement is configured, conversion rate by landing page, and paid-search cost per booking.

Commercial: walkthrough/quote starts, contact submissions, phone clicks, qualified leads, and cost per qualified lead.

Search: indexed canonical URLs, impressions, clicks, CTR, average position, positions 8–20 opportunities, and cases where the wrong page ranks.

AI/search assistants: Tampa Bay Shine mentions, official-domain citations, pages cited, query families producing citations, and competitors appearing alongside Tampa Bay Shine.

## Days 0–7
Strengthen `/`, `/standard-cleaning-services-tampa`, `/deep-cleaning-services-tampa`, `/move-out-cleaning-tampa`, `/move-out-cleaning-tampa-1`, `/office-cleaning`, `/commercial-cleaning-tampa`, and `/locations`.

Standardize social metadata, stable hero-image preload, server-rendered answer summaries, CTA hierarchy, `dateModified`, sitemap `lastmod`, and conversion event hooks.

Preserve query ownership: `/move-out-cleaning-tampa` owns Tampa city transactional intent; `/move-out-cleaning-tampa-1` remains the regional Tampa Bay hub. Do not create duplicate doorway pages for minor keyword variations.

## Days 8–30
Keep Google Business Profile services, hours, service areas, offers, photos, and Q&A current. Publish 1–2 useful posts per week. Request reviews only from genuine completed customers and never incentivize the rating or content.

Test tightly scoped paid search around high-intent queries and send each ad group to its relevant landing page.

Pursue legitimate local mentions/links from Realtors, property managers, apartment communities, HOAs, moving companies, business organizations, vendor directories, and commercial partners. Avoid purchased links, fake traffic, fake reviews, click farms, and mass low-quality directory campaigns.

## Days 31–60
Use Search Console data. Prioritize pages with rising impressions and low CTR, queries ranking positions 8–20, high-intent searches where the wrong page ranks, and pages producing real booking or lead actions.

Improve existing pages before creating new ones: stronger answer blocks, clearer pricing/scope, better internal links, FAQs based on real questions, and stronger CTA placement.

## Days 61–90
Compare conversion rates by landing page and service. Refine CTA copy/placement. Keep concise factual answers in initial HTML, maintain consistent schema, and rerun the AI-search benchmark.

## Query ownership
| Query family | Primary page |
|---|---|
| house cleaning Tampa | `/standard-cleaning-services-tampa` |
| recurring cleaning Tampa | `/standard-cleaning-services-tampa` |
| maid service Tampa | `/standard-cleaning-services-tampa` |
| deep cleaning Tampa | `/deep-cleaning-services-tampa` |
| move out cleaning Tampa | `/move-out-cleaning-tampa` |
| move out cleaning Tampa Bay / service areas | `/move-out-cleaning-tampa-1` |
| office cleaning Tampa Bay | `/office-cleaning` |
| commercial cleaning Tampa | `/commercial-cleaning-tampa` |
| cleaning company Tampa Bay | `/` |
| cleaning service areas Tampa Bay | `/locations` |

## Measurement
Shared site JavaScript should emit `booknow_click`, `phone_click`, `contact_click`, `commercial_quote_start`, `coupon_click`, and `review_click`. These are analytics-ready hooks only. Completed BookingKoala transaction measurement requires separate cross-domain/conversion configuration.

## Release discipline
For material updates: validate locally, commit, run staging gate, push `cloudflare-staging`, QA staging, promote with `tools/promote_cloudflare.py --push`, run post-cutover, notify IndexNow for changed canonical URLs, and use Google Search Console URL Inspection selectively.

## Measurement implementation status

The site now has first-party CTA event instrumentation for `booknow_click`, `phone_click`, `contact_click`, `commercial_quote_start`, `coupon_click`, and `review_click`.

These events are emitted in the browser and are pushed to `window.dataLayer` when a data layer exists.

Current status:
- event-generation layer: implemented;
- GA4/GTM collection: must be verified/configured separately;
- BookingKoala `booking_start` / `booking_complete`: not measured by this marketing-site instrumentation;
- revenue attribution: requires transactional/cross-domain measurement.

See `site-management/CONVERSION_TRACKING.md`.
