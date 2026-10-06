from __future__ import annotations
import argparse, html, json, os
from pathlib import Path
from urllib import request, error
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"
def load(name):
    p=DATA/name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
def num(v):
    try:return f"{float(v):,.0f}"
    except:return "--"
def pct(v): return "--" if v is None else f"{float(v):+.1f}%"
def metric_row(label,p):
    cur=p["overall"]["current"]; ch=p["overall"]["change"]; pos=cur.get("position")
    pt="--" if pos is None else f"{float(pos):.2f}"
    pd="--" if ch.get("position") is None else f"{float(ch['position']):+.2f}"
    return f"<tr><td><strong>{html.escape(label)}</strong></td><td>{num(cur.get('impressions'))} ({pct(ch.get('impressions_pct'))})</td><td>{num(cur.get('clicks'))} ({pct(ch.get('clicks_pct'))})</td><td>{float(cur.get('ctr',0))*100:.2f}% ({float(ch.get('ctr_points',0)):+.2f} pts)</td><td>{pt} ({pd})</td></tr>"
def mover_lines(items):
    out=[]
    for x in (items or [])[:3]:
        c=x.get("change",{})
        out.append(f"{x.get('name','--')}: {float(c.get('impressions',0)):+.0f} impressions, {float(c.get('clicks',0)):+.0f} clicks")
    return out
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--to",required=True); ap.add_argument("--from",dest="sender",required=True)
    ap.add_argument("--reply-to",required=True); ap.add_argument("--dashboard-url",required=True)
    a=ap.parse_args(); key=os.environ.get("RESEND_API_KEY","").strip()
    if not key: raise SystemExit("RESEND_API_KEY is missing")
    pi=load("performance-intelligence.json")
    if not pi.get("periods"): raise SystemExit("performance-intelligence.json is missing or invalid")
    d=pi["periods"]["daily"]; w=pi["periods"]["weekly"]; m=pi["periods"]["monthly"]
    matters=(d.get("observations",[])+w.get("observations",[])+m.get("observations",[])+mover_lines(w.get("query_movers"))+mover_lines(w.get("page_movers")))[:3]
    if not matters: matters=["No material observation met the brief threshold."]
    body=f"""<!doctype html><html><body style="font-family:Arial,sans-serif;color:#172033;line-height:1.45"><h2>Tampa Bay Shine Daily SEO Performance Brief</h2><div style="color:#667085">GSC data through {html.escape(str(pi.get('data_through','--')))}</div><table cellpadding="8" cellspacing="0" border="1" style="border-collapse:collapse;border-color:#d0d5dd"><tr><th>Period</th><th>Impressions</th><th>Clicks</th><th>CTR</th><th>Avg position</th></tr>{metric_row("Daily",d)}{metric_row("7 days",w)}{metric_row("28 days",m)}</table><h3>What matters today</h3><ul>{''.join(f'<li>{html.escape(str(x))}</li>' for x in matters)}</ul><p><strong>Conversion context:</strong> Booking starts are intent; confirmed bookings use the case-sensitive <code>BookingByCustomer</code> event. Review the dashboard for current Organic Search conversion evidence.</p><p><strong>AI context:</strong> Identifiable AI referrals and no-click AI answer visibility are separate measurements.</p><p><a href="{html.escape(a.dashboard_url)}">Open the SEO Dashboard</a></p><p style="font-size:12px;color:#667085">Site-wide GSC headline totals use date-only Search Console data. Query/page movers use retained histories and may omit anonymized or low-volume observations. Average position is aggregate; lower is better. Period movement and SEO Event timing do not prove causation.</p></body></html>"""
    payload={"from":a.sender,"to":[a.to],"reply_to":a.reply_to,"subject":f"Tampa Bay Shine SEO Brief — data through {pi.get('data_through','--')}","html":body}
    req=request.Request("https://api.resend.com/emails",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Accept":"application/json","User-Agent":"TampaBayShine-SEO-Dashboard/1.0"},method="POST")
    try:
        with request.urlopen(req,timeout=30) as resp: result=json.loads(resp.read().decode())
    except error.HTTPError as exc: raise SystemExit(f"Resend API error {exc.code}: {exc.read().decode(errors='replace')}")
    print("Daily SEO Performance Brief sent:",result.get("id","accepted"))
if __name__=="__main__": main()
