# Tampa Bay Shine SEO + AI Search Content Strategy

## Objective
Strengthen organic search visibility and AI-answer eligibility without creating doorway-style local pages or repeating generic FAQ content across the site.

## Content architecture
1. **Homepage** — brand/entity, primary residential/commercial proposition, pricing entry point, trust, service-area summary.
2. **Service hubs** — own broad service-definition, pricing, inclusions, comparisons and booking questions.
3. **Local service pages** — own local availability, access/logistics, property-type and service-scenario questions.
4. **Resource pages** — own informational intent: checklists, cost/time guides, turnover preparation and cleaning education.
5. **Commercial specialty pages** — own facility-specific scope, scheduling, COI/vendor onboarding, floor/window/common-area questions.

## FAQ policy
- Do not put the same company-wide policy questions on every local page.
- Broad recurring questions belong on the relevant hub page.
- Local pages should normally contain 4–7 intent-specific FAQs.
- Every visible FAQ must match FAQPage structured data exactly when FAQPage schema is present.
- FAQ schema is supplemental; the visible answer must be useful without schema.
- Avoid FAQs written only to insert keywords.

## AI-search positioning
Pages should state concise first-party facts in extractable language:
- what Tampa Bay Shine does;
- who the service is for;
- where service is available;
- meaningful starting prices where applicable;
- what is included/excluded;
- how booking or commercial walkthroughs work;
- insurance/COI/vendor facts where applicable;
- policies customers actually need to make a decision.

Prefer concrete, attributable company facts over generic cleaning-industry prose.

## Internal linking
Use a hub-and-spoke structure:
- House Cleaning -> Standard / Deep -> local house-cleaning pages
- Move-Out hub -> local move-out pages -> checklist -> cost/time guide
- Apartment hub -> local apartment pages -> apartment move-out
- Airbnb hub -> local Airbnb pages -> turnover checklist
- Commercial hub -> Office -> Medical -> Common Area -> Floors -> Windows
- Locations hub -> major local service pages

## Content quality safeguards
Run `tools/content_quality_audit.py` after content changes. Treat duplicate FAQ groups, FAQ/schema mismatches, orphan pages, thin content, duplicate metadata and canonical inconsistencies as release-review items.

## Next editorial phase
After FAQ differentiation, improve pages using real Search Console query/impression data:
- strengthen sections for queries already receiving impressions;
- add concise answer blocks where a page can directly satisfy a high-intent question;
- expand first-party examples and service process details;
- create new informational resources only when they fill a documented search-intent gap.
