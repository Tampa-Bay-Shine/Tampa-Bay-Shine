from __future__ import annotations
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"cloudflare-site"/"seo-dashboard"/"data"
OUT=DATA/"indexing-intelligence.json"
HISTORY=DATA/"indexing-history.json"
SITE="https://tampabayshine.com/"
SCOPES=["https://www.googleapis.com/auth/webmasters.readonly"]
PAGES=[
("/","Homepage"),("/services/","Services Hub"),
("/standard-cleaning-services-tampa/","Standard Cleaning"),
("/deep-cleaning-services-tampa/","Deep Cleaning"),
("/move-out-cleaning-tampa/","Move Out / Move In Cleaning"),
("/apartment-cleaning-tampa/","Apartment Cleaning"),
("/airbnb-cleaning-services/","Airbnb Cleaning"),
("/office-cleaning/","Office Cleaning"),
("/commercial-cleaning-tampa/","Commercial Cleaning"),
("/medical-office-cleaning-tampa/","Medical Office Cleaning"),
("/locations/","Locations Hub"),
("/house-cleaning-brandon-fl/","Brandon House Cleaning"),
("/house-cleaning-riverview-fl/","Riverview House Cleaning"),
("/house-cleaning-sun-city-center-fl/","Sun City Center House Cleaning"),
("/house-cleaning-ruskin-fl/","Ruskin House Cleaning")]

def auth(client_secret,token):
    creds=None
    if token.exists():
        creds=Credentials.from_authorized_user_file(str(token),SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_secrets_file(str(client_secret),SCOPES)
            creds=flow.run_local_server(port=0)
        token.write_text(creds.to_json(),encoding="utf-8")
    return creds

def inspect(service,url):
    raw=service.urlInspection().index().inspect(
        body={"inspectionUrl":url,"siteUrl":SITE}).execute()
    r=((raw.get("inspectionResult") or {}).get("indexStatusResult") or {})
    return {
      "url":url,"verdict":r.get("verdict"),"coverage_state":r.get("coverageState"),
      "indexing_state":r.get("indexingState"),"robots_txt_state":r.get("robotsTxtState"),
      "last_crawl_time":r.get("lastCrawlTime"),"page_fetch_state":r.get("pageFetchState"),
      "crawled_as":r.get("crawledAs"),"google_canonical":r.get("googleCanonical"),
      "user_canonical":r.get("userCanonical"),
      "inspection_result_link":((raw.get("inspectionResult") or {}).get("inspectionResultLink"))
    }

def is_indexed(x):
    return x.get("verdict")=="PASS" and x.get("coverage_state")=="Submitted and indexed"

def canonical_matches(x):
    return bool(x.get("google_canonical")) and x.get("google_canonical")==x.get("user_canonical")

def detect_changes(previous,current):
    # Material state changes are separated from routine Google recrawls.
    if not previous:
        return {"comparison_available":False,"previous_checked_at":None,"material_change_count":0,"adverse_change_count":0,"recrawl_count":0,"status":"baseline","events":[],"recrawls":[]}
    before={x.get("path"):x for x in (previous.get("pages") or [])}
    events=[]; recrawls=[]
    for cur in current:
        path=cur.get("path"); old=before.get(path)
        if not old:
            events.append({"path":path,"type":"new_tracked_page","severity":"info","from":None,"to":"tracked"}); continue
        oi,ni=is_indexed(old),is_indexed(cur)
        if oi!=ni: events.append({"path":path,"type":"indexing_status","severity":"recovered" if ni else "needs_attention","from":"indexed" if oi else "not_indexed","to":"indexed" if ni else "not_indexed"})
        if old.get("verdict")!=cur.get("verdict"): events.append({"path":path,"type":"verdict","severity":"recovered" if cur.get("verdict")=="PASS" else "needs_attention","from":old.get("verdict"),"to":cur.get("verdict")})
        if old.get("coverage_state")!=cur.get("coverage_state"): events.append({"path":path,"type":"coverage_state","severity":"recovered" if ni else "needs_attention","from":old.get("coverage_state"),"to":cur.get("coverage_state")})
        if old.get("google_canonical")!=cur.get("google_canonical"): events.append({"path":path,"type":"google_canonical","severity":"needs_attention","from":old.get("google_canonical"),"to":cur.get("google_canonical")})
        if old.get("user_canonical")!=cur.get("user_canonical"): events.append({"path":path,"type":"declared_canonical","severity":"needs_attention","from":old.get("user_canonical"),"to":cur.get("user_canonical")})
        oc,nc=canonical_matches(old),canonical_matches(cur)
        if oc!=nc: events.append({"path":path,"type":"canonical_match","severity":"recovered" if nc else "needs_attention","from":oc,"to":nc})
        if old.get("last_crawl_time") and cur.get("last_crawl_time") and old.get("last_crawl_time")!=cur.get("last_crawl_time"): recrawls.append({"path":path,"from":old.get("last_crawl_time"),"to":cur.get("last_crawl_time")})
    adverse=sum(x.get("severity")=="needs_attention" for x in events)
    return {"comparison_available":True,"previous_checked_at":previous.get("checked_at"),"material_change_count":len(events),"adverse_change_count":adverse,"recrawl_count":len(recrawls),"status":"needs_attention" if adverse else ("changed" if events else "no_change"),"events":events,"recrawls":recrawls}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--client-secret",type=Path,required=True)
    ap.add_argument("--token",type=Path,required=True)
    ap.add_argument("--out",type=Path,default=OUT)
    ap.add_argument("--history-out",type=Path,default=HISTORY)
    a=ap.parse_args()
    service=build("searchconsole","v1",credentials=auth(a.client_secret,a.token),cache_discovery=False)
    rows=[]
    for path,label in PAGES:
        x=inspect(service,SITE.rstrip("/")+path)
        x.update({"path":path,"label":label})
        rows.append(x)
    indexed=sum(x["verdict"]=="PASS" and x["coverage_state"]=="Submitted and indexed" for x in rows)
    canonical_match=sum(1 for x in rows if x.get("google_canonical") and x.get("google_canonical")==x.get("user_canonical"))
    issues=[x for x in rows if not (x["verdict"]=="PASS" and x["coverage_state"]=="Submitted and indexed")]
    now=datetime.now(timezone.utc).isoformat()
    status="healthy" if indexed==len(rows) and canonical_match==len(rows) else "needs_attention"
    hist={"schema_version":2,"snapshots":[]}
    if a.history_out.exists():
        hist=json.loads(a.history_out.read_text(encoding="utf-8-sig"))
    previous=(hist.get("snapshots") or [])[-1] if (hist.get("snapshots") or []) else None
    changes=detect_changes(previous,rows)
    payload={"schema_version":2,"generated_at":now,"source":"Google Search Console URL Inspection API",
      "property":SITE,"scope":"Fixed 15 strategic Core Pages; this is not a site-wide index coverage count.",
      "executive":{"status":status,"tracked":len(rows),"indexed":indexed,
        "not_indexed_or_nonpass":len(issues),"canonical_matches":canonical_match},
      "changes":changes,"pages":rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    snap={"checked_at":now,"status":status,"tracked":len(rows),"indexed":indexed,
          "not_indexed_or_nonpass":len(issues),"canonical_matches":canonical_match,
          "changes":{"status":changes["status"],"material_change_count":changes["material_change_count"],"adverse_change_count":changes.get("adverse_change_count",0),"recrawl_count":changes["recrawl_count"]},
          "pages":[{"path":x["path"],"verdict":x["verdict"],"coverage_state":x["coverage_state"],
                    "last_crawl_time":x["last_crawl_time"],"google_canonical":x["google_canonical"],
                    "user_canonical":x["user_canonical"]} for x in rows]}
    snaps=(hist.get("snapshots") or [])+[snap]
    hist={"schema_version":2,"snapshots":snaps[-180:]}
    a.history_out.write_text(json.dumps(hist,indent=2)+"\n",encoding="utf-8")
    print(f"Indexing Intelligence: {indexed}/{len(rows)} submitted and indexed; {canonical_match}/{len(rows)} canonical matches; {len(issues)} issues; {changes['material_change_count']} material changes; {changes['recrawl_count']} recrawls.")
if __name__=="__main__":main()