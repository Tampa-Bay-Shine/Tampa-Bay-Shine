from __future__ import annotations
import argparse, html, json, os
from pathlib import Path
from urllib import request, error

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"

def load(name):
    p=DATA/name
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}

def num(v,d=0):
    try:return f"{float(v):,.{d}f}"
    except (TypeError,ValueError):return "--"

def signed(v,suffix=""):
    if v is None:return "--"
    try:return f"{float(v):+.1f}{suffix}"
    except (TypeError,ValueError):return "--"

def esc(v):return html.escape(str(v if v is not None else "--"))

def nested(d,*keys,default=None):
    for k in keys:
        if not isinstance(d,dict):return default
        d=d.get(k)
        if d is None:return default
    return d

def period_current(p):
    return nested(p,"overall","current",default={}) or {}

def period_change(p):
    return nested(p,"overall","change",default={}) or {}

def overall_status(pi,di):
    w=nested(pi,"periods","weekly",default={}) or {}
    c,x=period_current(w),period_change(w)
    imp=float(x.get("impressions_pct") or 0)
    pos=float(x.get("position") or 0)
    high=int(nested(di,"summary","high",default=0) or 0)
    if high>=4 or (imp<=-15 and pos<=-3):return "NEEDS ATTENTION"
    if imp>=10 and pos>=2:return "IMPROVING"
    return "STABLE"

def core_search_line(core):
    if not core:return "Core Search data unavailable."
    cohort=(core.get("cohorts") or {}).get("top_20") or {}
    ex=cohort.get("executive") or {}
    status=str(ex.get("overall_status") or "tracked").replace("_"," ").upper()
    reliable=ex.get("reliable_top_20")
    if reliable is None:return "Core Search authoritative executive metrics unavailable."
    return f"{status}: {int(reliable)} reliable Core 20 terms currently average in the Top 20."


def broader_gsc_top10_line(gsc):
    """Summarize meaningful broader GSC Top-10 visibility outside fixed cohorts."""
    rows = gsc.get("top_queries") or []
    qualifying = []

    for row in rows:
        query = str(row.get("query") or "").strip()
        lowered = " ".join(query.lower().split())

        try:
            impressions = float(row.get("current_impressions") or 0)
            position = float(row.get("current_position") or 0)
        except (TypeError, ValueError):
            continue

        if impressions < 10 or position <= 0 or position > 10:
            continue

        if "tampa bay shine" in lowered or "shine of tampa bay" in lowered:
            continue
        if "site:" in lowered:
            continue

        operator_hits = lowered.count(" or ") + lowered.count(" and ")
        quoted_phrases = lowered.count('"') // 2
        parenthesized = "(" in lowered and ")" in lowered

        if (
            (parenthesized and operator_hits >= 2 and quoted_phrases >= 1)
            or (operator_hits >= 4 and quoted_phrases >= 2)
            or (len(lowered) >= 180 and operator_hits >= 2)
        ):
            continue

        qualifying.append(
            {
                "query": query,
                "position": position,
                "impressions": impressions,
            }
        )

    qualifying.sort(
        key=lambda x: (-x["impressions"], x["position"], x["query"])
    )

    if not qualifying:
        return (
            "No meaningful non-brand query in the retained Top Queries set "
            "currently clears both Top-10 average position and 10 impressions "
            "in the current 28-day window."
        )

    examples = "; ".join(
        f'{x["query"]} (pos. {x["position"]:.2f}, {int(x["impressions"])} impr.)'
        for x in qualifying[:4]
    )

    return (
        f"{len(qualifying)} meaningful non-brand GSC queries with at least "
        f"10 impressions currently average in the Top 10 over 28 days. "
        f"Examples: {examples}. "
        "This broader GSC measure is separate from the fixed Core Search and "
        "manual competitor SERP cohorts."
    )


def best_core_page_growth(pages):
    """Select an evidence-supported Core Page with both growth and striking-distance visibility."""
    candidates = []
    rows = pages.get("pages", []) if isinstance(pages, dict) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        confidence = str(row.get("confidence") or "").lower()
        period = nested(row, "periods", "28") or {}
        current = period.get("current") or {}
        change = period.get("change") or {}
        try:
            position = float(current.get("position"))
            impressions = float(current.get("impressions"))
            observed_days = int(current.get("observed_days") or 0)
            impression_change = float(change.get("impressions"))
            position_change = float(change.get("position"))
        except (TypeError, ValueError):
            continue

        # Growth opportunity means the page is already within striking distance
        # and current demand is expanding without a concurrent ranking decline.
        if (
            confidence == "low"
            or observed_days < 5
            or impressions < 25
            or position < 4
            or position > 20
            or impression_change <= 0
            or position_change < 0
        ):
            continue

        label = row.get("label") or row.get("path") or "Core Page"
        candidates.append(
            (impressions, impression_change, position_change, -position, str(label), position)
        )

    if not candidates:
        return "No Core Page currently clears the evidence threshold for a growth opportunity."

    impressions, impression_change, position_change, neg_position, label, position = max(candidates)
    return (
        f"{label} - position {position:.2f}, {int(impressions)} impressions in the current 28 days "
        f"({int(impression_change):+d} vs prior 28 days; position {position_change:+.2f}). "
        f"Prioritize strengthening the existing page while it is within striking distance."
    )

def core_pages_line(pages):
    if not pages:return "Core Page data unavailable."
    ex=pages.get("executive") or {}
    status=str(ex.get("overall_status") or "tracked").replace("_"," ").upper()
    reliable=ex.get("reliable_pages")
    attention=nested(ex,"momentum","needs_attention")
    if reliable is None or attention is None:
        return "Core Page authoritative executive metrics unavailable."
    noun="needs" if int(attention)==1 else "need"
    return f"{status}: {int(reliable)} reliable strategic pages; {int(attention)} currently {noun} attention."
def competitor_line(ci):
    if not ci:return "Competitive data unavailable."
    x=ci.get("summary") or {}
    observed=x.get("serp_queries_observed")
    top10=x.get("tbs_top10")
    vis=x.get("tbs_visibility_share")
    gap=x.get("leader_gap_points")
    if None in (observed,top10,vis,gap):return "Competitive authoritative summary metrics unavailable."
    return f"{int(top10)} Tampa Bay Shine Top 10 rankings across {int(observed)} observed SERPs; visibility share {num(vis,1)}%; leader gap {num(gap,1)} pts."

def ga_line(ga):
    p=nested(ga,"periods","28",default={}) or {}
    ov=nested(p,"overview","current",default={}) or {}
    it=nested(p,"intent","current",default={}) or {}
    bk=nested(p,"confirmed_bookings","current",default={}) or {}
    return (f"{num(ov.get('sessions'))} Organic Search sessions; "
            f"{num(it.get('booknow_click'))} booking starts; "
            f"{num(it.get('primary_intent_actions') if it.get('primary_intent_actions') is not None else it.get('primary_intent'))} primary intent actions; "
            f"{num(bk.get('confirmed_bookings'))} confirmed organic bookings in 28 days.")

def ai_line(ai):
    p=nested(ai,"periods","28","current","summary",default={}) or {}
    return (f"{num(p.get('sessions'))} identifiable AI referral sessions; "
            f"{num(p.get('booknow_click'))} booking starts; "
            f"{num(p.get('confirmed_bookings'))} confirmed booking(s) in 28 days. "
            "This is referral traffic, not controlled AI-answer visibility.")

def action_rows(di,limit=3):
    items=di.get("items") or []
    out=[]
    for x in items[:limit]:
        m=x.get("metrics") or {}
        sig=", ".join(str(z.get("type","")).replace("_"," ") for z in (x.get("signals") or []))
        out.append({
            "priority":str(x.get("priority","")).upper(),
            "subject":x.get("subject","--"),
            "signals":sig or "--",
            "position":m.get("position"),
            "impressions":m.get("impressions"),
            "change":m.get("position_improvement"),
            "action":x.get("recommended_action","Review dashboard evidence.")
        })
    return out

def render(args):
    pi=load("performance-intelligence.json")
    di=load("decision-intelligence.json")
    core=load("core-search.json")
    gsc=load("gsc.json")
    pages=load("core-pages.json")
    ci=load("competitor-intelligence.json")
    ga=load("ga4.json")
    ai=load("ai.json")
    indexing=load("indexing-intelligence.json")
    if not nested(pi,"periods"):raise SystemExit("performance-intelligence.json is missing or invalid")
    if not di.get("items"):raise SystemExit("decision-intelligence.json is missing or invalid")

    w=nested(pi,"periods","weekly",default={}) or {}
    wc,wx=period_current(w),period_change(w)
    status=overall_status(pi,di)
    actions=action_rows(di,3)
    top=actions[0] if actions else None
    high=int(nested(di,"summary","high",default=0) or 0)
    total=int(nested(di,"summary","consolidated_actions",default=len(di.get("items") or [])) or 0)

    search=(f"{num(wc.get('impressions'))} impressions ({signed(wx.get('impressions_pct'),'%')}) and "
            f"avg position {num(wc.get('position'),1)} "
            f"({signed(wx.get('position'),' positions')} vs prior 7 days; positive means improvement).")
    ix=nested(indexing,"executive",default={}) or {}
    ix_tracked=ix.get("tracked")
    ix_indexed=ix.get("indexed")
    ix_issues=ix.get("not_indexed_or_nonpass")
    ix_canon=ix.get("canonical_matches")
    change=nested(indexing,"changes",default={}) or {}
    comparison=bool(change.get("comparison_available"))
    material=int(change.get("material_change_count") or 0)
    adverse=int(change.get("adverse_change_count") or 0)
    recrawls=int(change.get("recrawl_count") or 0)
    change_line=((f"No material indexing/canonical changes since the previous inspection; {recrawls} Google recrawl(s) detected." if material==0 else f"{material} material indexing/canonical change(s) since the previous inspection; {adverse} adverse; {recrawls} Google recrawl(s) detected.") if comparison else "Change comparison baseline established; no prior inspection is available.")
    indexing_line=(
        f"{int(ix_indexed)}/{int(ix_tracked)} strategic Core Pages are Submitted and indexed; "
        f"{int(ix_canon)}/{int(ix_tracked)} Google-selected canonicals match declared canonicals; "
        f"{int(ix_issues)} inspection issues. {change_line} Scope is the fixed Core Pages cohort, not a site-wide coverage count."
        if None not in (ix_tracked,ix_indexed,ix_issues,ix_canon)
        else "Live URL Inspection data unavailable; no indexing-health claim is made."
    )
    management=(
        f"{high} high-priority and {total} total evidence-supported Decision Intelligence actions. "
        + indexing_line
    )
    opportunity=(f"{top['subject']} - position {num(top['position'],2)}, {num(top['impressions'])} impressions in the current 28 days. "
                 f"{top['action']}" if top else "No action currently clears the evidence threshold.")

    priority_issue=(f"{top['subject']} - position {num(top['position'],2)}, {num(top['impressions'])} impressions in the current 28 days. "
                    f"{top['action']}" if top else "No issue currently clears the evidence threshold.")
    growth_opportunity=best_core_page_growth(pages)

    rows="".join(
      f"<tr><td><b>{esc(x['priority'])}</b></td><td>{esc(x['subject'])}</td><td>{esc(x['signals'])}</td>"
      f"<td>{num(x['position'],2)}</td><td>{num(x['impressions'])}</td><td>{signed(x['change'],' pos.')}</td>"
      f"<td>{esc(x['action'])}</td></tr>" for x in actions
    )
    card=lambda title,text: f'<div style="border:1px solid #d8e3ef;border-radius:8px;padding:12px;margin:8px 0"><b>{esc(title)}</b><div style="margin-top:5px">{esc(text)}</div></div>'
    body=f"""<!doctype html><html><body style="font-family:Arial,sans-serif;color:#172033;line-height:1.45;max-width:900px;margin:auto;padding:18px">
<h2 style="margin-bottom:2px">Tampa Bay Shine Daily SEO Executive Brief</h2>
<div style="color:#667085">Data through {esc(pi.get('data_through','--'))} | Decision Intelligence through {esc(di.get('data_through','--'))}</div>
<div style="margin:16px 0;padding:14px;border-left:5px solid #1473e6;background:#f4f8fc"><b>OVERALL STATUS: {esc(status)}</b><br>{esc(search)}</div>
<h3>30-second executive view</h3>
{card("Google organic reach",search)}
{card("Core Search",core_search_line(core))}
{card("Broader GSC Top-10 visibility",broader_gsc_top10_line(gsc))}
{card("Core Pages",core_pages_line(pages))}
{card("Competitive position",competitor_line(ci))}
{card("Organic conversions",ga_line(ga))}
{card("AI referral results",ai_line(ai))}
{card("Technical / indexing",indexing_line)}
{card("Management attention",management)}
{card("Highest-priority issue",priority_issue)}
{card("Best growth opportunity",growth_opportunity)}
<h3>Top Decision Intelligence actions</h3>
<table cellpadding="7" cellspacing="0" border="1" style="border-collapse:collapse;border-color:#d0d5dd;width:100%;font-size:13px">
<tr><th>Priority</th><th>Query / Page</th><th>Signals</th><th>Position (28D)</th><th>Impr. (28D)</th><th>Change vs prior 28D</th><th>Recommended action</th></tr>{rows}</table>
<p style="margin-top:18px"><a href="{esc(args.dashboard_url)}">Open the SEO Dashboard</a></p>
<p style="font-size:12px;color:#667085">Decision Intelligence is the same evidence-thresholded model used by the dashboard; low-confidence samples and synthetic automation queries are excluded. GSC average position is impression-weighted performance data, not a deterministic live SERP rank. Organic Search and identifiable AI conversions are GA4 channel-level evidence and are not attributed to individual GSC queries.</p>
</body></html>"""
    return body,pi

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--to")
    ap.add_argument("--from",dest="sender")
    ap.add_argument("--reply-to")
    ap.add_argument("--dashboard-url",default="https://seo.tampabayshine.com/")
    ap.add_argument("--preview-html",help="Write HTML preview and do not send.")
    a=ap.parse_args()
    body,pi=render(a)
    if a.preview_html:
        out=Path(a.preview_html);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(body,encoding="utf-8")
        print("SEO executive email preview written:",out)
        return
    for name,val in [("--to",a.to),("--from",a.sender),("--reply-to",a.reply_to)]:
        if not val:raise SystemExit(f"{name} is required unless --preview-html is used")
    key=os.environ.get("RESEND_API_KEY","").strip()
    if not key:raise SystemExit("RESEND_API_KEY is missing")
    payload={"from":a.sender,"to":[a.to],"reply_to":a.reply_to,
             "subject":f"Tampa Bay Shine SEO Executive Brief - data through {pi.get('data_through','--')}","html":body}
    req=request.Request("https://api.resend.com/emails",data=json.dumps(payload).encode(),
      headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Accept":"application/json",
               "User-Agent":"TampaBayShine-SEO-Dashboard/2.0"},method="POST")
    try:
        with request.urlopen(req,timeout=30) as r:result=json.loads(r.read().decode())
    except error.HTTPError as e:raise SystemExit(f"Resend API error {e.code}: {e.read().decode(errors='replace')}")
    print("Daily SEO Executive Brief sent:",result.get("id","accepted"))
if __name__=="__main__":main()
