from __future__ import annotations
from pathlib import Path
from datetime import date, datetime, timedelta
import json, math, re

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"
CONFIG=ROOT/"config"/"seo-core-search.json"
OUT=DATA/"decision-intelligence.json"

def loadp(p, default=None):
    if not p.exists(): return {} if default is None else default
    return json.loads(p.read_text(encoding="utf-8-sig"))
def load(n,d=None): return loadp(DATA/n,d)

def norm(s): return " ".join(str(s or "").lower().strip().split())
def synthetic(q):
    t=norm(q); ops=sum(t.count(x) for x in (" or "," and ")); quotes=t.count('"')//2; parens="(" in t and ")" in t
    return bool(t) and ((parens and ops>=2 and quotes>=1) or (ops>=4 and quotes>=2) or (len(t)>=180 and ops>=2))

def collect_strings(obj, key_hint=""):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            lk=k.lower()
            if isinstance(v,str) and ("quer" in lk or "keyword" in lk): out.append(v)
            else: out += collect_strings(v,lk)
    elif isinstance(obj,list):
        for v in obj: out += collect_strings(v,key_hint)
    return out

cfg=loadp(CONFIG,{})
core20=[]
for q in collect_strings(cfg):
    nq=norm(q)
    if nq and nq not in core20: core20.append(nq)
# Prefer explicit fixed portfolio if config contains more incidental strings.
known=[
"house cleaning tampa","house cleaning services tampa","maid service tampa","house cleaning near me","cleaning services near me",
"deep cleaning tampa","move out cleaning tampa","move in cleaning tampa","apartment cleaning tampa","airbnb cleaning service tampa",
"office cleaning tampa","office cleaning service near me","commercial cleaning tampa","medical office cleaning tampa","medical office cleaning",
"commercial cleaning brandon fl","office cleaning brandon fl","office cleaning riverview fl","commercial cleaning riverview fl","janitorial services brandon fl"]
if not all(x in core20 for x in known): core20=known
else: core20=[x for x in core20 if x in known]

strategic_tokens=("house cleaning","cleaning services","maid service","deep cleaning","move out cleaning","move in cleaning",
                  "apartment cleaning","airbnb cleaning","office cleaning","commercial cleaning","medical office cleaning",
                  "janitorial","brandon","riverview","ruskin","sun city center","tampa","wesley chapel")
adjacent_tokens=("bathroom cleaning","amenity center","property management","floor maintenance","fitness center","condo common area")

def relevance(q):
    n=norm(q)
    if n in core20:return ("core20",3)
    if any(t in n for t in strategic_tokens) and not any(a in n for a in adjacent_tokens):return ("strategic",2)
    return ("discovered",1)

def unpack(obj,kind):
    out=[]
    for row in obj.get(kind,[]) if isinstance(obj,dict) else []:
        if not isinstance(row,dict):continue
        name=row.get("query") if kind=="queries" else row.get("page")
        name=name or row.get("name") or row.get("key"); pts=[]
        for p in row.get("points",[]):
            try:
                if isinstance(p,list) and len(p)>=5:d,c,i,ctr,pos=p[:5]
                elif isinstance(p,dict):d=p.get("date");c=p.get("clicks",0);i=p.get("impressions",0);pos=p.get("position")
                else:continue
                if d:pts.append({"date":str(d),"clicks":float(c or 0),"impressions":float(i or 0),"position":float(pos) if pos is not None else None})
            except Exception: pass
        if name and pts:out.append((str(name),pts))
    return out

def agg(pts,s,e):
    a=[p for p in pts if s<=p["date"]<=e]; imp=sum(x["impressions"] for x in a); clicks=sum(x["clicks"] for x in a)
    pi=sum(x["impressions"] for x in a if x["position"] is not None); pn=sum(x["impressions"]*x["position"] for x in a if x["position"] is not None)
    return {"clicks":round(clicks,2),"impressions":round(imp,2),"ctr":round(clicks/imp,6) if imp else 0,
            "position":round(pn/pi,2) if pi else None,"observed_days":len(a)}
def compare(pts,end,n=28):
    e=date.fromisoformat(end); cs=e-timedelta(days=n-1); pe=cs-timedelta(days=1); ps=pe-timedelta(days=n-1)
    return agg(pts,cs.isoformat(),e.isoformat()),agg(pts,ps.isoformat(),pe.isoformat())
def conf(c):
    if c["impressions"]>=30 and c["observed_days"]>=10:return "high"
    if c["impressions"]>=10 and c["observed_days"]>=5:return "medium"
    return "low"
def pct(a,b):return None if not b else round((a-b)/b*100,1)

qh=load("query-history.json"); ph=load("page-history.json")
queries=unpack(qh,"queries"); pages=unpack(ph,"pages")
dates=[p["date"] for _,pts in queries+pages for p in pts]
if not dates:raise SystemExit("No history")
end=max(dates); signals=[]

def emit(typ,subject,c,p,priority,evidence,action,rel="page",rw=2):
    pd=round(p["position"]-c["position"],2) if p["position"] is not None and c["position"] is not None else None
    signals.append({"type":typ,"subject":subject,"priority":priority,"confidence":conf(c),"relevance":rel,
      "metrics":{"position":c["position"],"impressions":c["impressions"],"clicks":c["clicks"],"ctr_percent":round(c["ctr"]*100,2),
                 "observed_days":c["observed_days"],"position_improvement":pd,"impressions_change_pct":pct(c["impressions"],p["impressions"])},
      "evidence":evidence,"recommended_action":action,"relevance_weight":rw})

for q,pts in queries:
    if synthetic(q):continue
    c,p=compare(pts,end); cf=conf(c); pos=c["position"]
    if cf=="low" or pos is None:continue
    rel,rw=relevance(q); pd=(p["position"]-pos) if p["position"] is not None else None
    # Strategic queue is stricter for discovered queries.
    minimp=10 if rw>=2 else 30
    if 4<=pos<=20 and c["impressions"]>=minimp:
        pri="high" if (rw==3 and pos<=15 and c["impressions"]>=20) or (rw>=2 and pos<=12 and c["impressions"]>=30) else "medium"
        emit("striking_distance",q,c,p,pri,f"Average position {pos:.1f} on {c['impressions']:.0f} impressions in the current 28-day window.",
             "Strengthen the existing ranking page for this intent: snippet alignment, on-page coverage, proof, and relevant internal links. Do not create an overlapping URL.",rel,rw)
    if pos<=15 and c["impressions"]>=30 and c["ctr"]<0.01 and rw>=2:
        emit("ctr_gap",q,c,p,"high" if pos<=10 and c["impressions"]>=50 else "medium",
             f"{c['impressions']:.0f} impressions at position {pos:.1f} with {c['ctr']*100:.2f}% CTR.",
             "Review search-snippet and intent alignment; improve title/meta messaging and page relevance before expanding scope.",rel,rw)
    if pd is not None and abs(pd)>=5 and c["impressions"]>=20 and p["impressions"]>=10:
        typ="ranking_momentum" if pd>0 else "ranking_decline"
        pri="medium" if pd>0 else ("high" if c["impressions"]>=50 and rw>=2 else "medium")
        emit(typ,q,c,p,pri,
             f"Average position {'improved' if pd>0 else 'declined'} {abs(pd):.1f} places versus the previous 28-day window.",
             "Protect the gain and verify the intended page is ranking." if pd>0 else "Inspect query-to-page alignment, recent SEO events, competing pages, and snippet/content changes before a targeted correction.",rel,rw)

for page,pts in pages:
    c,p=compare(pts,end)
    if conf(c)=="low":continue
    ic=pct(c["impressions"],p["impressions"]); pd=(p["position"]-c["position"]) if p["position"] is not None and c["position"] is not None else None
    if p["impressions"]>=30 and ic is not None and ic<=-30 and (pd is None or pd<=-3):
        emit("page_decay",page,c,p,"high" if p["impressions"]>=100 else "medium",
             f"Impressions declined {abs(ic):.1f}% and ranking did not improve enough to offset the loss.",
             "Review recent page changes, indexing/canonical status, internal links, and previously visible queries. Avoid creating a replacement page.","core_page",3)

tw={"ranking_decline":6,"page_decay":6,"ctr_gap":5,"striking_distance":4,"ranking_momentum":2}; pw={"high":3,"medium":2}
for x in signals:
    m=x["metrics"]; x["score"]=round(pw[x["priority"]]*20+x["relevance_weight"]*15+tw[x["type"]]*5+min(20,math.log10(max(1,m["impressions"]))*8),1)

# Consolidate query/page signals: one management action, retain all reasons.
groups={}
for x in signals:
    k=norm(x["subject"]); groups.setdefault(k,[]).append(x)
items=[]
for k,arr in groups.items():
    arr=sorted(arr,key=lambda z:-z["score"]); best=dict(arr[0])
    best["signals"]=[{"type":a["type"],"evidence":a["evidence"]} for a in arr]
    best["signal_count"]=len(arr)
    if len(arr)>1:
        best["evidence"]=" ".join(a["evidence"] for a in arr[:2])
    best["score"]=round(max(a["score"] for a in arr)+min(10,(len(arr)-1)*3),1)
    items.append(best)

# PHASE_5_2_MANAGEMENT_DECAY_GATE:
def _p52_keep_management_action(x):
    signal_types={str(s.get("type","")) for s in x.get("signals",[]) if isinstance(s,dict)}
    if "page_decay" not in signal_types:
        return True
    m=x.get("metrics") or {}
    imp=float(m.get("impressions") or 0)
    pos=float(m.get("position") or 999)
    return imp>=25 or (imp>=20 and pos<=30)

items=[x for x in items if _p52_keep_management_action(x)]
items.sort(key=lambda z:(-z["score"],z["subject"].lower()))

summary={"qualifying_signals":len(signals),"consolidated_actions":len(items),
 "high":sum(x["priority"]=="high" for x in items),
 "core20":sum(x["relevance"]=="core20" for x in items),
 "strategic":sum(x["relevance"] in ("strategic","core_page") for x in items),
 "discovered":sum(x["relevance"]=="discovered" for x in items),
 "striking_distance":sum(any(s["type"]=="striking_distance" for s in x["signals"]) for x in items),
 "ctr_gaps":sum(any(s["type"]=="ctr_gap" for s in x["signals"]) for x in items),
 "declines":sum(any(s["type"] in ("ranking_decline","page_decay") for s in x["signals"]) for x in items),
 "positive_momentum":sum(any(s["type"]=="ranking_momentum" for s in x["signals"]) for x in items)}
out={"schema_version":2,"generated_at":datetime.now().astimezone().isoformat(),"data_through":end,
 "methodology":{"comparison":"current 28 days vs previous 28 days","executive_default":"top 12 consolidated actions",
 "business_relevance":"Core 20 > strategic service/location intent > discovered queries","synthetic_queries":"excluded",
 "low_confidence":"excluded","indexing":"live GSC inspection/index coverage not yet wired"},
 "summary":summary,"items":items}
OUT.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("Decision Intelligence v2 through",end);print("Summary:",summary);print("Top 12:",[(x["subject"],x["priority"],x["relevance"],x["score"]) for x in items[:12]]);print("Wrote:",OUT)
