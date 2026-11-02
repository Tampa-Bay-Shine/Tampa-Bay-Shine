#!/usr/bin/env python3
"""Tampa Bay Shine: focused contextual internal-link improvements."""

from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser
import argparse
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "cloudflare-site"
MARKER = "<!-- TBS_SEO_CONTEXT_LINKS_20261102 -->"

CHANGES = {
    "house-cleaning-ruskin-fl": {
        "heading": "Explore Cleaning Services Near Ruskin",
        "copy": (
            'Need cleaning elsewhere in SouthShore? Explore '
            '<a href="/house-cleaning-apollo-beach/">house cleaning in Apollo Beach</a> '
            'and <a href="/house-cleaning-sun-city-center-fl/">house cleaning in Sun City Center</a>. '
            'For a one-time or recurring cleaning in Ruskin, '
            '<a href="/book/">check online pricing and availability</a>.'
        ),
    },
    "house-cleaning-brandon-fl": {
        "heading": "More Cleaning Options for Brandon Homes",
        "copy": (
            'Need a more thorough cleaning? Explore our '
            '<a href="/deep-cleaning-services-tampa/">deep cleaning services</a>. '
            'Preparing for a move? Review '
            '<a href="/move-out-cleaning-tampa/">move-out cleaning</a>. '
            'We also provide '
            '<a href="/house-cleaning-riverview-fl/">house cleaning in Riverview</a>. '
            '<a href="/book/">Check pricing and availability online</a>.'
        ),
    },
    "office-cleaning-brandon": {
        "heading": "Related Commercial Cleaning Services",
        "copy": (
            'Managing more than an office? Explore '
            '<a href="/medical-office-cleaning-brandon/">medical office cleaning in Brandon</a>, '
            '<a href="/common-area-cleaning/">HOA and apartment common-area cleaning</a>, '
            'and <a href="/commercial-cleaning-tampa/">commercial cleaning services</a>. '
            '<a href="/contact-us/">Request a facility-specific cleaning estimate</a>.'
        ),
    },
    "common-area-cleaning": {
        "heading": "Resources for Property Managers",
        "copy": (
            'Explore our '
            '<a href="/property-management-cleaning-tampa/">property management cleaning services</a>, '
            '<a href="/office-cleaning-brandon/">Brandon office cleaning</a>, '
            'and <a href="/blog/hoa-common-area-cleaning-tampa-bay-guide/">'
            'HOA and common-area cleaning guide</a>. '
            '<a href="/contact-us/">Request a customized cleaning quote</a>.'
        ),
    },
}

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

def page_path(slug):
    return SITE / slug / "index.html"

def block(heading, copy):
    return (
        "\n" + MARKER + "\n"
        '<section class="tbs-resource-link" '
        'aria-label="Related cleaning services">\n'
        '  <div class="site-shell">\n'
        f'    <h2>{heading}</h2>\n'
        f'    <p>{copy}</p>\n'
        '  </div>\n'
        '</section>\n'
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    updates = []
    errors = []

    for slug, data in CHANGES.items():
        path = page_path(slug)
        if not path.is_file():
            errors.append(f"Missing source page: {path}")
            continue

        original = path.read_text(encoding="utf-8")

        if MARKER in original:
            print(f"SKIP: {slug} (already updated)")
            continue

        closing = original.lower().rfind("</main>")
        if closing < 0:
            errors.append(f"Missing </main>: {slug}")
            continue

        addition = block(data["heading"], data["copy"])

        links = LinkParser()
        links.feed(addition)

        for href in links.links:
            if not href.startswith("/"):
                continue

            target = SITE / href.strip("/") / "index.html"
            if not target.is_file():
                errors.append(f"{slug}: unresolved link {href}")

        revised = original[:closing] + addition + original[closing:]
        updates.append((slug, path, original, revised))

    if errors:
        for error in errors:
            print("ERROR:", error)
        print("No files changed.")
        return 1

    print(f"Pages ready for update: {len(updates)}")

    if not args.apply:
        for slug, *_ in updates:
            print("DRY RUN:", slug)
        print("Use --apply to write changes.")
        return 0

    if not updates:
        print("Nothing to change.")
        return 0

    backup = ROOT / "reports" / (
        "seo-link-backup-" +
        datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    backup.mkdir(parents=True, exist_ok=False)

    for slug, path, original, revised in updates:
        dest = backup / slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)

    try:
        for slug, path, original, revised in updates:
            path.write_text(revised, encoding="utf-8")
            print("UPDATED:", slug)
    except Exception as exc:
        for slug, path, original, revised in updates:
            path.write_text(original, encoding="utf-8")
        print("ERROR: Changes rolled back:", exc)
        return 1

    print("Backup:", backup)
    print("SUCCESS: Contextual internal links updated.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
