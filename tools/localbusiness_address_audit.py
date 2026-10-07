#!/usr/bin/env python3
"""Audit Tampa Bay Shine LocalBusiness JSON-LD for required address data."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ORG_START = '{"name":"Tampa Bay Shine","legalName":"Tampa Bay Shine, LLC"'
ORG_ID = '"@id":"https://tampabayshine.com/#organization"'

SCRIPT_RE = re.compile(
    r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)

REQUIRED = (
    '"@type":"PostalAddress"',
    '"streetAddress":',
    '"addressLocality":',
    '"addressRegion":',
    '"postalCode":',
    '"addressCountry":',
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    site = repo / "cloudflare-site"

    if not site.is_dir():
        print(f"ERROR: missing {site}", file=sys.stderr)
        return 2

    total = 0
    good = 0
    failures = []

    for path in sorted(site.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        for m in SCRIPT_RE.finditer(text):
            body = m.group(1)
            pos = 0
            while True:
                start = body.find(ORG_START, pos)
                if start < 0:
                    break
                end = body.find(ORG_ID, start)
                if end < 0:
                    break

                segment = body[start:end + len(ORG_ID)]
                if '"LocalBusiness"' in segment:
                    total += 1
                    missing = [token for token in REQUIRED if token not in segment]
                    if missing:
                        failures.append((path.relative_to(repo), missing))
                    else:
                        good += 1
                pos = end + len(ORG_ID)

    print("TAMPA BAY SHINE LOCALBUSINESS ADDRESS AUDIT")
    print("=" * 48)
    print(f"LocalBusiness entities: {total}")
    print(f"Valid address objects: {good}")
    print(f"Missing/invalid address objects: {len(failures)}")

    if failures:
        for path, missing in failures:
            print(f"ERROR: {path}: missing {', '.join(missing)}")
        print("RESULT: FAILED")
        return 1

    if total == 0:
        print("ERROR: no Tampa Bay Shine LocalBusiness entities found")
        return 3

    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
