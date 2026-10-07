from __future__ import annotations
import argparse,csv,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DASH=ROOT/"cloudflare-site"/"seo-dashboard"/"data"

def write(path,payload):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); print(f"Wrote {path}")

def rankings(src,out):
    grouped={}
    with src.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            q=(r.get("query") or "").strip().lower()
            if not q: continue
            try: p=int(float(r.get("position") or ""))
            except ValueError: continue
            grouped.setdefault(q,[]).append({"position":p,"domain":(r.get("domain") or "").strip(),
                                             "url":(r.get("url") or "").strip() or None,"title":(r.get("title") or "").strip() or None})
    write(out,{"schema_version":1,"observed_at":datetime.now(timezone.utc).isoformat(),"source":"manual/free SERP observation import",
               "queries":[{"query":q,"results":sorted(v,key=lambda x:x["position"])} for q,v in sorted(grouped.items())]})

def authority(src,out):
    fields=["moz_da","ahrefs_dr","semrush_authority","referring_domains","backlinks","organic_keywords","organic_traffic"]; rows=[]
    with src.open("r",encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            d=(r.get("domain") or "").strip()
            if not d: continue
            x={"domain":d}
            for k in fields:
                raw=(r.get(k) or "").strip()
                if not raw: x[k]=None
                else:
                    try:x[k]=float(raw)
                    except ValueError:x[k]=raw
            rows.append(x)
    write(out,{"schema_version":1,"observed_at":datetime.now(timezone.utc).isoformat(),"source":"manual/free authority-tool import","domains":rows})

def main():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
    r=sp.add_parser("rankings"); r.add_argument("csv",type=Path); r.add_argument("--out",type=Path,default=DASH/"competitor-rankings.json")
    a=sp.add_parser("authority"); a.add_argument("csv",type=Path); a.add_argument("--out",type=Path,default=DASH/"competitor-authority.json")
    x=p.parse_args(); rankings(x.csv,x.out) if x.cmd=="rankings" else authority(x.csv,x.out)
if __name__=="__main__":main()
