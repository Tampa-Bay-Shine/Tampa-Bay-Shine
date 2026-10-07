from __future__ import annotations

import argparse, json, math
from datetime import datetime, timezone, date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "cloudflare-site" / "seo-dashboard" / "data"
DEFAULT_CONFIG = DASH / "competitor-config.json"
DEFAULT_RANKINGS = DASH / "competitor-rankings.json"
DEFAULT_AUTHORITY = DASH / "competitor-authority.json"
DEFAULT_GSC = DASH / "gsc.json"
DEFAULT_EVENTS = DASH / "events.json"
DEFAULT_OUT = DASH / "competitor-intelligence.json"
VISIBILITY_WEIGHTS = {1:30,2:18,3:12,4:8,5:6,6:5,7:4,8:3,9:2,10:1}

def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

def norm_domain(v):
    v=(v or "").strip().lower()
    if not v: return ""
    if "://" in v: v=urlparse(v).netloc
    return v.split(":")[0].removeprefix("www.").strip(".")

def num(v, default=None):
    if v in (None,""): return default
    try: return float(v)
    except (TypeError,ValueError): return default

def clamp(v, lo=0, hi=100): return max(lo,min(hi,v))

def pos_points(p):
    if p is None: return 0
    p=float(p)
    if p<=3: return 30
    if p<=10: return 26-((p-4)/6)*8
    if p<=20: return 18-((p-11)/9)*8
    if p<=50: return max(2,10-((p-21)/29)*8)
    return 0

def confidence(impr):
    return "high" if impr>=50 else "medium" if impr>=20 else "low"

def gsc_index(gsc):
    out={}
    for x in gsc.get("tracked_keywords",[]):
        q=str(x.get("query") or "").strip().lower()
        if q:
            cur=x.get("current") or {}
            out[q]={"position":num(cur.get("position")),"impressions":num(cur.get("impressions"),0) or 0,
                    "clicks":num(cur.get("clicks"),0) or 0,"position_change":num(x.get("position_change")),
                    "page":x.get("ranking_page"),"source":"gsc_tracked"}
    for x in gsc.get("top_queries",[]):
        q=str(x.get("query") or "").strip().lower()
        if q and q not in out:
            out[q]={"position":num(x.get("current_position")),"impressions":num(x.get("current_impressions"),0) or 0,
                    "clicks":num(x.get("current_clicks"),0) or 0,"position_change":num(x.get("position_improvement")),
                    "page":None,"source":"gsc_top_query"}
    return out

def rankings_index(data):
    out={}
    for row in data.get("queries",[]):
        q=str(row.get("query") or "").strip().lower()
        if not q: continue
        clean=[]
        for r in row.get("results",[]):
            p=num(r.get("position")); d=norm_domain(r.get("domain") or r.get("url"))
            if p is None or not d: continue
            clean.append({"position":int(p),"domain":d,"url":r.get("url"),"title":r.get("title")})
        out[q]=sorted(clean,key=lambda z:z["position"])
    return out

def authority_index(data):
    return {norm_domain(x.get("domain")):x for x in data.get("domains",[]) if norm_domain(x.get("domain"))}

def authority_strength(row):
    if not row: return None
    vals=[num(row.get(k)) for k in ("ahrefs_dr","moz_da","semrush_authority")]
    vals=[v for v in vals if v is not None]
    refs=num(row.get("referring_domains"))
    base=sum(vals)/len(vals) if vals else None
    if base is None and refs is None: return None
    if base is None: return min(100,math.log10(max(refs,1)+1)*25)
    if refs is None: return base
    return .75*base+.25*min(100,math.log10(max(refs,1)+1)*25)

def guard(query,page,events,days):
    today=date.today(); q=(query or "").lower(); p=(page or "").rstrip("/").lower()
    for e in events.get("events",[]):
        try: d=datetime.strptime(str(e.get("date")),"%Y-%m-%d").date()
        except Exception: continue
        age=(today-d).days
        if age<0 or age>days: continue
        hay=" ".join([str(e.get("title") or ""),str(e.get("description") or ""),str(e.get("notes") or ""),
                      " ".join(str(x) for x in e.get("urls",[]))]).lower()
        if (q and q in hay) or (p and p in hay):
            return {"guarded":True,"event_date":d.isoformat(),"event_title":e.get("title"),"age_days":age,
                    "reason":f"Recent logged SEO change ({age} days ago). Hold major page changes until the {days}-day stabilization window passes."}
    return {"guarded":False}

def build(config,rankings,authority,gsc,events):
    primary=norm_domain(config.get("primary_domain") or "tampabayshine.com")
    stab=int(config.get("stabilization_days",14))
    gi=gsc_index(gsc); ri=rankings_index(rankings); ai=authority_index(authority)
    kw=config.get("keywords") or [{"query":q,"commercial_weight":1} for q in gi]
    lb={}; battle=[]
    for item in kw:
        q=str(item.get("query") or "").strip().lower()
        if not q: continue
        w=float(item.get("commercial_weight",1) or 1)
        results=ri.get(q,[]); g=gi.get(q,{})
        own=next((x for x in results if x["domain"]==primary),None)
        pos=own["position"] if own else g.get("position")
        src="serp_observation" if own else ("gsc_average_position" if g else "unavailable")
        page=(own or {}).get("url") or g.get("page")
        impr=float(g.get("impressions",0) or 0)
        for r in results:
            pts=VISIBILITY_WEIGHTS.get(r["position"],0)*w
            if not pts: continue
            z=lb.setdefault(r["domain"],{"visibility_points":0,"keywords":set(),"top3":0,"top10":0})
            z["visibility_points"]+=pts; z["keywords"].add(q)
            if r["position"]<=3: z["top3"]+=1
            if r["position"]<=10: z["top10"]+=1
        comp=next((x for x in results if x["domain"]!=primary),None)
        weakness=7.5
        if comp:
            a=authority_strength(ai.get(primary)); b=authority_strength(ai.get(comp["domain"]))
            if a is not None and b is not None: weakness=clamp(7.5+(a-b)*.3,0,15)
        impr_score=clamp(math.log10(impr+1)/math.log10(101)*25 if impr else 0,0,25)
        gap=0
        if results and pos is not None: gap=clamp((float(pos)-float(results[0]["position"]))/20*20,0,20)
        score=round(pos_points(pos)+impr_score+weakness+clamp(w*10,0,10)+gap,1)
        gstate=guard(q,page,events,stab)
        action="Insufficient competitor SERP data"
        if results and pos is not None:
            if gstate["guarded"]: action="Hold major changes; measure during stabilization window"
            elif 4<=float(pos)<=20 and impr>=10: action="High-value page-one / page-two opportunity"
            elif float(pos)>20 and impr>=20: action="Build relevance and internal-link support"
            elif float(pos)<=3: action="Protect ranking; avoid unnecessary edits"
            else: action="Monitor"
        battle.append({"query":q,"tbs_position":round(float(pos),2) if pos is not None else None,
                       "tbs_position_source":src,"tbs_page":page,"gsc_impressions":round(impr,2),
                       "gsc_clicks":round(float(g.get("clicks",0) or 0),2),"gsc_position_change":g.get("position_change"),
                       "confidence":confidence(impr),"top_competitor":comp,"opportunity_score":score,
                       "stabilization":gstate,"recommended_action":action})
    total=sum(v["visibility_points"] for v in lb.values())
    leaderboard=[]
    for d,v in lb.items():
        leaderboard.append({"domain":d,"visibility_points":round(v["visibility_points"],2),
                            "share_of_observed_visibility":round(v["visibility_points"]/total*100,2) if total else None,
                            "keywords_overlapping":len(v["keywords"]),"top3":v["top3"],"top10":v["top10"],
                            "authority":ai.get(d)})
    leaderboard.sort(key=lambda x:x["visibility_points"],reverse=True)
    own=next((x for x in leaderboard if x["domain"]==primary),None); leader=leaderboard[0] if leaderboard else None
    share=own.get("share_of_observed_visibility") if own else None
    gap=None
    if share is not None and leader: gap=0 if leader["domain"]==primary else round((leader.get("share_of_observed_visibility") or 0)-share,2)
    observed=sum(1 for x in kw if str(x.get("query") or "").strip().lower() in ri)
    top10=sum(1 for x in battle if x["tbs_position_source"]=="serp_observation" and x["tbs_position"] is not None and x["tbs_position"]<=10)
    top3=sum(1 for x in battle if x["tbs_position_source"]=="serp_observation" and x["tbs_position"] is not None and x["tbs_position"]<=3)
    battle.sort(key=lambda x:(x["opportunity_score"],x["gsc_impressions"]),reverse=True)
    return {"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"primary_domain":primary,
            "source_status":{"gsc_generated_at":gsc.get("generated_at"),"serp_observed_at":rankings.get("observed_at"),
                             "authority_observed_at":authority.get("observed_at"),"serp_queries_observed":observed,
                             "tracked_keywords":len(kw),"note":"Missing competitor metrics remain null; no external rankings, DA/DR, backlinks, traffic, or search volume are fabricated."},
            "summary":{"tracked_keywords":len(kw),"serp_queries_observed":observed,"tbs_top10":top10 if observed else None,
                       "tbs_top3":top3 if observed else None,"tbs_visibility_share":share,"leader_gap_points":gap,"stabilization_days":stab},
            "leaderboard":leaderboard,"keyword_battle":battle,"authority":authority.get("domains",[]),
            "methodology":{"visibility_weights":VISIBILITY_WEIGHTS,
                           "opportunity_score_components":{"ranking_proximity":30,"gsc_impressions":25,"competitor_weakness":15,"commercial_intent":10,"visibility_gap":20},
                           "important":["Vendor authority metrics stay separate.","GSC position is a labeled TBS-only fallback.","Share of visibility uses supplied SERP observations only.","Recent SEO events trigger the stabilization hold."]}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config",type=Path,default=DEFAULT_CONFIG); p.add_argument("--rankings",type=Path,default=DEFAULT_RANKINGS)
    p.add_argument("--authority",type=Path,default=DEFAULT_AUTHORITY); p.add_argument("--gsc",type=Path,default=DEFAULT_GSC)
    p.add_argument("--events",type=Path,default=DEFAULT_EVENTS); p.add_argument("--out",type=Path,default=DEFAULT_OUT)
    a=p.parse_args()
    result=build(load_json(a.config,{}),load_json(a.rankings,{"queries":[]}),load_json(a.authority,{"domains":[]}),
                 load_json(a.gsc,{}),load_json(a.events,{"events":[]}))
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Competitor Intelligence: {result['summary']['serp_queries_observed']}/{result['summary']['tracked_keywords']} SERP queries observed")
    print(f"Wrote: {a.out}")
if __name__=="__main__": main()
