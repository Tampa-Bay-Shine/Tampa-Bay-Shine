#!/usr/bin/env python3

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_WORKFLOW = Path(
    "cloudflare-site/seo-dashboard/data/opportunity-workflow.json"
)
DEFAULT_INTELLIGENCE = Path(
    "cloudflare-site/seo-dashboard/data/opportunity-intelligence.json"
)
DEFAULT_EVENTS = Path(
    "cloudflare-site/seo-dashboard/data/events.json"
)

STATUSES = (
    "new",
    "investigating",
    "implemented",
    "measuring",
    "closed",
)

EVENT_CATEGORIES = (
    "Technical",
    "Content",
    "On-page",
    "Internal linking",
    "Migration",
    "Local SEO",
    "AEO",
)


def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def normalize_page(value):
    value = str(value or "").strip()

    if not value:
        return ""

    if value.startswith(("http://", "https://")):
        parsed = urlsplit(value)
        path = parsed.path or "/"
    else:
        path = value.split("?", 1)[0].split("#", 1)[0]

    if not path.startswith("/"):
        path = "/" + path

    if path != "/":
        path = path.rstrip("/")

    return path.lower()


def stable_opportunity_id(action):
    parts = [
        str(action.get("type") or "").strip().lower(),
        str(action.get("query") or "").strip().lower(),
        normalize_page(action.get("page")),
        str(action.get("subject") or "").strip().lower(),
    ]

    identity = "|".join(parts)
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]

    return f"opp-{digest}"


def load_workflow(path):
    data = load_json(
        path,
        {
            "schema_version": 1,
            "updated_at": None,
            "items": {},
        },
    )

    if data.get("schema_version") != 1:
        raise ValueError("Unsupported opportunity workflow schema_version.")

    if not isinstance(data.get("items"), dict):
        raise ValueError("'items' must be an object.")

    return data


def intelligence_actions(path):
    data = load_json(path, {"actions": []})
    actions = data.get("actions", [])

    if not isinstance(actions, list):
        raise ValueError("Opportunity Intelligence 'actions' must be a list.")

    return actions


def find_action(actions, opportunity_id):
    for action in actions:
        action_id = action.get("id") or stable_opportunity_id(action)

        if action_id == opportunity_id:
            return action

    raise ValueError(
        f"Opportunity ID not found in current intelligence: {opportunity_id}"
    )


def workflow_record(action, opportunity_id, existing=None):
    existing = existing or {}

    return {
        "id": opportunity_id,
        "status": existing.get("status", "new"),
        "subject": action.get("subject"),
        "query": action.get("query"),
        "page": action.get("page"),
        "type": action.get("type"),
        "created_at": existing.get("created_at"),
        "updated_at": existing.get("updated_at"),
        "implemented_at": existing.get("implemented_at"),
        "implementation_summary": existing.get(
            "implementation_summary", ""
        ),
        "notes": existing.get("notes", ""),
        "seo_event": existing.get("seo_event"),
    }


def sync_workflow(args):
    workflow_path = Path(args.file)
    actions = intelligence_actions(Path(args.intelligence))
    workflow = load_workflow(workflow_path)
    now = datetime.now(timezone.utc).isoformat()

    current_ids = set()

    for action in actions:
        opportunity_id = action.get("id") or stable_opportunity_id(action)
        current_ids.add(opportunity_id)

        existing = workflow["items"].get(opportunity_id)
        record = workflow_record(action, opportunity_id, existing)

        if not record["created_at"]:
            record["created_at"] = now

        if not record["updated_at"]:
            record["updated_at"] = now

        workflow["items"][opportunity_id] = record

    workflow["updated_at"] = now
    save_json(workflow_path, workflow)

    active = len(current_ids)
    retained = len(workflow["items"]) - active

    print(
        f"Workflow synced: {workflow_path} | "
        f"{active} current opportunities | "
        f"{retained} historical records retained"
    )


def set_status(args):
    workflow_path = Path(args.file)
    actions = intelligence_actions(Path(args.intelligence))
    workflow = load_workflow(workflow_path)

    action = find_action(actions, args.id)
    existing = workflow["items"].get(args.id)
    record = workflow_record(action, args.id, existing)

    now = datetime.now(timezone.utc).isoformat()

    if not record["created_at"]:
        record["created_at"] = now

    record["status"] = args.status
    record["updated_at"] = now

    if args.summary is not None:
        record["implementation_summary"] = args.summary.strip()

    if args.notes is not None:
        record["notes"] = args.notes.strip()

    if args.status == "implemented" and not record["implemented_at"]:
        record["implemented_at"] = now

    workflow["items"][args.id] = record
    workflow["updated_at"] = now
    save_json(workflow_path, workflow)

    print(f"Updated: {args.id} -> {args.status}")


def add_event(args):
    workflow_path = Path(args.file)
    intelligence_path = Path(args.intelligence)
    events_path = Path(args.events)

    actions = intelligence_actions(intelligence_path)
    workflow = load_workflow(workflow_path)
    action = find_action(actions, args.id)

    if args.id not in workflow["items"]:
        raise ValueError(
            "Sync the workflow before creating an implementation event."
        )

    record = workflow["items"][args.id]

    if record.get("status") not in ("implemented", "measuring", "closed"):
        raise ValueError(
            "Mark the opportunity implemented before creating its SEO event."
        )

    event_date = args.date or date.today().isoformat()
    summary = (
        args.description
        or record.get("implementation_summary")
        or action.get("recommended_action")
        or "Implemented Opportunity Intelligence recommendation."
    ).strip()

    title = (
        args.title
        or f"Opportunity implemented: {action.get('subject') or args.id}"
    ).strip()

    events = load_json(
        events_path,
        {"schema_version": 1, "events": []},
    )

    if events.get("schema_version") != 1:
        raise ValueError("Unsupported events schema_version.")

    duplicate = next(
        (
            event
            for event in events.get("events", [])
            if event.get("date") == event_date
            and str(event.get("title") or "").casefold()
            == title.casefold()
        ),
        None,
    )

    if duplicate:
        raise ValueError(
            f"Duplicate SEO event: {event_date} | {title}"
        )

    urls = []

    if action.get("page"):
        urls.append(action["page"])

    event = {
        "date": event_date,
        "category": args.category,
        "title": title,
        "description": summary,
        "urls": urls,
        "notes": (
            f"Opportunity Intelligence ID: {args.id}. "
            "Event timing provides measurement context and does not prove causation."
        ),
    }

    events.setdefault("events", []).append(event)
    events["events"] = sorted(
        events["events"],
        key=lambda item: (
            item.get("date", ""),
            str(item.get("title") or "").lower(),
        ),
    )

    save_json(events_path, events)

    now = datetime.now(timezone.utc).isoformat()
    record["seo_event"] = {
        "date": event_date,
        "category": args.category,
        "title": title,
    }
    record["updated_at"] = now
    workflow["updated_at"] = now

    save_json(workflow_path, workflow)

    print(
        f"SEO event added: {event_date} | {args.category} | {title}"
    )


def list_items(args):
    workflow = load_workflow(Path(args.file))

    rows = list(workflow["items"].values())

    if args.status:
        rows = [
            row for row in rows
            if row.get("status") == args.status
        ]

    rows.sort(
        key=lambda row: (
            STATUSES.index(row.get("status", "new"))
            if row.get("status", "new") in STATUSES
            else 99,
            str(row.get("subject") or "").lower(),
        )
    )

    if not rows:
        print("No workflow items.")
        return

    for row in rows:
        print(
            f"{row.get('id')} | "
            f"{row.get('status')} | "
            f"{row.get('subject') or '--'}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Manage the SEO/AEO Opportunity Intelligence workflow."
    )

    parser.add_argument(
        "--file",
        default=str(DEFAULT_WORKFLOW),
        help="Path to opportunity-workflow.json",
    )
    parser.add_argument(
        "--intelligence",
        default=str(DEFAULT_INTELLIGENCE),
        help="Path to opportunity-intelligence.json",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sync = sub.add_parser(
        "sync",
        help="Sync current intelligence opportunities into workflow state.",
    )
    sync.set_defaults(func=sync_workflow)

    listing = sub.add_parser(
        "list",
        help="List workflow opportunities.",
    )
    listing.add_argument("--status", choices=STATUSES)
    listing.set_defaults(func=list_items)

    status = sub.add_parser(
        "status",
        help="Change an opportunity lifecycle status.",
    )
    status.add_argument("--id", required=True)
    status.add_argument("--status", required=True, choices=STATUSES)
    status.add_argument("--summary")
    status.add_argument("--notes")
    status.set_defaults(func=set_status)

    event = sub.add_parser(
        "event",
        help="Create an SEO Event for an implemented opportunity.",
    )
    event.add_argument("--id", required=True)
    event.add_argument(
        "--events",
        default=str(DEFAULT_EVENTS),
    )
    event.add_argument(
        "--category",
        required=True,
        choices=EVENT_CATEGORIES,
    )
    event.add_argument("--date")
    event.add_argument("--title")
    event.add_argument("--description")
    event.set_defaults(func=add_event)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
