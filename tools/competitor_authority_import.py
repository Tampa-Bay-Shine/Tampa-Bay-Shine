from __future__ import annotations
import argparse, csv, json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "site-management" / "competitor-authority-template.csv"
DEFAULT_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "competitor-authority.json"
METRICS = ("moz_da","ahrefs_dr","semrush_authority","referring_domains","backlinks","organic_keywords","organic_traffic")

def norm_domain(value):
    value=(value or "").strip().lower()
    if not value: return ""
    if "://" in value: value=urlparse(value).netloc
    return value.split(":")[0].removeprefix("www.").strip(".")

def number(value):
    if value is None: return None
    s=str(value).strip().replace(",","")
    if not s: return None
    try: n=float(s)
    except ValueError as exc: raise ValueError(f"Not a number: {value!r}") from exc
    return int(n) if n.is_integer() else n

def main():
    p=argparse.ArgumentParser(description="Import manually collected competitor authority/backlink observations.")
    p.add_argument("csv_file", nargs="?", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--allow-partial", action="store_true")
    a=p.parse_args()
    if not a.csv_file.exists(): raise SystemExit(f"CSV not found: {a.csv_file}")
    rows=[]; populated=0; sources=set(); observed=[]
    with a.csv_file.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not reader.fieldnames or "domain" not in reader.fieldnames:
            raise SystemExit("CSV must contain a domain column.")
        for line_no,raw in enumerate(reader,start=2):
            domain=norm_domain(raw.get("domain"))
            if not domain: continue
            row={"domain":domain}
            for k in METRICS:
                try: row[k]=number(raw.get(k))
                except ValueError as exc: raise SystemExit(f"{a.csv_file}:{line_no}: {k}: {exc}") from exc
            row["group"]=(raw.get("group") or "").strip() or None
            row["source"]=(raw.get("source") or "").strip() or None
            row["observed_at"]=(raw.get("observed_at") or "").strip() or None
            row["notes"]=(raw.get("notes") or "").strip() or None
            if any(row[k] is not None for k in METRICS): populated+=1
            if row["source"]: sources.add(row["source"])
            if row["observed_at"]: observed.append(row["observed_at"])
            rows.append(row)
    if not rows: raise SystemExit("No domain rows found in CSV.")
    if populated==0 and not a.allow_partial:
        raise SystemExit("No authority/backlink metrics were populated. Fill at least one metric or use --allow-partial.")
    payload={
        "schema_version":2,
        "observed_at": max(observed) if observed else datetime.now(timezone.utc).isoformat(),
        "source":"; ".join(sorted(sources)) if sources else "manual/free authority-tool import",
        "domains":rows,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(f"Imported authority rows: {len(rows)}")
    print(f"Rows with at least one metric: {populated}")
    print(f"Wrote: {a.out}")
    print(r"Run next: python.exe .\tools\competitor_intelligence.py")
if __name__=="__main__": main()
