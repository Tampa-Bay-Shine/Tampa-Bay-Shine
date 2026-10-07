from __future__ import annotations
import argparse, html, json, os
from pathlib import Path
from urllib import request, error
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"
def load(n):
 p=DATA/n; return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
def n(v,d=0):
 try:return f"{float(v):,.{d}f}"
 except:return "--"
def pct(v): return "--" if v is None else f"{float(v):+.1f}%"
def row(label,p):
 c=p["overall"]["current"]; x=p["overall"]["change"]
 return f"<tr><td><b>{label}</b></td><td>{n(c.get('impressions'))} ({pct(x.get('impressions_pct'))})</td><td>{n(c.get('clicks'))} ({pct(x.get('clicks_pct'))})</td><td>{float(c.get('ctr',0))*100:.2f}% ({float(x.get('ctr_points',0)):+.2f} pts)</td><td>{float(c.get('position',0)):.2f} ({float(x.get('position',0)):+.2f})</td></tr>"
def page_name(value):
    from urllib.parse import urlparse
    try:
        path=urlparse(value).path.strip("/")
    except Exception:
        return value
    if not path: return "Homepage"
    return " ".join(x.capitalize() for x in path.replace("-", " ").split("/"))

def strongest(items, kind):
    candidates=[]
    for z in items or []:
        c=z.get("current",{}); p=z.get("previous",{}); x=z.get("change",{})
        vol=float(c.get("impressions",0) or 0)+float(p.get("impressions",0) or 0)
        if vol < 10: continue
        imp=float(x.get("impressions",0) or 0); clk=float(x.get("clicks",0) or 0)
        pos=float(x.get("position",0) or 0)
        if kind=="growth":
            score=clk*25+max(imp,0)+max(pos,0)*.25
            if clk>0 or imp>=5: candidates.append((score,z))
        elif kind=="ranking_decline" and pos <= -3:
            prior_vol=float(p.get("impressions",0) or 0)
            if prior_vol >= 10:
                candidates.append((abs(pos)+max(-clk,0)*25,z))
    return max(candidates,key=lambda q:q[0])[1] if candidates else None

def growth_text(label,z,is_page=False):
    if not z:return None
    x=z.get("change",{}); name=page_name(z.get("name","--")) if is_page else z.get("name","--")
    imp=float(x.get("impressions",0) or 0); clk=float(x.get("clicks",0) or 0); pos=float(x.get("position",0) or 0)
    rank=("ranking improved %.2f positions"%pos if pos>0.5 else "ranking declined %.2f positions"%abs(pos) if pos<-0.5 else "ranking essentially stable")
    return f"{label}: {name} — {imp:+.0f} impressions, {clk:+.0f} clicks; {rank}."

def decline_text(label,z,is_page=False):
    if not z:return None
    x=z.get("change",{}); name=page_name(z.get("name","--")) if is_page else z.get("name","--")
    imp=float(x.get("impressions",0) or 0); clk=float(x.get("clicks",0) or 0); pos=float(x.get("position",0) or 0)
    return f"{label}: {name} — impressions {imp:+.0f}, clicks {clk:+.0f}, while average position deteriorated by {abs(pos):.2f} positions."

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--to",required=True); ap.add_argument("--from",dest="sender",required=True); ap.add_argument("--reply-to",required=True); ap.add_argument("--dashboard-url",required=True); a=ap.parse_args()
 key=os.environ.get("RESEND_API_KEY","").strip()
 if not key:raise SystemExit("RESEND_API_KEY is missing")
 pi=load("performance-intelligence.json"); ga=load("ga4.json"); ai=load("ai.json"); op=load("opportunity-intelligence.json")
 if not pi.get("periods"):raise SystemExit("performance-intelligence.json is missing or invalid")
 d,w,m=pi["periods"]["daily"],pi["periods"]["weekly"],pi["periods"]["monthly"]; wc,wx=w["overall"]["current"],w["overall"]["change"]; mc,mx=m["overall"]["current"],m["overall"]["change"]
 matters=[]
 if wc.get("impressions",0)>=100:matters.append(f"7-day search visibility: {n(wc.get('impressions'))} impressions ({pct(wx.get('impressions_pct'))}) and {n(wc.get('clicks'))} clicks ({pct(wx.get('clicks_pct'))}) versus the prior 7 days.")
 if mc.get("impressions",0)>=250:matters.append(f"28-day trend: {n(mc.get('impressions'))} impressions ({pct(mx.get('impressions_pct'))}), {n(mc.get('clicks'))} clicks ({pct(mx.get('clicks_pct'))}), with CTR movement of {float(mx.get('ctr_points',0)):+.2f} percentage points.")
 if float(d["overall"]["current"].get("clicks",0) or 0)+float(d["overall"]["previous"].get("clicks",0) or 0)>=10:matters.append(f"Daily clicks: {n(d['overall']['current'].get('clicks'))} ({pct(d['overall']['change'].get('clicks_pct'))}) versus the prior complete day.")
 g=ga.get("periods",{}).get("7",{}); ov=g.get("overview",{}).get("current",{}); it=g.get("intent",{}).get("current",{}); bk=g.get("confirmed_bookings",{}).get("current",{})
 organic=f"{n(ov.get('sessions'))} Organic Search sessions; {n(it.get('booknow_click'))} booking starts ({n(ov.get('booking_start_rate'),2)}%); {n(bk.get('confirmed_bookings'))} confirmed bookings ({n(ov.get('confirmed_booking_rate'),2)}%)."
 aa=ai.get("periods",{}).get("7",{}).get("current",{}).get("summary",{}); ait=f"{n(aa.get('sessions'))} identifiable AI referral session(s), {n(aa.get('booknow_click'))} booking start(s), and {n(aa.get('confirmed_bookings'))} confirmed booking(s) in the latest 7 days."
 weekly_range=w.get("overall",{}).get("range",{}).get("current",[])
 full_week_post_boundary=bool(weekly_range and weekly_range[0] >= "2026-10-05")
 movers=[x for x in [
  growth_text("Query growth",strongest(w.get("query_movers"),"growth")),
  decline_text("Query ranking concern",strongest(w.get("query_movers"),"ranking_decline")) if full_week_post_boundary else None,
  growth_text("Page growth",strongest(w.get("page_movers"),"growth"),True),
  decline_text("Page ranking concern",strongest(w.get("page_movers"),"ranking_decline"),True) if full_week_post_boundary else None
 ] if x]
 acts=op.get("actions") or []; top=next((x for x in acts if x.get("priority")=="high"),acts[0] if acts else None)
 rec=(f"{top.get('subject','Priority opportunity')}: {top.get('recommended_action','Review dashboard evidence before changing the site.')}" if top else "No evidence-based opportunity currently meets the action threshold; continue measurement.")
 body=f"""<!doctype html><html><body style="font-family:Arial,sans-serif;color:#172033;line-height:1.45;max-width:900px;margin:auto"><h2>Tampa Bay Shine Daily SEO Performance Brief</h2><div style="color:#667085">GSC data through {html.escape(str(pi.get('data_through','--')))}</div><table cellpadding="8" cellspacing="0" border="1" style="border-collapse:collapse;border-color:#d0d5dd;margin-top:12px"><tr><th>Period</th><th>Impressions</th><th>Clicks</th><th>CTR</th><th>Avg position</th></tr>{row("Daily",d)}{row("7 days",w)}{row("28 days",m)}</table><h3>What matters today</h3><ul>{''.join(f'<li>{html.escape(x)}</li>' for x in matters)}</ul><h3>Business results</h3><p><b>Organic Search:</b> {html.escape(organic)}</p><p><b>AI referrals:</b> {html.escape(ait)}</p><h3>Search movers</h3>{('<ul>'+''.join(f'<li>{html.escape(x)}</li>' for x in movers)+'</ul>') if movers else '<p>No retained query/page movement cleared the volume threshold.</p>'}<h3>Recommended action</h3><p>{html.escape(rec)}</p><p><a href="{html.escape(a.dashboard_url)}">Open the SEO Dashboard</a></p><p style="font-size:12px;color:#667085">Site-wide GSC headline totals use date-only Search Console data. Query/page movers use retained histories and may omit anonymized or low-volume observations. Organic Search and identifiable AI conversions are GA4 channel-level evidence and are not attributed to individual GSC queries. Average position is aggregate; lower is better. SEO Event timing and period movement do not prove causation.</p></body></html>"""
 payload={"from":a.sender,"to":[a.to],"reply_to":a.reply_to,"subject":f"Tampa Bay Shine SEO Brief — data through {pi.get('data_through','--')}","html":body}
 req=request.Request("https://api.resend.com/emails",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Accept":"application/json","User-Agent":"TampaBayShine-SEO-Dashboard/1.0"},method="POST")
 try:
  with request.urlopen(req,timeout=30) as r: result=json.loads(r.read().decode())
 except error.HTTPError as e:raise SystemExit(f"Resend API error {e.code}: {e.read().decode(errors='replace')}")
 print("Daily SEO Performance Brief sent:",result.get("id","accepted"))
if __name__=="__main__":main()
