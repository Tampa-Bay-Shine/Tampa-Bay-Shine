#!/usr/bin/env python3

import argparse
import json
from datetime import date
from pathlib import Path


DEFAULT_EVENTS = Path("cloudflare-site/seo-dashboard/data/events.json")

CATEGORIES = (
    "Technical",
    "Content",
    "On-page",
    "Internal linking",
    "Migration",
    "Local SEO",
    "AEO",
)


def load_events(path):
    if not path.exists():
        return {"schema_version": 1, "events": []}

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Event file root must be an object.")

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported events schema_version.")

    if not isinstance(data.get("events"), list):
        raise ValueError("'events' must be a list.")

    return data


def save_events(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    data["events"] = sorted(
        data["events"],
        key=lambda item: (item["date"], item["title"].lower())
    )

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


def validate_date(value):
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date must use YYYY-MM-DD format."
        ) from exc


def add_event(args):
    path = Path(args.file)
    data = load_events(path)

    event = {
        "date": args.date,
        "category": args.category,
        "title": args.title.strip(),
        "description": args.description.strip(),
        "urls": args.url or [],
        "notes": args.notes.strip() if args.notes else "",
    }

    if not event["title"]:
        raise ValueError("Title cannot be empty.")

    if not event["description"]:
        raise ValueError("Description cannot be empty.")

    duplicate = next(
        (
            item for item in data["events"]
            if item["date"] == event["date"]
            and item["title"].casefold() == event["title"].casefold()
        ),
        None,
    )

    if duplicate:
        raise ValueError(
            f'Duplicate event: {event["date"]} | {event["title"]}'
        )

    data["events"].append(event)
    save_events(path, data)

    print(f'Added: {event["date"]} | {event["category"]} | {event["title"]}')


def list_events(args):
    data = load_events(Path(args.file))

    if not data["events"]:
        print("No SEO events recorded.")
        return

    for event in data["events"]:
        print(
            f'{event["date"]} | '
            f'{event["category"]} | '
            f'{event["title"]}'
        )


def main():
    parser = argparse.ArgumentParser(
        description="Manage Tampa Bay Shine SEO dashboard events."
    )

    parser.add_argument(
        "--file",
        default=str(DEFAULT_EVENTS),
        help="Path to events.json",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add an SEO event")
    add.add_argument("--date", required=True, type=validate_date)
    add.add_argument("--category", required=True, choices=CATEGORIES)
    add.add_argument("--title", required=True)
    add.add_argument("--description", required=True)
    add.add_argument("--url", action="append")
    add.add_argument("--notes")
    add.set_defaults(func=add_event)

    listing = sub.add_parser("list", help="List SEO events")
    listing.set_defaults(func=list_events)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
