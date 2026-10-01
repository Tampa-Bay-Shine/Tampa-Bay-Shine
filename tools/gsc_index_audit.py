
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
DEFAULT_BASELINE = "2026-09-28T00:00:00Z"


def parse_rfc3339(value: str | None) -> datetime | None:
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        if "." not in v:
            raise
        head, tail = v.split(".", 1)
        tz = ""
        frac = tail
        plus = tail.find("+")
        minus = tail.find("-", 1)
        pos = min([x for x in (plus, minus) if x >= 0], default=-1)
        if pos >= 0:
            frac, tz = tail[:pos], tail[pos:]
        dt = datetime.fromisoformat(head + "." + frac[:6] + tz)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fmt_utc(dt: datetime | None) -> str:
    return "" if not dt else dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    p = urlparse(url.strip())
    scheme = (p.scheme or "https").lower()
    host = p.netloc.lower()
    path = p.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return f"{scheme}://{host}{path}"


def read_sitemap(path: Path) -> list[str]:
    if not path.exists():
        raise SystemExit(f"Sitemap not found: {path}")
    tree = ET.parse(path)
    urls = []
    for loc in tree.findall(".//sm:loc", NS):
        if loc.text and loc.text.strip():
            urls.append(loc.text.strip())
    urls = list(dict.fromkeys(urls))
    if not urls:
        raise SystemExit(f"No <loc> URLs found in sitemap: {path}")
    return urls


def google_modules():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError as exc:
        raise SystemExit(
            "Missing Google API packages.\n\nInstall once with:\n"
            "  python.exe -m pip install --upgrade "
            "google-api-python-client google-auth-httplib2 google-auth-oauthlib\n"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, HttpError


def get_credentials(client_secret: Path, token_path: Path):
    Request, Credentials, InstalledAppFlow, _, _ = google_modules()
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    if not creds or not creds.valid:
        if not client_secret.exists():
            raise SystemExit(
                "Google OAuth client secret not found.\n\n"
                f"Expected:\n  {client_secret}\n\n"
                "Create a Google Cloud Desktop OAuth client for the Search Console API,\n"
                "download the JSON file, and save it there."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def build_services(creds):
    _, _, _, build, HttpError = google_modules()
    searchconsole = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    webmasters = build("webmasters", "v3", credentials=creds, cache_discovery=False)
    return searchconsole, webmasters, HttpError


def choose_property(webmasters, requested: str | None, host: str) -> tuple[str, list[str]]:
    resp = webmasters.sites().list().execute()
    props = [x.get("siteUrl", "") for x in resp.get("siteEntry", []) if x.get("siteUrl")]

    if requested:
        if requested not in props:
            raise SystemExit(
                "Requested Search Console property is not available to this Google account:\n"
                f"  {requested}\n\nAvailable properties:\n  " + "\n  ".join(props)
            )
        return requested, props

    domain = f"sc-domain:{host}"
    if domain in props:
        return domain, props

    for candidate in (
        f"https://{host}/",
        f"https://www.{host}/",
        f"http://{host}/",
        f"http://www.{host}/",
    ):
        if candidate in props:
            return candidate, props

    raise SystemExit(
        f"No Search Console property matching {host} was found.\n\n"
        "Available properties:\n  " + "\n  ".join(props)
    )


@dataclass
class Row:
    url: str
    verdict: str
    coverage_state: str
    indexing_state: str
    robots_txt_state: str
    page_fetch_state: str
    last_crawl_time_utc: str
    days_since_crawl: str
    crawled_after_baseline: str
    user_canonical: str
    google_canonical: str
    canonical_match: str
    crawled_as: str
    sitemap_known_by_google: str
    status: str
    needs_attention: str
    inspection_link: str
    error: str


def classify(
    verdict: str,
    coverage_state: str,
    indexing_state: str,
    robots_state: str,
    fetch_state: str,
    last_crawl: datetime | None,
    baseline: datetime,
    user_canonical: str,
    google_canonical: str,
) -> tuple[str, bool]:
    coverage = (coverage_state or "").strip().lower()

    # Explicit blocking states only. UNSPECIFIED does NOT mean blocked.
    if indexing_state == "BLOCKED_BY_META_TAG":
        return "BLOCKED_NOINDEX_META", True
    if indexing_state == "BLOCKED_BY_HTTP_HEADER":
        return "BLOCKED_NOINDEX_HEADER", True
    if robots_state == "DISALLOWED":
        return "BLOCKED_BY_ROBOTS", True

    # Google's coverage-state wording is often more informative than enum fields
    # when the URL has not yet been crawled.
    if coverage == "url is unknown to google":
        return "UNKNOWN_TO_GOOGLE", True
    if coverage == "discovered - currently not indexed":
        return "DISCOVERED_NOT_CRAWLED", True
    if coverage == "crawled - currently not indexed":
        return "CRAWLED_NOT_INDEXED", True
    if coverage == "alternate page with proper canonical tag":
        return "ALTERNATE_CANONICAL", True
    if "duplicate" in coverage and "canonical" in coverage:
        return "DUPLICATE_CANONICAL", True
    if "soft 404" in coverage:
        return "SOFT_404", True
    if "not found" in coverage or coverage == "not found (404)":
        return "NOT_FOUND", True

    # Fetch state matters only when Google actually reports a concrete fetch result.
    if fetch_state and fetch_state != "PAGE_FETCH_STATE_UNSPECIFIED" and fetch_state != "SUCCESSFUL":
        return f"FETCH_{fetch_state}", True

    # A canonical mismatch is meaningful only when both canonicals are present.
    if user_canonical and google_canonical:
        if normalize_url(user_canonical) != normalize_url(google_canonical):
            return "CANONICAL_MISMATCH", True

    # PASS is the clearest successful indexed state.
    if verdict == "PASS":
        if last_crawl and last_crawl >= baseline:
            return "INDEXED_FRESH", False
        if last_crawl:
            return "INDEXED_STALE", True
        return "INDEXED_NO_CRAWL_TIMESTAMP", True

    # NEUTRAL/FAIL without a recognized coverage-state explanation.
    if verdict == "NEUTRAL":
        return "NOT_INDEXED_NEUTRAL", True
    if verdict == "FAIL":
        return "NOT_INDEXED_FAIL", True

    # No meaningful index record.
    if (
        indexing_state in {"", "INDEXING_STATE_UNSPECIFIED"}
        and robots_state in {"", "ROBOTS_TXT_STATE_UNSPECIFIED"}
        and fetch_state in {"", "PAGE_FETCH_STATE_UNSPECIFIED"}
        and not last_crawl
    ):
        return "INDEX_STATUS_UNKNOWN", True

    return f"INDEX_STATUS_{verdict or 'UNKNOWN'}", True


def inspect_url(service, site_url: str, url: str, baseline: datetime, HttpError, retries=4) -> Row:
    body = {"inspectionUrl": url, "siteUrl": site_url, "languageCode": "en-US"}
    result = {}
    error = ""

    for attempt in range(retries):
        try:
            response = service.urlInspection().index().inspect(body=body).execute()
            result = response.get("inspectionResult", {})
            break
        except HttpError as exc:
            code = getattr(exc.resp, "status", None)
            if code in {429, 500, 502, 503, 504} and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            error = f"HTTP {code}: {exc}"
            break
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            break

    idx = result.get("indexStatusResult", {}) if result else {}
    verdict = idx.get("verdict", "")
    coverage = idx.get("coverageState", "")
    indexing = idx.get("indexingState", "")
    robots = idx.get("robotsTxtState", "")
    fetch = idx.get("pageFetchState", "")
    last_dt = parse_rfc3339(idx.get("lastCrawlTime")) if idx.get("lastCrawlTime") else None

    now = datetime.now(timezone.utc)
    days = "" if not last_dt else f"{(now - last_dt).total_seconds() / 86400:.1f}"

    user_canonical = idx.get("userCanonical", "")
    google_canonical = idx.get("googleCanonical", "")
    canonical_match = ""
    if user_canonical and google_canonical:
        canonical_match = str(
            normalize_url(user_canonical) == normalize_url(google_canonical)
        ).lower()

    if error:
        status, attention = "API_ERROR", True
    else:
        status, attention = classify(
            verdict,
            coverage,
            indexing,
            robots,
            fetch,
            last_dt,
            baseline,
            user_canonical,
            google_canonical,
        )

    return Row(
        url=url,
        verdict=verdict,
        coverage_state=coverage,
        indexing_state=indexing,
        robots_txt_state=robots,
        page_fetch_state=fetch,
        last_crawl_time_utc=fmt_utc(last_dt),
        days_since_crawl=days,
        crawled_after_baseline="" if not last_dt else str(last_dt >= baseline).lower(),
        user_canonical=user_canonical,
        google_canonical=google_canonical,
        canonical_match=canonical_match,
        crawled_as=idx.get("crawledAs", ""),
        sitemap_known_by_google="true" if idx.get("sitemap") else "false",
        status=status,
        needs_attention=str(attention).lower(),
        inspection_link=result.get("inspectionResultLink", "") if result else "",
        error=error,
    )


def write_csv(path: Path, rows: list[Row]):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(Row.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(asdict(row))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(
        description="Audit every Tampa Bay Shine sitemap URL with the Google Search Console URL Inspection API."
    )
    ap.add_argument("--sitemap", default="cloudflare-site/sitemap.xml")
    ap.add_argument("--property", default=None, help="Optional Search Console property, e.g. sc-domain:tampabayshine.com")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE, help="RFC3339 timestamp or YYYY-MM-DD")
    ap.add_argument("--client-secret", default=str(Path.home() / ".tbs-gsc" / "client_secret.json"))
    ap.add_argument("--token", default=str(Path.home() / ".tbs-gsc" / "token.json"))
    ap.add_argument("--out-dir", default="reports/gsc-index-audit")
    ap.add_argument("--limit", type=int, default=0, help="Inspect only first N sitemap URLs; useful for setup testing.")
    ap.add_argument("--pause", type=float, default=0.10, help="Seconds to pause between API calls.")
    args = ap.parse_args()

    sitemap = Path(args.sitemap).resolve()
    urls = read_sitemap(sitemap)
    if args.limit > 0:
        urls = urls[:args.limit]

    host = urlparse(urls[0]).netloc.lower()
    baseline_raw = args.baseline
    if len(baseline_raw) == 10:
        baseline_raw += "T00:00:00Z"
    baseline = parse_rfc3339(baseline_raw)
    if not baseline:
        raise SystemExit("Invalid --baseline")

    creds = get_credentials(Path(args.client_secret), Path(args.token))
    searchconsole, webmasters, HttpError = build_services(creds)
    property_url, _ = choose_property(webmasters, args.property, host)

    print("TAMPA BAY SHINE GOOGLE INDEX AUDIT")
    print("==================================")
    print(f"Search Console property: {property_url}")
    print(f"Sitemap URLs to inspect: {len(urls)}")
    print(f"Freshness baseline: {fmt_utc(baseline)}")
    print("")

    rows = []
    for i, url in enumerate(urls, 1):
        row = inspect_url(searchconsole, property_url, url, baseline, HttpError)
        rows.append(row)
        crawl = row.last_crawl_time_utc or "never"
        print(f"[{i:02d}/{len(urls):02d}] {row.status:28} {crawl:22} {url}")
        if args.pause:
            time.sleep(args.pause)

    out_dir = Path(args.out_dir).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    csv_path = out_dir / f"gsc-index-status-{stamp}.csv"
    json_path = out_dir / f"gsc-index-status-{stamp}.json"

    counts = Counter(r.status for r in rows)
    indexed = sum(1 for r in rows if r.verdict == "PASS")
    stale = sum(1 for r in rows if r.status == "INDEXED_STALE")
    fresh = sum(1 for r in rows if r.status == "INDEXED_FRESH")
    unknown = sum(1 for r in rows if r.status == "UNKNOWN_TO_GOOGLE")
    discovered = sum(1 for r in rows if r.status == "DISCOVERED_NOT_CRAWLED")
    crawled_not_indexed = sum(1 for r in rows if r.status == "CRAWLED_NOT_INDEXED")
    alternate = sum(1 for r in rows if r.status == "ALTERNATE_CANONICAL")
    canon = sum(1 for r in rows if r.status == "CANONICAL_MISMATCH")
    fetch_errors = sum(1 for r in rows if r.status.startswith("FETCH_") or r.status == "API_ERROR")
    blocked = sum(1 for r in rows if r.status.startswith("BLOCKED_"))
    attention = sum(1 for r in rows if r.needs_attention == "true")

    payload = {
        "generated_at_utc": fmt_utc(datetime.now(timezone.utc)),
        "search_console_property": property_url,
        "sitemap": str(sitemap),
        "baseline_utc": fmt_utc(baseline),
        "summary": {
            "urls_checked": len(rows),
            "indexed_pass": indexed,
            "indexed_fresh": fresh,
            "indexed_stale": stale,
            "unknown_to_google": unknown,
            "discovered_not_crawled": discovered,
            "crawled_not_indexed": crawled_not_indexed,
            "alternate_canonical": alternate,
            "actual_index_blocks": blocked,
            "canonical_mismatches": canon,
            "fetch_or_api_errors": fetch_errors,
            "needs_attention": attention,
            "status_counts": dict(sorted(counts.items())),
        },
        "rows": [asdict(r) for r in rows],
    }

    write_csv(csv_path, rows)
    write_json(json_path, payload)

    print("")
    print("SUMMARY")
    print("-------")
    print(f"URLs checked:                 {len(rows)}")
    print(f"Indexed (PASS):               {indexed}")
    print(f"Indexed + crawled after base: {fresh}")
    print(f"Indexed but crawl predates:   {stale}")
    print(f"Unknown to Google:            {unknown}")
    print(f"Discovered, not crawled:      {discovered}")
    print(f"Crawled, not indexed:         {crawled_not_indexed}")
    print(f"Alternate canonical:          {alternate}")
    print(f"Actual index blocks:          {blocked}")
    print(f"Canonical mismatches:         {canon}")
    print(f"Fetch/API errors:             {fetch_errors}")
    print(f"Needs attention:              {attention}")
    print("")
    print(f"CSV:  {csv_path}")
    print(f"JSON: {json_path}")
    print("")
    print("NOTE: URL Inspection API reports Google's indexed-version data. It is not a live URL test.")

if __name__ == "__main__":
    main()
