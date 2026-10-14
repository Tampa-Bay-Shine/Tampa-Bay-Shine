#!/usr/bin/env python3
"""Tampa Bay Shine v26.0 conversion architecture implementation."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO = Path(".").resolve()
SITE = REPO / "cloudflare-site"
REPORTS = REPO / "reports"
BACKUP = REPORTS / "v26_conversion_backup"

MARKER_RES = "<!-- TBS_V26_RESIDENTIAL_CTA -->"
MARKER_COM = "<!-- TBS_V26_COMMERCIAL_CTA -->"
MARKER_LINK = "<!-- TBS_V26_CONTEXT_LINK -->"


# High-intent residential pages where online quoting/booking
# and current offers are directly relevant.
RESIDENTIAL = [
    "standard-cleaning-services-tampa",
    "deep-cleaning-services-tampa",
    "deep-move-in-move-out-cleaning",
    "move-out-cleaning-tampa-1",
    "move-out-cleaning-tampa",
    "apartment-cleaning-services",
    "airbnb-cleaning-services",
    "house-cleaning-tampa",
    "house-cleaning-south-tampa",
    "house-cleaning-downtown-tampa",
    "house-cleaning-brandon-fl",
    "house-cleaning-riverview-fl",
    "house-cleaning-apollo-beach-fl",
    "house-cleaning-wesley-chapel",
    "house-cleaning-ruskin-fl",
    "house-cleaning-sun-city-center-fl",
]

# Commercial pages use the commercial lead path, not residential booking.
COMMERCIAL = [
    "office-cleaning",
    "commercial-cleaning-tampa",
    "medical-office-cleaning-tampa",
    "medical-office-cleaning-brandon",
    "medical-office-cleaning-wesley-chapel",
    "common-area-cleaning",
    "property-management-cleaning-tampa",
    "gym-cleaning",
    "post-event-cleaning",
    "post-construction-cleaning",
    "floor-cleaning",
    "floor-stripping-waxing",
    "office-cleaning-south-tampa",
    "office-cleaning-brandon",
    "office-cleaning-riverview",
]

RESIDENTIAL_CTA = f"""
{MARKER_RES}
<section class="tbs-v26-conversion" aria-label="Online cleaning quote and booking">
  <div class="site-shell tbs-v26-conversion-inner">
    <div class="tbs-v26-conversion-copy">
      <span class="tbs-v26-eyebrow">Easy Online Scheduling</span>
      <h2>Get a Quote &amp; Book Online 24/7</h2>
      <p>See your cleaning price and available options online whenever it is convenient for you. Online quotes and booking are available 24/7; cleaning appointments are scheduled based on service availability.</p>
      <p class="tbs-v26-trust"><strong>Local Tampa Bay cleaning company</strong> &bull; Licensed &amp; insured</p>
    </div>
    <div class="tbs-v26-actions">
      <a class="tbs-v26-primary" href="/booknow">Check Pricing &amp; Availability</a>
      <a class="tbs-v26-secondary" href="/coupons/">View Current Offers</a>
    </div>
  </div>
</section>
"""

COMMERCIAL_CTA = f"""
{MARKER_COM}
<section class="tbs-v26-conversion tbs-v26-commercial" aria-label="Commercial cleaning quote">
  <div class="site-shell tbs-v26-conversion-inner">
    <div class="tbs-v26-conversion-copy">
      <span class="tbs-v26-eyebrow">Commercial Cleaning</span>
      <h2>Request a Commercial Cleaning Quote</h2>
      <p>Tell us about your facility, cleaning priorities, access requirements and preferred schedule. Tampa Bay Shine can help build a cleaning scope around your property and operating needs.</p>
      <p class="tbs-v26-trust"><strong>Local Tampa Bay cleaning company</strong> &bull; Licensed &amp; insured &bull; COI available on request</p>
    </div>
    <div class="tbs-v26-actions">
      <a class="tbs-v26-primary" href="/contact-us/">Request a Commercial Quote</a>
      <a class="tbs-v26-secondary" href="tel:+17273511779">Call 727.351.1779</a>
    </div>
  </div>
</section>
"""

CSS = """

/* v26.0 - conversion architecture */
.tbs-v26-conversion{
  margin:36px 0 0;
  padding:30px 0;
  background:#f7f9ff;
  border-top:1px solid #dfe5f3;
  border-bottom:1px solid #dfe5f3;
}
.tbs-v26-conversion-inner{
  display:grid;
  grid-template-columns:minmax(0,1fr) auto;
  gap:28px;
  align-items:center;
}
.tbs-v26-conversion-copy{
  min-width:0;
}
.tbs-v26-eyebrow{
  display:inline-block;
  margin-bottom:6px;
  color:#001c7d;
  font-size:.78rem;
  font-weight:900;
  letter-spacing:.06em;
  text-transform:uppercase;
}
.tbs-v26-conversion h2{
  margin:0 0 8px;
  color:#111827;
  font-size:clamp(1.35rem,2.5vw,1.8rem);
}
.tbs-v26-conversion p{
  margin:0;
  max-width:850px;
  color:#374151;
  line-height:1.65;
}
.tbs-v26-conversion .tbs-v26-trust{
  margin-top:9px;
  font-size:.92rem;
}
.tbs-v26-actions{
  display:flex;
  flex-direction:column;
  gap:10px;
  min-width:245px;
}
.tbs-v26-primary,
.tbs-v26-secondary{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:46px;
  padding:11px 18px;
  border-radius:10px;
  font-weight:900;
  text-align:center;
  text-decoration:none;
}
.tbs-v26-primary,
.tbs-v26-primary:link,
.tbs-v26-primary:visited{
  background:#001c7d;
  color:#fff;
}
.tbs-v26-primary:hover,
.tbs-v26-primary:focus{
  background:#0f0889;
  color:#fff;
}
.tbs-v26-secondary,
.tbs-v26-secondary:link,
.tbs-v26-secondary:visited{
  background:#fff;
  color:#001c7d;
  border:1px solid #001c7d;
}
.tbs-v26-secondary:hover,
.tbs-v26-secondary:focus{
  background:#eef2ff;
  color:#001c7d;
}
.tbs-v26-commercial{
  background:#f8fafc;
}
@media(max-width:760px){
  .tbs-v26-conversion-inner{
    grid-template-columns:1fr;
  }
  .tbs-v26-actions{
    min-width:0;
  }
}
"""


CONTEXT_LINKS = {
    # Transactional -> informational reinforcement
    "standard-cleaning-services-tampa": (
        "/blog/house-cleaning-cost-tampa-guide/",
        "House Cleaning Cost in Tampa",
        "Planning your budget? See the factors that affect house-cleaning pricing in our Tampa cost guide."
    ),
    "deep-cleaning-services-tampa": (
        "/blog/standard-vs-deep-cleaning-tampa/",
        "Standard vs. Deep Cleaning in Tampa",
        "Not sure which service fits your home? Compare standard and deep cleaning before choosing."
    ),
    "airbnb-cleaning-services": (
        "/blog/airbnb-turnover-cleaning-tampa-bay-guide/",
        "Airbnb Turnover Cleaning Guide",
        "Hosts can review our Tampa Bay turnover-cleaning planning guide for scheduling, scope and guest-ready considerations."
    ),
    "window-cleaning": (
        "/blog/window-cleaning-tampa-guide/",
        "Window Cleaning in Tampa Guide",
        "Review what to consider for interior glass, reachable exterior glass, screens, tracks and sills."
    ),
    "common-area-cleaning": (
        "/blog/hoa-common-area-cleaning-tampa-bay-guide/",
        "HOA & Common-Area Cleaning Guide",
        "HOAs and property managers can review our Tampa Bay guide to planning common-area cleaning."
    ),
    "property-management-cleaning-tampa": (
        "/blog/hoa-common-area-cleaning-tampa-bay-guide/",
        "HOA & Common-Area Cleaning Guide",
        "Planning recurring service for shared spaces? Review our HOA and common-area cleaning guide."
    ),
    "medical-office-cleaning-tampa": (
        "/blog/medical-office-cleaning-tampa-guide/",
        "Medical Office Cleaning Guide",
        "Review planning considerations for professional medical-office cleaning in Tampa."
    ),
    "office-cleaning": (
        "/blog/office-cleaning-frequency-tampa/",
        "Office Cleaning Frequency Guide",
        "Not sure how often your office should be cleaned? Review our Tampa office-cleaning frequency guide."
    ),
    "house-cleaning-wesley-chapel": (
        "/blog/house-cleaning-wesley-chapel-guide/",
        "Wesley Chapel House Cleaning Guide",
        "See our local guide to planning professional house cleaning in Wesley Chapel."
    ),
    "realtor-partners": (
        "/blog/pre-listing-cleaning-guide-tampa-realtors/",
        "Pre-Listing Cleaning Guide",
        "Realtors and sellers can review our practical Tampa pre-listing cleaning guide."
    ),
}


def page(slug):
    return SITE / slug / "index.html"


def backup(path):
    rel = path.relative_to(REPO)
    target = BACKUP / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(path, target)


def inject_before_main_end(path, block, marker):
    if not path.exists():
        return "missing"

    text = path.read_text(encoding="utf-8")

    if marker in text:
        return "already-present"

    pos = text.lower().rfind("</main>")

    if pos < 0:
        return "no-main"

    backup(path)

    text = text[:pos] + block + text[pos:]
    path.write_text(text, encoding="utf-8")

    return "changed"


def add_context_link(slug, href, title, description):
    path = page(slug)

    if not path.exists():
        return "missing"

    text = path.read_text(encoding="utf-8")

    if href in text:
        return "already-linked"

    pos = text.lower().rfind("</main>")

    if pos < 0:
        return "no-main"

    block = f"""
{MARKER_LINK}
<section class="tbs-resource-link">
  <div class="site-shell">
    <strong>Helpful Cleaning Guide:</strong>
    <a href="{href}">{title}</a>
    <p>{description}</p>
  </div>
</section>
"""

    backup(path)

    text = text[:pos] + block + text[pos:]
    path.write_text(text, encoding="utf-8")

    return "changed"


def main():
    BACKUP.mkdir(parents=True, exist_ok=True)

    report = {
        "residential": {},
        "commercial": {},
        "context_links": {},
        "css": None,
    }

    for slug in RESIDENTIAL:
        report["residential"][slug] = inject_before_main_end(
            page(slug),
            RESIDENTIAL_CTA,
            MARKER_RES,
        )

    for slug in COMMERCIAL:
        report["commercial"][slug] = inject_before_main_end(
            page(slug),
            COMMERCIAL_CTA,
            MARKER_COM,
        )

    for slug, data in CONTEXT_LINKS.items():
        report["context_links"][slug] = add_context_link(
            slug,
            *data,
        )

    css_path = SITE / "assets/css/main.css"

    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")

        if "/* v26.0 - conversion architecture */" not in css_text:
            backup(css_path)
            css_path.write_text(
                css_text.rstrip() + CSS + "\n",
                encoding="utf-8",
            )
            report["css"] = "changed"
        else:
            report["css"] = "already-present"
    else:
        report["css"] = "missing"

    report_path = REPORTS / "v26_conversion_changes.json"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("TAMPA BAY SHINE v26.0 CONVERSION ARCHITECTURE")
    print("=" * 54)

    for group in ("residential", "commercial", "context_links"):
        changed = sum(
            value == "changed"
            for value in report[group].values()
        )

        print(
            f"{group}: {changed} changed / "
            f"{len(report[group])} targeted"
        )

        for slug, status in report[group].items():
            print(f"  {status:15} {slug}")

    print(f"css: {report['css']}")
    print()
    print(f"Report: {report_path}")
    print(f"Backup: {BACKUP}")


if __name__ == "__main__":
    main()
