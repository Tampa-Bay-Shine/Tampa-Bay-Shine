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
    payload={"schema_version":1,"generated_at":now,"source":"Google Search Console URL Inspection API",
      "property":SITE,"scope":"Fixed 15 strategic Core Pages; this is not a site-wide index coverage count.",
      "executive":{"status":status,"tracked":len(rows),"indexed":indexed,
        "not_indexed_or_nonpass":len(issues),"canonical_matches":canonical_match},
      "pages":rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    hist={"schema_version":1,"snapshots":[]}
    if a.history_out.exists():
        hist=json.loads(a.history_out.read_text(encoding="utf-8-sig"))
    snap={"checked_at":now,"status":status,"tracked":len(rows),"indexed":indexed,
          "not_indexed_or_nonpass":len(issues),"canonical_matches":canonical_match,
          "pages":[{"path":x["path"],"verdict":x["verdict"],"coverage_state":x["coverage_state"],
                    "last_crawl_time":x["last_crawl_time"],"google_canonical":x["google_canonical"],
                    "user_canonical":x["user_canonical"]} for x in rows]}
    snaps=(hist.get("snapshots") or [])+[snap]
    hist={"schema_version":1,"snapshots":snaps[-180:]}
    a.history_out.write_text(json.dumps(hist,indent=2)+"\n",encoding="utf-8")
    print(f"Indexing Intelligence: {indexed}/{len(rows)} submitted and indexed; {canonical_match}/{len(rows)} canonical matches; {len(issues)} issues.")
if __name__=="__main__":main()