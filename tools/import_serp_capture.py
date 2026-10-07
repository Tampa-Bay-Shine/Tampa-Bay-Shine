from __future__ import annotations
import argparse, json, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "competitor-rankings.json"
DEFAULT_HISTORY = ROOT / "cloudflare-site" / "seo-dashboard" / "data" / "competitor-rankings-history.json"

def load(path, default):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:return default

def main():
    p=argparse.ArgumentParser(description="Import TBS Chrome SERP Capture export.")
    p.add_argument("json_file",type=Path)
    p.add_argument("--out",type=Path,default=DEFAULT_OUT)
    p.add_argument("--history",type=Path,default=DEFAULT_HISTORY)
    a=p.parse_args()

    data=json.loads(a.json_file.read_text(encoding="utf-8"))
    if not isinstance(data.get("queries"),list):
        raise SystemExit("Invalid export: queries[] missing.")
    for row in data["queries"]:
        if not row.get("query") or not isinstance(row.get("results"),list):
            raise SystemExit("Invalid export: malformed query row.")
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if a.out.exists():
        stamp=datetime.now().strftime("%Y%m%d-%H%M%S")
        shutil.copy2(a.out,a.out.with_name(f"competitor-rankings.pre-import-{stamp}.json"))
    a.out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")

    history=load(a.history,{"schema_version":1,"snapshots":[]})
    history.setdefault("snapshots",[]).append(data)
    history["snapshots"]=history["snapshots"][-52:]
    a.history.write_text(json.dumps(history,indent=2)+"\n",encoding="utf-8")

    print(f"Imported {len(data['queries'])} SERP queries")
    print(f"Wrote: {a.out}")
    print(f"History: {a.history}")
    print()
    print("Next:")
    print(r"python.exe .\tools\competitor_intelligence.py")

if __name__=="__main__":main()
