from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "cloudflare-site/seo-dashboard/data/ai-visibility.json"

SCHEMA_VERSION = 2
BENCHMARK_VERSION = "tbs-aeo-core-v1"

BENCHMARK_PROMPTS = [
    {
        "id": "residential-tampa-best",
        "category": "Residential local",
        "prompt": "What are the best house cleaning services in Tampa, Florida?",
    },
    {
        "id": "residential-tampa-reliable",
        "category": "Residential local",
        "prompt": "Which house cleaning companies in Tampa are reliable and easy to book online?",
    },
    {
        "id": "residential-tampa-recurring",
        "category": "Residential local",
        "prompt": "Who offers recurring house cleaning services in Tampa, Florida?",
    },
    {
        "id": "residential-tampa-professional",
        "category": "Residential local",
        "prompt": "Recommend professional residential cleaning companies in Tampa, Florida.",
    },

    {
        "id": "deep-tampa-best",
        "category": "Deep cleaning",
        "prompt": "Who offers the best deep cleaning services in Tampa, Florida?",
    },
    {
        "id": "deep-tampa-home",
        "category": "Deep cleaning",
        "prompt": "Which companies provide deep house cleaning in Tampa?",
    },
    {
        "id": "deep-tampa-one-time",
        "category": "Deep cleaning",
        "prompt": "Recommend a company for a one-time deep cleaning in Tampa, Florida.",
    },
    {
        "id": "deep-tampa-professional",
        "category": "Deep cleaning",
        "prompt": "What professional cleaning companies in Tampa specialize in deep cleaning?",
    },

    {
        "id": "moveout-tampa-best",
        "category": "Move-out",
        "prompt": "What are the best move-out cleaning services in Tampa, Florida?",
    },
    {
        "id": "moveout-tampa-recommend",
        "category": "Move-out",
        "prompt": "Recommend a move-out cleaning company in Tampa, Florida.",
    },
    {
        "id": "movein-tampa",
        "category": "Move-out",
        "prompt": "Who provides move-in cleaning services in Tampa, Florida?",
    },
    {
        "id": "moveout-tampa-professional",
        "category": "Move-out",
        "prompt": "Which professional cleaners in Tampa handle move-out cleaning?",
    },

    {
        "id": "commercial-tampa-best",
        "category": "Commercial",
        "prompt": "What are the best commercial cleaning services in Tampa, Florida?",
    },
    {
        "id": "office-tampa-best",
        "category": "Commercial",
        "prompt": "What are the best office cleaning services in Tampa, Florida?",
    },
    {
        "id": "commercial-tampa-reliable",
        "category": "Commercial",
        "prompt": "Recommend reliable commercial cleaning companies in Tampa, Florida.",
    },
    {
        "id": "medical-office-tampa",
        "category": "Commercial",
        "prompt": "Who provides medical office cleaning in Tampa, Florida?",
    },

    {
        "id": "brandon-house-cleaning",
        "category": "Local markets",
        "prompt": "What are the best house cleaning services in Brandon, Florida?",
    },
    {
        "id": "riverview-house-cleaning",
        "category": "Local markets",
        "prompt": "What are the best house cleaning services in Riverview, Florida?",
    },
    {
        "id": "south-tampa-house-cleaning",
        "category": "Local markets",
        "prompt": "What are the best house cleaning services in South Tampa, Florida?",
    },
    {
        "id": "wesley-chapel-house-cleaning",
        "category": "Local markets",
        "prompt": "What are the best house cleaning services in Wesley Chapel, Florida?",
    },
]

PROMPT_BY_ID = {
    row["id"]: row
    for row in BENCHMARK_PROMPTS
}

PROMPT_ID_BY_TEXT = {
    row["prompt"].strip().lower(): row["id"]
    for row in BENCHMARK_PROMPTS
}


def empty_data() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "benchmark": {
            "version": BENCHMARK_VERSION,
            "prompt_count": len(BENCHMARK_PROMPTS),
            "prompts": BENCHMARK_PROMPTS,
        },
        "observations": [],
        "benchmark_runs": [],
        "latest_complete_run": None,
        "latest_run": None,
        "rollups": {
            "categories": [],
            "platforms": [],
            "cited_urls": [],
        },
    }


def load_data(path: Path) -> dict:
    if not path.exists():
        return empty_data()

    with path.open(encoding="utf-8-sig") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise SystemExit("Visibility data must be a JSON object.")

    data.setdefault("observations", [])

    if not isinstance(data["observations"], list):
        raise SystemExit("'observations' must be a JSON array.")

    return data


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


def canonical_prompt_id(prompt: str):
    return PROMPT_ID_BY_TEXT.get(
        str(prompt or "").strip().lower()
    )


def normalize_citation_url(value):
    value = str(value or "").strip()

    if not value:
        return None

    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(
            "citation_url must be an http:// or https:// URL"
        )

    return value


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

    prompt_id = (
        str(row.get("prompt_id") or "").strip()
        or canonical_prompt_id(prompt)
    )

    if prompt_id and prompt_id not in PROMPT_BY_ID:
        raise ValueError(
            f"Unknown benchmark prompt_id: {prompt_id}"
        )

    benchmark_prompt = (
        PROMPT_BY_ID.get(prompt_id)
        if prompt_id
        else None
    )

    if benchmark_prompt:
        if (
            prompt.strip().lower()
            != benchmark_prompt["prompt"].strip().lower()
        ):
            raise ValueError(
                f"Prompt text does not match {prompt_id}"
            )

    mentioned = parse_bool(row.get("mentioned"))
    cited = parse_bool(row.get("cited"))

    position = parse_position(
        row.get("position", row.get("order"))
    )

    citation_url = normalize_citation_url(
        row.get("citation_url")
        or row.get("cited_url")
        or ""
    )

    if cited and not citation_url:
        # Some AI surfaces can visibly cite the business/source
        # without exposing a stable URL. Preserve cited=True while
        # leaving citation_url unknown.
        citation_url = None

    category = (
        str(row.get("category") or "").strip()
        or (
            benchmark_prompt["category"]
            if benchmark_prompt
            else None
        )
    )

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
        "prompt_id": prompt_id,
        "benchmark_version": (
            BENCHMARK_VERSION if prompt_id else None
        ),
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


def run_key(x: dict):
    return (
        x.get("date"),
        x.get("platform"),
        x.get("model"),
        x.get("run", 1),
    )


def rate(count, total):
    if not total:
        return None

    return round(count / total * 100, 2)


def summarize_observations(rows: list[dict]) -> dict:
    total = len(rows)
    mentioned = sum(
        1 for row in rows
        if row.get("mentioned") is True
    )
    cited = sum(
        1 for row in rows
        if row.get("cited") is True
    )

    positions = [
        int(row["position"])
        for row in rows
        if row.get("position") is not None
    ]

    return {
        "observations": total,
        "mentions": mentioned,
        "citations": cited,
        "mention_rate": rate(mentioned, total),
        "citation_rate": rate(cited, total),
        "average_appearance": (
            round(sum(positions) / len(positions), 2)
            if positions
            else None
        ),
    }


def build_benchmark_runs(observations: list[dict]) -> list[dict]:
    grouped = defaultdict(list)

    for row in observations:
        if (
            row.get("benchmark_version") != BENCHMARK_VERSION
            or not row.get("prompt_id")
        ):
            continue

        grouped[run_key(row)].append(row)

    output = []

    expected_ids = set(PROMPT_BY_ID)

    for key, rows in grouped.items():
        observation_date, platform, model, run = key

        observed_ids = {
            row.get("prompt_id")
            for row in rows
            if row.get("prompt_id")
        }

        missing_ids = sorted(
            expected_ids - observed_ids
        )

        duplicate_ids = sorted(
            prompt_id
            for prompt_id, count in Counter(
                row.get("prompt_id")
                for row in rows
                if row.get("prompt_id")
            ).items()
            if count > 1
        )

        complete = (
            observed_ids == expected_ids
            and not duplicate_ids
        )

        metrics = summarize_observations(rows)

        output.append({
            "date": observation_date,
            "platform": platform,
            "model": model,
            "run": run,
            "benchmark_version": BENCHMARK_VERSION,
            "expected_prompts": len(BENCHMARK_PROMPTS),
            "observed_prompts": len(observed_ids),
            "coverage_percent": round(
                len(observed_ids)
                / len(BENCHMARK_PROMPTS)
                * 100,
                2,
            ),
            "complete": complete,
            "missing_prompt_ids": missing_ids,
            "duplicate_prompt_ids": duplicate_ids,
            **metrics,
        })

    output.sort(
        key=lambda x: (
            x.get("date", ""),
            x.get("platform", ""),
            x.get("model") or "",
            x.get("run", 0),
        )
    )

    return output


def build_rollup(
    observations: list[dict],
    field: str,
) -> list[dict]:
    grouped = defaultdict(list)

    for row in observations:
        value = row.get(field)

        if value:
            grouped[str(value)].append(row)

    output = []

    for value, rows in grouped.items():
        output.append({
            field: value,
            **summarize_observations(rows),
        })

    output.sort(
        key=lambda x: (
            -x["observations"],
            str(x[field]).lower(),
        )
    )

    return output


def build_cited_url_rollup(
    observations: list[dict],
) -> list[dict]:
    counts = Counter(
        row.get("citation_url")
        for row in observations
        if row.get("cited") is True
        and row.get("citation_url")
    )

    return [
        {
            "citation_url": url,
            "citations": count,
        }
        for url, count in counts.most_common()
    ]


def rebuild_derived(data: dict) -> dict:
    normalized = []

    for raw in data.get("observations", []):
        normalized.append(normalize(raw))

    normalized.sort(
        key=lambda x: (
            x.get("date", ""),
            x.get("platform", ""),
            x.get("model") or "",
            x.get("run", 0),
            x.get("prompt_id") or "",
            x.get("prompt", ""),
        )
    )

    runs = build_benchmark_runs(normalized)

    latest_run = runs[-1] if runs else None

    complete_runs = [
        row for row in runs
        if row.get("complete") is True
    ]

    latest_complete = (
        complete_runs[-1]
        if complete_runs
        else None
    )

    # Headline rollups use the latest complete benchmark only.
    # If there is no complete run, do not manufacture a score.
    headline_rows = []

    if latest_complete:
        key = (
            latest_complete["date"],
            latest_complete["platform"],
            latest_complete.get("model"),
            latest_complete["run"],
        )

        headline_rows = [
            row
            for row in normalized
            if run_key(row) == key
            and row.get("benchmark_version")
            == BENCHMARK_VERSION
        ]

    data = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "benchmark": {
            "version": BENCHMARK_VERSION,
            "prompt_count": len(BENCHMARK_PROMPTS),
            "prompts": BENCHMARK_PROMPTS,
            "definition": (
                "Fixed Tampa Bay Shine controlled AI-answer "
                "benchmark. Headline visibility metrics use "
                "only the latest complete 20-prompt run."
            ),
        },
        "observations": normalized,
        "benchmark_runs": runs,
        "latest_run": latest_run,
        "latest_complete_run": latest_complete,
        "rollups": {
            "categories": build_rollup(
                headline_rows,
                "category",
            ),
            "platforms": build_rollup(
                headline_rows,
                "platform",
            ),
            "cited_urls": build_cited_url_rollup(
                headline_rows
            ),
        },
    }

    return data


def save_data(path: Path, data: dict) -> dict:
    data = rebuild_derived(data)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=True,
        ) + "\n",
        encoding="utf-8",
    )

    return data


def add_observations(
    data: dict,
    incoming: list[dict],
) -> tuple[int, int]:
    observations = data.setdefault(
        "observations",
        [],
    )

    existing = {
        observation_key(x): i
        for i, x in enumerate(observations)
    }

    added = 0
    updated = 0

    for observation in incoming:
        key = observation_key(observation)

        if key in existing:
            observations[
                existing[key]
            ] = observation
            updated += 1
        else:
            existing[key] = len(observations)
            observations.append(observation)
            added += 1

    return added, updated


def import_csv(path: Path) -> list[dict]:
    with path.open(
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        required = {
            "platform",
            "prompt",
            "mentioned",
            "cited",
        }

        fields = set(
            reader.fieldnames or []
        )

        missing = required - fields

        if missing:
            raise SystemExit(
                "CSV missing required columns: "
                + ", ".join(
                    sorted(missing)
                )
            )

        output = []

        for line_number, row in enumerate(
            reader,
            start=2,
        ):
            try:
                output.append(
                    normalize(row)
                )
            except Exception as exc:
                raise SystemExit(
                    f"CSV line "
                    f"{line_number}: {exc}"
                ) from exc

        return output


def write_template(path: Path) -> None:
    fields = [
        "date",
        "platform",
        "model",
        "category",
        "prompt_id",
        "prompt",
        "run",
        "mentioned",
        "cited",
        "position",
        "citation_url",
    ]

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in BENCHMARK_PROMPTS:
            writer.writerow({
                "date": "",
                "platform": "",
                "model": "",
                "category": row["category"],
                "prompt_id": row["id"],
                "prompt": row["prompt"],
                "run": 1,
                "mentioned": "",
                "cited": "",
                "position": "",
                "citation_url": "",
            })

    print("Wrote benchmark template:", path)


def print_prompts() -> None:
    print(
        f"Benchmark: {BENCHMARK_VERSION}"
    )
    print(
        f"Prompts: {len(BENCHMARK_PROMPTS)}"
    )

    for index, row in enumerate(
        BENCHMARK_PROMPTS,
        start=1,
    ):
        print(
            f"{index:02d}. "
            f"[{row['category']}] "
            f"{row['id']}: "
            f"{row['prompt']}"
        )


def summary(data: dict) -> None:
    data = rebuild_derived(data)

    observations = data["observations"]

    print(
        "Benchmark:",
        data["benchmark"]["version"],
    )
    print(
        "Canonical prompts:",
        data["benchmark"]["prompt_count"],
    )
    print(
        "Observations:",
        len(observations),
    )
    print(
        "Benchmark runs:",
        len(data["benchmark_runs"]),
    )

    latest = data.get("latest_run")

    if latest:
        print(
            "Latest run:",
            latest["date"],
            "|",
            latest["platform"],
            "|",
            latest.get("model") or "model unknown",
            "| run",
            latest["run"],
        )
        print(
            "Coverage:",
            f"{latest['observed_prompts']}/"
            f"{latest['expected_prompts']}",
            f"({latest['coverage_percent']}%)",
        )
        print(
            "Complete:",
            "yes" if latest["complete"] else "no",
        )

    complete = data.get(
        "latest_complete_run"
    )

    if not complete:
        print(
            "Headline visibility: "
            "No complete benchmark run"
        )
        return

    print(
        "Latest complete run:",
        complete["date"],
        "|",
        complete["platform"],
        "|",
        complete.get("model") or "model unknown",
    )
    print(
        "Mention rate:",
        f"{complete['mention_rate']}%",
    )
    print(
        "Citation rate:",
        f"{complete['citation_rate']}%",
    )
    print(
        "Average appearance:",
        complete["average_appearance"],
    )


def main():
    ap = argparse.ArgumentParser(
        description=(
            "Record/import controlled AI answer "
            "visibility observations and maintain "
            "the Tampa Bay Shine AEO benchmark."
        )
    )

    ap.add_argument(
        "--data",
        default=str(DEFAULT_DATA),
    )
    ap.add_argument("--import-csv")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--list-prompts", action="store_true")
    ap.add_argument("--write-template")

    ap.add_argument("--date")
    ap.add_argument("--platform")
    ap.add_argument("--model")
    ap.add_argument("--category")
    ap.add_argument("--prompt-id")
    ap.add_argument("--prompt")
    ap.add_argument(
        "--run",
        type=int,
        default=1,
    )
    ap.add_argument("--mentioned")
    ap.add_argument("--cited")
    ap.add_argument(
        "--position",
        type=int,
    )
    ap.add_argument("--citation-url")

    args = ap.parse_args()
    path = Path(args.data)

    if args.list_prompts:
        print_prompts()

    if args.write_template:
        write_template(
            Path(args.write_template)
        )

    data = load_data(path)

    incoming = []

    if args.import_csv:
        incoming.extend(
            import_csv(
                Path(args.import_csv)
            )
        )

    manual_requested = any(
        value is not None
        for value in (
            args.platform,
            args.prompt,
            args.prompt_id,
            args.mentioned,
            args.cited,
        )
    )

    if manual_requested:
        prompt = args.prompt

        if args.prompt_id:
            benchmark_prompt = (
                PROMPT_BY_ID.get(
                    args.prompt_id
                )
            )

            if not benchmark_prompt:
                raise SystemExit(
                    "Unknown --prompt-id: "
                    + args.prompt_id
                )

            if not prompt:
                prompt = (
                    benchmark_prompt["prompt"]
                )

        if (
            args.platform is None
            or prompt is None
        ):
            raise SystemExit(
                "--platform and either "
                "--prompt or --prompt-id "
                "are required for a "
                "manual observation."
            )

        incoming.append(
            normalize({
                "date": (
                    args.date
                    or date.today().isoformat()
                ),
                "platform": args.platform,
                "model": args.model,
                "category": args.category,
                "prompt_id": args.prompt_id,
                "prompt": prompt,
                "run": args.run,
                "mentioned": args.mentioned,
                "cited": args.cited,
                "position": args.position,
                "citation_url": (
                    args.citation_url
                ),
            })
        )

    if incoming:
        added, updated = (
            add_observations(
                data,
                incoming,
            )
        )

        data = save_data(
            path,
            data,
        )

        print("Added:", added)
        print("Updated:", updated)
        print("Wrote:", path)

    elif (
        not args.list_prompts
        and not args.write_template
    ):
        # Migrate/rebuild derived schema even
        # when no new observation is supplied.
        data = save_data(
            path,
            data,
        )

    if args.summary or (
        not incoming
        and not args.list_prompts
        and not args.write_template
    ):
        summary(data)


if __name__ == "__main__":
    main()
