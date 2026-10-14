#!/usr/bin/env python3
"""Tampa Bay Shine visibility and conversion architecture audit."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.parse import urlparse


A_RE = re.compile(
    r'<a\b[^>]*?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
    re.I | re.S,
)

TAG_RE = re.compile(r'<[^>]+>')

META_RE = re.compile(
    r'<meta\b[^>]*>',
    re.I,
)

CONTENT_RE = re.compile(
    r'<main\b[^>]*>(.*?)</main>',
    re.I | re.S,
)

TITLE_RE = re.compile(
    r'<title[^>]*>(.*?)</title>',
    re.I | re.S,
)

H1_RE = re.compile(
    r'<h1[^>]*>(.*?)</h1>',
    re.I | re.S,
)


def clean(value):
    return re.sub(
        r'\s+',
        ' ',
        html.unescape(TAG_RE.sub(' ', value)),
    ).strip()


def route_for(path, root):
    rel = path.relative_to(root).as_posix()

    if rel == "index.html":
        return "/"

    if rel.endswith("/index.html"):
        return "/" + rel[:-10]

    return "/" + rel


def normalize_href(href):
    if not href:
        return None

    if href.startswith(
        ("#", "mailto:", "tel:", "javascript:")
    ):
        return None

    parsed = urlparse(href)

    if parsed.scheme and parsed.netloc:
        if parsed.netloc.lower() not in {
            "tampabayshine.com",
            "www.tampabayshine.com",
        }:
            return None

    path = parsed.path or "/"

    if not path.startswith("/"):
        return None

    if (
        path != "/"
        and not path.endswith("/")
        and "." not in path.rsplit("/", 1)[-1]
    ):
        path += "/"

    return path


def contains(text, *terms):
    return any(term in text for term in terms)


def is_noindex(raw):
    """Detect robots noindex regardless of meta attribute order."""
    for tag in META_RE.findall(raw):
        lower = tag.lower()

        if (
            re.search(
                r'name\s*=\s*["\']robots["\']',
                lower,
            )
            and "noindex" in lower
        ):
            return True

    return False


def extract_links(raw):
    links = []

    for href, label in A_RE.findall(raw):
        normalized = normalize_href(
            html.unescape(href)
        )

        if normalized:
            links.append(
                (normalized, clean(label))
            )

    return links


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo",
        default=".",
        help="Repository root",
    )

    parser.add_argument(
        "--out",
        default="reports/visibility_conversion_audit",
        help="Output path without extension",
    )

    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    root = repo / "cloudflare-site"
    out = repo / args.out

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not root.exists():
        raise SystemExit(
            f"ERROR: Cloudflare site directory not found: {root}"
        )

    pages = {}

    for file_path in sorted(root.rglob("*.html")):
        raw = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        route = route_for(
            file_path,
            root,
        )

        full_text = clean(raw).lower()

        main_match = CONTENT_RE.search(raw)

        if main_match:
            content_html = main_match.group(1)
        else:
            content_html = raw

        content_text = clean(
            content_html
        ).lower()

        all_links = extract_links(raw)
        content_links = extract_links(
            content_html
        )

        title_match = TITLE_RE.search(raw)
        h1_match = H1_RE.search(raw)

        pages[route] = {
            "file":
                file_path.relative_to(repo).as_posix(),

            "indexable":
                not is_noindex(raw)
                and route != "/404.html",

            "title":
                clean(title_match.group(1))
                if title_match else "",

            "h1":
                clean(h1_match.group(1))
                if h1_match else "",

            "links":
                all_links,

            "content_links":
                content_links,

            # Entire-page signals
            "book_cta":
                sum(
                    1
                    for url, _ in all_links
                    if url == "/booknow/"
                ),

            "coupon_links":
                sum(
                    1
                    for url, _ in all_links
                    if url == "/coupons/"
                ),

            "online":
                contains(
                    full_text,
                    "online booking",
                    "book online",
                    "online quote",
                    "quote online",
                ),

            "24_7":
                contains(
                    full_text,
                    "24/7",
                    "24 hours",
                    "24-hour",
                    "24 hour",
                ),

            # Main-content conversion signals
            "content_book_cta":
                sum(
                    1
                    for url, _ in content_links
                    if url == "/booknow/"
                ),

            "content_coupon_links":
                sum(
                    1
                    for url, _ in content_links
                    if url == "/coupons/"
                ),

            "content_online":
                contains(
                    content_text,
                    "online booking",
                    "book online",
                    "online quote",
                    "quote online",
                ),

            "content_24_7":
                contains(
                    content_text,
                    "24/7",
                    "24 hours",
                    "24-hour",
                    "24 hour",
                ),

            "content_quote":
                contains(
                    content_text,
                    "get a quote",
                    "instant quote",
                    "online quote",
                    "quote online",
                    "get pricing",
                    "check pricing",
                ),

            "content_discount":
                contains(
                    content_text,
                    "discount",
                    "coupon",
                    "% off",
                    "save $",
                    "save ",
                    "special offer",
                ),

            "content_insured":
                "insured" in content_text,

            "content_licensed":
                "licensed" in content_text,
        }

    inbound = defaultdict(list)
    anchors = defaultdict(Counter)

    # Build internal-link graph using indexable pages.
    for source, page in pages.items():
        if not page["indexable"]:
            continue

        for destination, label in page["links"]:
            if (
                destination in pages
                and pages[destination]["indexable"]
            ):
                inbound[destination].append(
                    source
                )

                if label:
                    anchors[destination][label] += 1

    # Calculate click depth from homepage.
    depth = {
        url: None
        for url, page in pages.items()
        if page["indexable"]
    }

    if "/" in depth:
        depth["/"] = 0
        queue = deque(["/"])

        while queue:
            source = queue.popleft()

            for destination, _ in pages[source]["links"]:
                if (
                    destination in depth
                    and depth[destination] is None
                ):
                    depth[destination] = (
                        depth[source] + 1
                    )

                    queue.append(
                        destination
                    )

    rows = []

    excluded_scoring = {
        "/",
        "/privacy-policy/",
        "/terms/",
        "/data-deletion/",
        "/sms-opt-in/",
    }

    for url, page in pages.items():
        if not page["indexable"]:
            continue

        unique_inbound = len(
            set(inbound[url])
        )

        total_inbound = len(
            inbound[url]
        )

        click_depth = depth[url]

        score = 0

        if url not in excluded_scoring:

            # Internal authority
            if unique_inbound < 3:
                score += 3

            elif unique_inbound < 6:
                score += 2

            elif unique_inbound < 10:
                score += 1

            # Crawl/click depth
            if (
                click_depth is None
                or click_depth > 3
            ):
                score += 3

            elif click_depth == 3:
                score += 1

            # Contextual conversion weakness
            if page["content_book_cta"] == 0:
                score += 2

            if not page["content_online"]:
                score += 1

            if not (
                page["content_insured"]
                or page["content_licensed"]
            ):
                score += 1

        rows.append({
            "route":
                url,

            "file":
                page["file"],

            "inbound_unique":
                unique_inbound,

            "inbound_total":
                total_inbound,

            "click_depth":
                click_depth,

            "outbound_internal":
                sum(
                    1
                    for destination, _
                    in page["links"]
                    if destination in pages
                ),

            # Global/sitewide
            "booknow_links":
                page["book_cta"],

            "coupon_links":
                page["coupon_links"],

            # Contextual/main content
            "content_booknow_links":
                page["content_book_cta"],

            "content_coupon_links":
                page["content_coupon_links"],

            "content_online_booking_quote":
                page["content_online"],

            "content_mentions_24_7":
                page["content_24_7"],

            "content_quote_message":
                page["content_quote"],

            "content_discount_message":
                page["content_discount"],

            "content_insured":
                page["content_insured"],

            "content_licensed":
                page["content_licensed"],

            "priority_score":
                score,

            "top_anchors":
                " | ".join(
                    f"{anchor} ({count})"
                    for anchor, count
                    in anchors[url].most_common(5)
                ),

            "title":
                page["title"],

            "h1":
                page["h1"],
        })

    rows.sort(
        key=lambda row: (
            -row["priority_score"],
            row["inbound_unique"],
            row["route"],
        )
    )

    if not rows:
        raise SystemExit(
            "ERROR: No indexable HTML pages found."
        )

    csv_path = Path(
        str(out) + ".csv"
    )

    json_path = Path(
        str(out) + ".json"
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
        )

        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "indexable_pages":
            len(rows),

        "pages_with_global_booknow_link":
            sum(
                row["booknow_links"] > 0
                for row in rows
            ),

        "pages_with_global_coupon_link":
            sum(
                row["coupon_links"] > 0
                for row in rows
            ),

        "pages_with_contextual_booknow_link":
            sum(
                row["content_booknow_links"] > 0
                for row in rows
            ),

        "pages_with_contextual_coupon_link":
            sum(
                row["content_coupon_links"] > 0
                for row in rows
            ),

        "pages_with_contextual_online_booking_or_quote_language":
            sum(
                row["content_online_booking_quote"]
                for row in rows
            ),

        "pages_with_contextual_24_7_message":
            sum(
                row["content_mentions_24_7"]
                for row in rows
            ),

        "pages_with_contextual_quote_message":
            sum(
                row["content_quote_message"]
                for row in rows
            ),

        "pages_with_contextual_discount_message":
            sum(
                row["content_discount_message"]
                for row in rows
            ),

        "pages_with_contextual_insured_signal":
            sum(
                row["content_insured"]
                for row in rows
            ),

        "pages_with_contextual_licensed_signal":
            sum(
                row["content_licensed"]
                for row in rows
            ),

        "pages_depth_3_plus":
            sum(
                row["click_depth"] is None
                or row["click_depth"] >= 3
                for row in rows
            ),

        "underlinked_lt_3_unique":
            sum(
                row["inbound_unique"] < 3
                for row in rows
            ),

        "highest_priority":
            rows[:25],
    }

    json_path.write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        "VISIBILITY + CONVERSION ARCHITECTURE AUDIT v2"
    )

    print("=" * 56)

    for key, value in summary.items():
        if key != "highest_priority":
            print(
                f"{key}: {value}"
            )

    print()
    print("Highest-priority pages")
    print("-" * 56)

    for row in rows[:25]:
        print(
            f'{row["priority_score"]:>2}  '
            f'in={row["inbound_unique"]:>2} '
            f'depth={str(row["click_depth"]):>4} '
            f'book={row["content_booknow_links"]:>2} '
            f'coupon={row["content_coupon_links"]:>2} '
            f'online={str(row["content_online_booking_quote"]):<5} '
            f'24/7={str(row["content_mentions_24_7"]):<5} '
            f'{row["route"]}'
        )

    print()
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
