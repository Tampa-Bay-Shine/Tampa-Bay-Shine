from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = (
    ROOT
    / "cloudflare-site"
    / "seo-dashboard"
    / "data"
    / "ai-visibility.json"
)

EXPECTED_VERSION = "tbs-aeo-core-v1"
EXPECTED_PROMPTS = 20

errors = []

# Missing controlled observations are unknown, not negative
# observations. Blank result fields must therefore be rejected.
try:
    from ai_visibility import parse_bool

    try:
        parse_bool("", "mentioned")
        errors.append(
            "blank mentioned value was accepted"
        )
    except ValueError:
        pass

    try:
        parse_bool(None, "cited")
        errors.append(
            "blank cited value was accepted"
        )
    except ValueError:
        pass

    if parse_bool("no", "mentioned") is not False:
        errors.append(
            "explicit 'no' did not parse as False"
        )

    if parse_bool("yes", "mentioned") is not True:
        errors.append(
            "explicit 'yes' did not parse as True"
        )

except Exception as exc:
    errors.append(
        f"boolean validation regression failed: {exc}"
    )

if not DATA.exists():
    errors.append(
        f"Missing dataset: {DATA}"
    )
else:
    with DATA.open(
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    if data.get("schema_version") != 2:
        errors.append(
            "schema_version must be 2"
        )

    benchmark = (
        data.get("benchmark") or {}
    )

    if (
        benchmark.get("version")
        != EXPECTED_VERSION
    ):
        errors.append(
            "unexpected benchmark version"
        )

    prompts = (
        benchmark.get("prompts") or []
    )

    if len(prompts) != EXPECTED_PROMPTS:
        errors.append(
            f"expected {EXPECTED_PROMPTS} "
            f"canonical prompts; "
            f"found {len(prompts)}"
        )

    ids = [
        row.get("id")
        for row in prompts
    ]

    if len(set(ids)) != len(ids):
        errors.append(
            "benchmark prompt IDs "
            "must be unique"
        )

    runs = (
        data.get("benchmark_runs")
        or []
    )

    for run in runs:
        complete = (
            run.get("complete")
            is True
        )

        coverage = (
            run.get(
                "observed_prompts"
            )
        )

        if (
            complete
            and coverage
            != EXPECTED_PROMPTS
        ):
            errors.append(
                "complete benchmark run "
                "does not contain all "
                "20 prompts"
            )

    latest_complete = (
        data.get(
            "latest_complete_run"
        )
    )

    if latest_complete:
        if (
            latest_complete.get(
                "complete"
            )
            is not True
        ):
            errors.append(
                "latest_complete_run "
                "is not complete"
            )

        if (
            latest_complete.get(
                "observed_prompts"
            )
            != EXPECTED_PROMPTS
        ):
            errors.append(
                "latest_complete_run "
                "does not have "
                "20 prompts"
            )

    observations = (
        data.get("observations")
        or []
    )

    for row in observations:
        if (
            row.get(
                "benchmark_version"
            )
            == EXPECTED_VERSION
        ):
            if (
                row.get("prompt_id")
                not in set(ids)
            ):
                errors.append(
                    "observation contains "
                    "unknown benchmark "
                    "prompt_id"
                )

print(
    "TAMPA BAY SHINE "
    "AI VISIBILITY REGRESSION"
)
print("=" * 43)
print(
    "Canonical prompts:",
    EXPECTED_PROMPTS,
)
print(
    "Benchmark runs:",
    len(
        data.get(
            "benchmark_runs",
            []
        )
    ) if DATA.exists() else 0,
)
print("Errors:", len(errors))

for error in errors:
    print("ERROR:", error)

if errors:
    print("RESULT: FAIL")
    sys.exit(1)

print("RESULT: PASS")
