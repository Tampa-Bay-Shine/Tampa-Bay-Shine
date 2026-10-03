from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "cloudflare-site/seo-dashboard/data/ai-visibility.json"


def load_data(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": 1, "observations": []}

    with path.open(encoding="utf-8-sig") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise SystemExit("Visibility data must be a JSON object.")

    data.setdefault("schema_version", 1)
    data.setdefault("observations", [])

    if not isinstance(data["observations"], list):
        raise SystemExit("'observations' must be a JSON array.")

    return data


def save_data(path: Path, data: dict) -> None:
    data["observations"] = sorted(
        data["observations"],
        key=lambda x: (
            x.get("date", ""),
            x.get("platform", ""),
            x.get("prompt", ""),
            x.get("run", 0),
        ),
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value

    value = str(value or "").strip().lower()

    if value in {"1", "true", "yes", "y"}:
        return True
    if value in {"0", "false", "no", "n", ""}:
        return False

    raise ValueError(f"Invalid boolean value: {value!r}")


def parse_position(value):
    value = str(value or "").strip()

    if not value:
        return None

    position = int(value)

    if position < 1:
        raise ValueError("Position must be 1 or greater.")

    return position


def normalize(row: dict) -> dict:
    observation_date = str(
        row.get("date") or date.today().isoformat()
    ).strip()

    date.fromisoformat(observation_date)

    platform = str(row.get("platform") or "").strip()
    prompt = str(row.get("prompt") or "").strip()

    if not platform:
        raise ValueError("platform is required")

    if not prompt:
        raise ValueError("prompt is required")

    mentioned = parse_bool(row.get("mentioned"))
    cited = parse_bool(row.get("cited"))
    position = parse_position(
        row.get("position", row.get("order"))
    )

    citation_url = str(
        row.get("citation_url") or row.get("cited_url") or ""
    ).strip() or None

    category = str(row.get("category") or "").strip() or None
    model = str(row.get("model") or "").strip() or None

    run_raw = str(row.get("run") or "1").strip()
    run = int(run_raw)

    if run < 1:
        raise ValueError("run must be 1 or greater")

    return {
        "date": observation_date,
        "platform": platform,
        "model": model,
        "category": category,
        "prompt": prompt,
        "run": run,
        "mentioned": mentioned,
        "cited": cited,
        "position": position,
        "citation_url": citation_url,
    }


def observation_key(x: dict):
    return (
        x.get("date"),
        x.get("platform"),
        x.get("model"),
        x.get("prompt"),
        x.get("run"),
    )


def add_observations(data: dict, incoming: list[dict]) -> tuple[int, int]:
    existing = {
        observation_key(x): i
        for i, x in enumerate(data["observations"])
    }

    added = 0
    updated = 0

    for observation in incoming:
        key = observation_key(observation)

        if key in existing:
            data["observations"][existing[key]] = observation
            updated += 1
        else:
            existing[key] = len(data["observations"])
            data["observations"].append(observation)
            added += 1

    return added, updated


def import_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        required = {"platform", "prompt", "mentioned", "cited"}
        fields = set(reader.fieldnames or [])
        missing = required - fields

        if missing:
            raise SystemExit(
                "CSV missing required columns: "
                + ", ".join(sorted(missing))
            )

        output = []

        for line_number, row in enumerate(reader, start=2):
            try:
                output.append(normalize(row))
            except Exception as exc:
                raise SystemExit(
                    f"CSV line {line_number}: {exc}"
                ) from exc

        return output


def summary(data: dict) -> None:
    observations = data["observations"]

    print("Observations:", len(observations))

    if not observations:
        print("Status: No observations")
        return

    mentioned = sum(1 for x in observations if x["mentioned"])
    cited = sum(1 for x in observations if x["cited"])

    mention_rate = mentioned / len(observations) * 100
    citation_rate = cited / len(observations) * 100

    positions = [
        x["position"]
        for x in observations
        if x.get("position") is not None
    ]

    print(f"Mentioned: {mentioned} ({mention_rate:.1f}%)")
    print(f"Cited: {cited} ({citation_rate:.1f}%)")

    if positions:
        print(
            "Average appearance position:",
            f"{sum(positions) / len(positions):.2f}",
        )
    else:
        print("Average appearance position: No observations")

    platforms = sorted(
        {x["platform"] for x in observations}
    )
    print("Platforms:", ", ".join(platforms))


def main():
    ap = argparse.ArgumentParser(
        description="Record or import controlled AI answer visibility observations."
    )

    ap.add_argument("--data", default=str(DEFAULT_DATA))
    ap.add_argument("--import-csv")
    ap.add_argument("--summary", action="store_true")

    ap.add_argument("--date")
    ap.add_argument("--platform")
    ap.add_argument("--model")
    ap.add_argument("--category")
    ap.add_argument("--prompt")
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--mentioned")
    ap.add_argument("--cited")
    ap.add_argument("--position", type=int)
    ap.add_argument("--citation-url")

    args = ap.parse_args()
    path = Path(args.data)
    data = load_data(path)

    incoming = []

    if args.import_csv:
        incoming.extend(import_csv(Path(args.import_csv)))

    manual_requested = any(
        value is not None
        for value in (
            args.platform,
            args.prompt,
            args.mentioned,
            args.cited,
        )
    )

    if manual_requested:
        if args.platform is None or args.prompt is None:
            raise SystemExit(
                "--platform and --prompt are required for a manual observation."
            )

        incoming.append(
            normalize(
                {
                    "date": args.date or date.today().isoformat(),
                    "platform": args.platform,
                    "model": args.model,
                    "category": args.category,
                    "prompt": args.prompt,
                    "run": args.run,
                    "mentioned": args.mentioned,
                    "cited": args.cited,
                    "position": args.position,
                    "citation_url": args.citation_url,
                }
            )
        )

    if incoming:
        added, updated = add_observations(data, incoming)
        save_data(path, data)
        print("Added:", added)
        print("Updated:", updated)
        print("Wrote:", path)

    if args.summary or not incoming:
        summary(data)


if __name__ == "__main__":
    main()
