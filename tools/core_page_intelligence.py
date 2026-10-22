from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"
OUT=DATA/"core-pages.json"

# Fixed strategic cohort. Membership changes only by explicit rebaseline.
CORE_PAGES=[
 {"path":"/","label":"Homepage","intent":"brand / broad residential"},
 {"path":"/services/","label":"Services Hub","intent":"service discovery"},
 {"path":"/standard-cleaning-services-tampa/","label":"Standard Cleaning","intent":"recurring / house cleaning"},
 {"path":"/deep-cleaning-services-tampa/","label":"Deep Cleaning","intent":"deep cleaning"},
 {"path":"/move-out-cleaning-tampa/","label":"Move Out / Move In Cleaning","intent":"move cleaning"},
 {"path":"/apartment-cleaning-tampa/","label":"Apartment Cleaning","intent":"apartment cleaning"},
 {"path":"/airbnb-cleaning-services/","label":"Airbnb Cleaning","intent":"short-term rental cleaning"},
 {"path":"/office-cleaning/","label":"Office Cleaning","intent":"office cleaning"},
 {"path":"/commercial-cleaning-tampa/","label":"Commercial Cleaning","intent":"commercial cleaning"},
 {"path":"/medical-office-cleaning-tampa/","label":"Medical Office Cleaning","intent":"medical office cleaning"},
 {"path":"/locations/","label":"Locations Hub","intent":"local service areas"},
 {"path":"/house-cleaning-brandon-fl/","label":"Brandon House Cleaning","intent":"Brandon residential"},
 {"path":"/house-cleaning-riverview-fl/","label":"Riverview House Cleaning","intent":"Riverview residential"},
 {"path":"/house-cleaning-sun-city-center-fl/","label":"Sun City Center House Cleaning","intent":"Sun City Center residential"},
 {"path":"/house-cleaning-ruskin-fl/","label":"Ruskin House Cleaning","intent":"Ruskin residential"},
]

def load(p): return json.loads(p.read_text(encoding="utf-8-sig"))

def norm(v):
 s=str(v or "").strip()
 if not s:return "/"
 if s.startswith(("http://","https://")):s=urlparse(s).path or "/"
 s=s.split("?",1)[0].split("#",1)[0]
 if not s.startswith("/"):s="/"+s
 if s!="/" and not s.endswith("/"):s+="/"
 return s.lower()

def parse(d):
 out={}
 for row in d.get("pages",[]):
  key=norm(row.get("page") or row.get("path") or row.get("url"))
  dest=out.setdefault(key,{"points_by_date":{}})
  for p in row.get("points",[]):
   if not isinstance(p,list) or len(p)<5:continue
   day,clicks,impr,_ctr,pos=p[:5]
   clicks=float(clicks or 0); impr=float(impr or 0); pos=float(pos) if pos is not None else None
   x=dest["points_by_date"].setdefault(str(day),{"date":str(day),"clicks":0.0,"impressions":0.0,"weighted":0.0})
   x["clicks"]+=clicks;x["impressions"]+=impr
   if pos is not None:x["weighted"]+=pos*impr
 final={}
 for key,v in out.items():
  pts=[]
  for day,x in sorted(v["points_by_date"].items()):
   pts.append({"date":day,"clicks":x["clicks"],"impressions":x["impressions"],
               "position":x["weighted"]/x["impressions"] if x["impressions"] else None})
  final[key]={"points":pts}
 return final

def agg(points,start,end):
 rows=[p for p in points if start<=p["date"]<=end]
 c=sum(p["clicks"] for p in rows);i=sum(p["impressions"] for p in rows)
 w=sum(p["position"]*p["impressions"] for p in rows if p["position"] is not None)
 return {"clicks":round(c,2),"impressions":round(i,2),"ctr":round(c/i*100,2) if i else 0,
         "position":round(w/i,2) if i else None,"observed_days":len(rows)}

def delta(c,p):
 pct=lambda a,b:None if not b else round((a-b)/b*100,2)
 return {"clicks":round(c["clicks"]-p["clicks"],2),"clicks_pct":pct(c["clicks"],p["clicks"]),
         "impressions":round(c["impressions"]-p["impressions"],2),"impressions_pct":pct(c["impressions"],p["impressions"]),
         "ctr_points":round(c["ctr"]-p["ctr"],2),
         "position":round(p["position"]-c["position"],2) if p["position"] is not None and c["position"] is not None else None}

def compare(points,end_s,n):
 e=date.fromisoformat(end_s);cs=e-timedelta(days=n-1);pe=cs-timedelta(days=1);ps=pe-timedelta(days=n-1)
 c=agg(points,cs.isoformat(),e.isoformat());p=agg(points,ps.isoformat(),pe.isoformat())
 return {"current":c,"previous":p,"change":delta(c,p),
         "range":{"current":[cs.isoformat(),e.isoformat()],"previous":[ps.isoformat(),pe.isoformat()]}}

def confidence(m):
 if m["impressions"]>=100 and m["observed_days"]>=14:return "high"
 if m["impressions"]>=30 and m["observed_days"]>=7:return "medium"
 return "low"

def momentum(c,p):
 conf=confidence(c)
 if not c["impressions"]:return "no_visibility"
 if not p["impressions"]:return "new_visibility" if c["impressions"]>=30 else "low_sample"
 if conf=="low":return "low_sample"
 imp=(c["impressions"]-p["impressions"])/p["impressions"]*100
 pos=(p["position"]-c["position"]) if p["position"] is not None and c["position"] is not None else 0
 if (imp<=-35 and c["impressions"]<=p["impressions"]-20) or (pos<=-5 and p["impressions"]>=30):return "needs_attention"
 if (imp>=30 and c["impressions"]>=p["impressions"]+20) or pos>=5:return "improving"
 return "stable"

def main():
 raw=load(DATA/"page-history.json");series=parse(raw);end=raw.get("period",{}).get("end")
 if not end:raise SystemExit("page-history.json missing period.end")
 rows=[];counts={k:0 for k in ("improving","stable","needs_attention","new_visibility","low_sample","no_visibility")}
 confs={k:0 for k in ("high","medium","low")}
 for spec in CORE_PAGES:
  pts=series.get(norm(spec["path"]),{}).get("points",[])
  periods={str(n):compare(pts,end,n) for n in (7,28,90)}
  c=periods["28"]["current"];p=periods["28"]["previous"];conf=confidence(c);state=momentum(c,p)
  confs[conf]+=1;counts[state]+=1
  rows.append({**spec,"path":norm(spec["path"]),"confidence":conf,"momentum":state,"periods":periods})
 reliable=sum(r["confidence"] in ("high","medium") for r in rows)
 positive=counts["improving"]+counts["new_visibility"]
 status="needs_attention" if counts["needs_attention"]>=4 else ("improving" if positive>counts["needs_attention"] else "stable")
 out={"schema_version":2,"generated_at":datetime.now().astimezone().isoformat(),"data_through":end,
      "source":"Google Search Console retained daily page history",
      "methodology":{"membership":"Fixed strategic landing-page cohort; changes require explicit rebaseline.",
       "canonicalization":"Absolute URLs, query strings, fragments, and trailing-slash aliases normalize to one canonical path.",
       "position":"Impression-weighted average GSC position.","missing_dates":"Missing page/date observations are not treated as zero.",
       "confidence":{"high":"At least 100 impressions across 14 observed days in current 28d.",
                     "medium":"At least 30 impressions across 7 observed days in current 28d.",
                     "low":"Below medium evidence threshold."}},
      "executive":{"overall_status":status,"page_count":len(rows),"reliable_pages":reliable,"confidence":confs,"momentum":counts},
      "pages":rows}
 OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
 print(f"Wrote {OUT.relative_to(ROOT)} through {end}")
if __name__=="__main__":main()
