#!/usr/bin/env python3
"""Repair known UTF-8 mojibake on the Tampa Bay Shine Services page."""

from pathlib import Path
from datetime import datetime
import argparse
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "cloudflare-site" / "services" / "index.html"

# Use ASCII-only replacements to prevent another encoding problem.
REPLACEMENTS = {
    "\u00e2\u20ac\u2122": "&#8217;",  # Curly apostrophe
    "\u00e2\u2020\u2019": "&#8594;", # Right arrow
    "\u00c2\u00b7": "&middot;",      # Middle dot
    "\u00c2\u00a9": "&copy;",        # Copyright
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not TARGET.is_file():
        print("ERROR: Services page not found.")
        return 1

    original = TARGET.read_bytes()
    text = original.decode("utf-8")

    updated = text
    total = 0

    for bad, good in REPLACEMENTS.items():
        count = updated.count(bad)
        if count:
            print(f"{bad!r} -> {good}: {count}")
            updated = updated.replace(bad, good)
            total += count

    print(f"Total replacements: {total}")

    if not total:
        print("No known encoding issues found.")
        return 0

    if not args.apply:
        print("DRY RUN: No files changed.")
        return 0

    backup_dir = ROOT / "reports" / (
        "services-encoding-backup-" +
        datetime.now().strftime("%Y%m%d-%H%M%S")
    )
    backup_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(TARGET, backup_dir / "index.html")

    # Preserve the original line endings and avoid PowerShell
    # Set-Content rewriting the HTML.
    TARGET.write_bytes(updated.encode("utf-8"))

    print("SUCCESS: Services page encoding repaired.")
    print("Backup:", backup_dir)
    return 0

if __name__ == "__main__":
    sys.exit(main())
