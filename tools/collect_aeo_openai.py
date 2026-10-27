from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from ai_visibility import BENCHMARK_PROMPTS, BENCHMARK_VERSION  # noqa: E402

API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-5.5"
TBS_DOMAIN = "tampabayshine.com"
TBS_NAME_RE = re.compile(r"\btampa\s+bay\s+shine\b", re.I)


def api_request(api_key: str, model: str, prompt: str) -> dict:
    payload = {
        "model": model,
        "input": prompt,
        "tools": [{"type": "web_search"}],
        "include": ["web_search_call.action.sources"],
        "store": False,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc


def output_text_and_citations(response: dict) -> tuple[str, list[str]]:
    texts: list[str] = []
    urls: list[str] = []

    for item in response.get("output") or []:
        if item.get("type") != "message":
            continue
        for content in item.get("content") or []:
            if content.get("type") != "output_text":
                continue
            text = content.get("text") or ""
            if text:
                texts.append(text)
            for annotation in content.get("annotations") or []:
                if annotation.get("type") == "url_citation":
                    url = annotation.get("url")
                    if url:
                        urls.append(url)

    # Preserve order while deduplicating.
    urls = list(dict.fromkeys(urls))
    return "\n".join(texts).strip(), urls


def is_tbs_url(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host == TBS_DOMAIN or host.endswith("." + TBS_DOMAIN)


def detect_mention(text: str, citation_urls: list[str]) -> bool:
    return bool(
        TBS_NAME_RE.search(text or "")
        or TBS_DOMAIN in (text or "").lower()
        or any(is_tbs_url(url) for url in citation_urls)
    )


def detect_position(text: str) -> int | None:
    """Return position only for an explicitly numbered TBS list item."""
    if not text:
        return None

    for match in re.finditer(
        r"(?m)^\s*(?:#{1,6}\s*)?(?:\*\*)?"
        r"(\d{1,2})[\.\)]\s+"
        r"(.+?)(?:\*\*)?\s*$",
        text,
    ):
        position = int(match.group(1))
        line = match.group(2)

        if TBS_NAME_RE.search(line) or TBS_DOMAIN in line.lower():
            return position

    return None

def next_run(data_path: Path, observation_date: str, platform: str, model: str) -> int:
    if not data_path.exists():
        return 1
    try:
        data = json.loads(data_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return 1

    runs = []
    for row in data.get("benchmark_runs") or []:
        if (
            row.get("date") == observation_date
            and row.get("platform") == platform
            and (row.get("model") or "") == model
        ):
            try:
                runs.append(int(row.get("run") or 0))
            except Exception:
                pass
    return max(runs, default=0) + 1


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Run the fixed Tampa Bay Shine AEO benchmark through fresh, "
            "stateless OpenAI Responses API requests with web search."
        )
    )
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--run", type=int)
    ap.add_argument(
        "--platform",
        default="OpenAI Responses API",
        help="Measurement surface label stored in the AEO dataset.",
    )
    ap.add_argument(
        "--output",
        help="CSV output path. Defaults under reports/.",
    )
    ap.add_argument(
        "--raw-dir",
        help="Raw response directory. Defaults under reports/aeo-raw/.",
    )
    ap.add_argument(
        "--data",
        default=str(
            ROOT / "cloudflare-site/seo-dashboard/data/ai-visibility.json"
        ),
    )
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is not set. Set it in the current PowerShell "
            "session before running this collector."
        )

    observation_date = args.date
    platform = args.platform
    model = args.model
    run = args.run or next_run(
        Path(args.data), observation_date, platform, model
    )

    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "-", model).strip("-")
    output = Path(args.output) if args.output else (
        ROOT / "reports"
        / f"aeo-openai-{observation_date}-run{run}-{safe_model}.csv"
    )
    raw_dir = Path(args.raw_dir) if args.raw_dir else (
        ROOT / "reports" / "aeo-raw"
        / f"{observation_date}-openai-run{run}-{safe_model}"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    fields = [
        "date", "platform", "model", "category", "prompt_id", "prompt",
        "run", "mentioned", "cited", "position", "citation_url",
    ]
    rows = []

    print(f"Benchmark: {BENCHMARK_VERSION}")
    print(f"Platform: {platform}")
    print(f"Model: {model}")
    print(f"Date: {observation_date}")
    print(f"Run: {run}")
    print(f"Prompts: {len(BENCHMARK_PROMPTS)}")
    print()

    for index, benchmark in enumerate(BENCHMARK_PROMPTS, start=1):
        prompt_id = benchmark["id"]
        prompt = benchmark["prompt"]
        print(f"[{index:02d}/20] {prompt_id}")

        response = api_request(api_key, model, prompt)
        text, citation_urls = output_text_and_citations(response)

        raw_path = raw_dir / f"{index:02d}-{prompt_id}.json"
        raw_path.write_text(
            json.dumps(response, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        tbs_urls = [url for url in citation_urls if is_tbs_url(url)]
        mentioned = detect_mention(text, citation_urls)
        cited = bool(tbs_urls)
        position = detect_position(text) if mentioned else None

        rows.append({
            "date": observation_date,
            "platform": platform,
            "model": model,
            "category": benchmark["category"],
            "prompt_id": prompt_id,
            "prompt": prompt,
            "run": run,
            "mentioned": "yes" if mentioned else "no",
            "cited": "yes" if cited else "no",
            "position": position or "",
            "citation_url": tbs_urls[0] if tbs_urls else "",
        })

        print(
            f"         mentioned={'yes' if mentioned else 'no'} "
            f"cited={'yes' if cited else 'no'} "
            f"position={position or '-'}"
        )
        if index < len(BENCHMARK_PROMPTS) and args.delay > 0:
            time.sleep(args.delay)

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    mentions = sum(row["mentioned"] == "yes" for row in rows)
    citations = sum(row["cited"] == "yes" for row in rows)

    print()
    print("COLLECTION COMPLETE")
    print(f"CSV: {output}")
    print(f"Raw responses: {raw_dir}")
    print(f"Coverage: {len(rows)}/20")
    print(f"Mentions: {mentions}/20 ({mentions / 20 * 100:.1f}%)")
    print(f"Citations: {citations}/20 ({citations / 20 * 100:.1f}%)")
    print()
    print("Review the CSV/raw responses, then import with:")
    print(
        f'python.exe .\\tools\\ai_visibility.py '
        f'--import-csv "{output}" --summary'
    )


if __name__ == "__main__":
    main()
