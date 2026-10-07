from pathlib import Path
from datetime import date,datetime,timedelta
import json,math
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"cloudflare-site/seo-dashboard/data"
def load(n):
 p=DATA/n
 return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
def series(o):
 src=next((o[k] for k in ("queries","pages","items","series","history") if isinstance(o,dict) and isinstance(o.get(k),(dict,list))),o)
 if isinstance(src,dict):
  it=src.items()
 elif isinstance(src,list):
  it=[]
  for row in src:
   if not isinstance(row,dict): continue
   name=row.get("query") or row.get("page") or row.get("name") or row.get("key")
   if name: it.append((name,row))
 else:
  it=[]
 out=[]
 for name,v in it:
  pts=v.get("points",[]) if isinstance(v,dict) else v
  a=[]
  if not isinstance(pts,list): continue
  for p in pts:
   try:
    if isinstance(p,list) and len(p)>=5: d,c,i,ctr,pos=p[:5]
    elif isinstance(p,dict): d=p.get("date");c=p.get("clicks",0);i=p.get("impressions",0);ctr=p.get("ctr",0);pos=p.get("position")
    else: continue
    if d:a.append({"date":str(d),"clicks":float(c or 0),"impressions":float(i or 0),"position":float(pos) if pos is not None else None})
   except: pass
  if a: out.append((str(name),a))
 return out

def total_points(o):
    pts=[]
    for p in o.get("points",[]) if isinstance(o,dict) else []:
        if isinstance(p,list) and len(p)>=5:
            d,c,i,ctr,pos=p[:5]
            pts.append({"date":str(d),"clicks":float(c or 0),"impressions":float(i or 0),"position":float(pos) if pos is not None else None})
    return pts


def agg(pts,s,e):
 a=[p for p in pts if s<=p["date"]<=e]; c=sum(x["clicks"] for x in a); i=sum(x["impressions"] for x in a)
 pn=sum((x["position"] or 0)*x["impressions"] for x in a if x["position"] is not None)
 return {"clicks":round(c,2),"impressions":round(i,2),"ctr":round(c/i if i else 0,6),"position":round(pn/i,2) if i else None,"observed_days":len(a)}
def pct(a,b): return None if b==0 else round((a-b)/b*100,1)
def cmp(pts,end,n):
 e=date.fromisoformat(end); cs=e-timedelta(days=n-1); pe=cs-timedelta(days=1); ps=pe-timedelta(days=n-1)
 c=agg(pts,cs.isoformat(),e.isoformat()); p=agg(pts,ps.isoformat(),pe.isoformat())
 return {"current":c,"previous":p,"change":{"clicks":round(c["clicks"]-p["clicks"],2),"clicks_pct":pct(c["clicks"],p["clicks"]),"impressions":round(c["impressions"]-p["impressions"],2),"impressions_pct":pct(c["impressions"],p["impressions"]),"ctr_points":round((c["ctr"]-p["ctr"])*100,2),"position":round(p["position"]-c["position"],2) if p["position"] is not None and c["position"] is not None else None},"range":{"current":[cs.isoformat(),e.isoformat()],"previous":[ps.isoformat(),pe.isoformat()]}}
def total(ss,end,n):
 by={}
 for _,pts in ss:
  for x in pts:
   z=by.setdefault(x["date"],{"date":x["date"],"clicks":0,"impressions":0,"pn":0})
   z["clicks"]+=x["clicks"];z["impressions"]+=x["impressions"]
   if x["position"] is not None:z["pn"]+=x["position"]*x["impressions"]
 pts=[{"date":z["date"],"clicks":z["clicks"],"impressions":z["impressions"],"position":z["pn"]/z["impressions"] if z["impressions"] else None} for z in by.values()]
 return cmp(pts,end,n)
def movers(ss,end,n):
 r=[]
 for name,pts in ss:
  x=cmp(pts,end,n); c=x["current"];p=x["previous"]
  if c["impressions"]+p["impressions"]<5:continue
  ch=x["change"]; impact=abs(ch["impressions"])*.08+abs(ch["clicks"])*8+(abs(ch["position"] or 0)*max(1,math.log10(c["impressions"]+1)))
  r.append({"name":name,**x,"impact":round(impact,1)})
 return sorted(r,key=lambda x:x["impact"],reverse=True)[:12]
def canonical_page_name(name):
 from urllib.parse import urlsplit,urlunsplit
 try:
  u=urlsplit(name)
  if not u.scheme or not u.netloc:return name
  path=u.path or "/"
  if path!="/":path=path.rstrip("/")+"/"
  return urlunsplit((u.scheme.lower(),u.netloc.lower(),path,"",""))
 except Exception:return name

def merge_named_series(ss,normalizer):
 merged={}
 for name,pts in ss:
  key=normalizer(name); bydate=merged.setdefault(key,{})
  for x in pts:
   z=bydate.setdefault(x["date"],{"date":x["date"],"clicks":0.0,"impressions":0.0,"pn":0.0,"pi":0.0})
   z["clicks"]+=x["clicks"]; z["impressions"]+=x["impressions"]
   if x["position"] is not None:
    z["pn"]+=x["position"]*x["impressions"]; z["pi"]+=x["impressions"]
 out=[]
 for name,bydate in merged.items():
  pts=[{"date":z["date"],"clicks":z["clicks"],"impressions":z["impressions"],
        "position":z["pn"]/z["pi"] if z["pi"] else None} for z in bydate.values()]
  out.append((name,sorted(pts,key=lambda x:x["date"])))
 return out

q=series(load("query-history.json"))
pages=merge_named_series(series(load("page-history.json")),canonical_page_name)
totals=total_points(load("daily-total-history.json"))
if not totals: raise SystemExit("No authoritative daily GSC total history found")
end=max(x["date"] for x in totals); brand=("tampa bay shine","tampabayshine")
out={"generated_at":datetime.now().astimezone().isoformat(),"data_through":end,"methodology":{"monthly_days":28,"headline_source":"GSC date-only daily totals","query_page_source":"retained daily histories","missing_query_dates_are_zero":False,"page_url_normalization":"canonical trailing-slash aliases merged"},"periods":{}}
for label,n in {"daily":1,"weekly":7,"monthly":28}.items():
 o=cmp(totals,end,n); qm=movers(q,end,n); pm=movers(pages,end,n); ch=o["change"]; notes=[]
 if ch["impressions_pct"] is not None:notes.append(f"Search impressions {'increased' if ch['impressions_pct']>=0 else 'decreased'} {abs(ch['impressions_pct']):.1f}% versus the previous {n}-day period.")
 if ch["clicks_pct"] is not None:notes.append(f"Google clicks {'increased' if ch['clicks_pct']>=0 else 'decreased'} {abs(ch['clicks_pct']):.1f}% versus the previous {n}-day period.")
 if qm:notes.append(f"Highest-impact retained query movement: {qm[0]['name']}.")
 b=[x for x in q if any(t in x[0].lower() for t in brand)]; nb=[x for x in q if x not in b]
 out["periods"][label]={"days":n,"overall":o,"query_movers":qm,"page_movers":pm,"branded":total(b,end,n) if b else None,"nonbranded":total(nb,end,n) if nb else None,"observations":notes}
(DATA/"performance-intelligence.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print("Wrote Performance Intelligence data through",end)
