from __future__ import annotations
import argparse,json,re
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange,Dimension,Metric,RunReportRequest
ROOT=Path(__file__).resolve().parents[1]
SCOPES=["https://www.googleapis.com/auth/analytics.readonly"]
INTENT=["booknow_click","phone_click","commercial_quote_start","contact_click","coupon_click"]
PRIMARY=["booknow_click","phone_click","commercial_quote_start","contact_click"]
CONFIRMED="BookingByCustomer"
RULES=[
("chatgpt","ChatGPT / OpenAI",(r"chatgpt\.com",r"chat\.openai\.com",r"^chatgpt$")),
("perplexity","Perplexity",(r"perplexity\.ai",r"^perplexity$")),
("claude","Claude",(r"claude\.ai",r"^claude$")),
("copilot","Microsoft Copilot",(r"copilot\.microsoft\.com",r"^copilot$")),
("gemini","Gemini",(r"gemini\.google\.com",r"^gemini$"))]
def credentials(secret,token):
 c=Credentials.from_authorized_user_file(str(token),SCOPES) if token.exists() else None
 if c and c.expired and c.refresh_token:
  try:c.refresh(Request())
  except Exception:c=None
 if not c or not c.valid:
  c=InstalledAppFlow.from_client_secrets_file(str(secret),SCOPES).run_local_server(port=0)
  token.parent.mkdir(parents=True,exist_ok=True);token.write_text(c.to_json(),encoding="utf-8")
 return c
def report(client,pid,dims,metrics,dr):
 return client.run_report(RunReportRequest(property=f"properties/{pid}",
  dimensions=[Dimension(name=x) for x in dims],metrics=[Metric(name=x) for x in metrics],
  date_ranges=[DateRange(start_date=dr[0],end_date=dr[1])],limit=100000))
def rows(r):
 dh=[x.name for x in r.dimension_headers];mh=[x.name for x in r.metric_headers];out=[]
 for x in r.rows:
  d={h:v.value for h,v in zip(dh,x.dimension_values)}
  d.update({h:v.value for h,v in zip(mh,x.metric_values)});out.append(d)
 return out
def n(v):
 try:return float(v or 0)
 except:return 0.0
def classify(source,sm):
 h=f"{source or ''} {sm or ''}".lower()
 for key,label,pats in RULES:
  if any(re.search(p,h) for p in pats):return key,label
 return None,None
def blank(key,label):
 return {"platform":key,"label":label,"sessions":0,"active_users":0,"engaged_sessions":0,
         **{e:0 for e in INTENT},"confirmed_bookings":0}
def rates(x):
 s=n(x["sessions"]);b=n(x["booknow_click"]);c=n(x["confirmed_bookings"])
 x["engagement_rate"]=round(n(x["engaged_sessions"])/s*100,2) if s else None
 x["booking_start_rate"]=round(b/s*100,2) if s else None
 x["confirmed_booking_rate"]=round(c/s*100,2) if s else None
 x["booking_completion_rate"]=round(c/b*100,2) if b else None
 x["primary_intent_actions"]=sum(n(x[e]) for e in PRIMARY);return x
def collect(client,pid,dr):
 traffic=rows(report(client,pid,["sessionSource","sessionSourceMedium"],["sessions","activeUsers","engagedSessions"],dr))
 events=rows(report(client,pid,["sessionSource","sessionSourceMedium","eventName"],["eventCount"],dr))
 ps={};sources={}
 for r in traffic:
  k,l=classify(r.get("sessionSource"),r.get("sessionSourceMedium"))
  if not k:continue
  p=ps.setdefault(k,blank(k,l))
  p["sessions"]+=n(r.get("sessions"));p["active_users"]+=n(r.get("activeUsers"));p["engaged_sessions"]+=n(r.get("engagedSessions"))
  sk=(k,r.get("sessionSource") or "(not set)",r.get("sessionSourceMedium") or "(not set)")
  q=sources.setdefault(sk,{"platform":k,"source":sk[1],"source_medium":sk[2],"sessions":0})
  q["sessions"]+=n(r.get("sessions"))
 for r in events:
  ev=r.get("eventName")
  if ev not in INTENT+[CONFIRMED]:continue
  k,l=classify(r.get("sessionSource"),r.get("sessionSourceMedium"))
  if not k:continue
  p=ps.setdefault(k,blank(k,l))
  if ev==CONFIRMED:p["confirmed_bookings"]+=n(r.get("eventCount"))
  else:p[ev]+=n(r.get("eventCount"))
 total=blank("all_ai","All identifiable AI referrals")
 for p in ps.values():
  for k in ["sessions","active_users","engaged_sessions",*INTENT,"confirmed_bookings"]:total[k]+=n(p[k])
 return {"summary":rates(total),"platforms":[rates(x) for x in sorted(ps.values(),key=lambda x:n(x["sessions"]),reverse=True)],
         "sources":sorted(sources.values(),key=lambda x:n(x["sessions"]),reverse=True)}
def write_history(path,snapshots):
 h={"schema_version":1,"window_days":28,"snapshots":snapshots}
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(h,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")

def history(path,payload):
 h={"schema_version":1,"window_days":28,"snapshots":[]}
 if path.exists():
  try:h=json.loads(path.read_text(encoding="utf-8-sig"))
  except:pass
 through=(date.today()-timedelta(days=1)).isoformat()
 s=payload["periods"]["28"]["current"]["summary"]
 snap={"date":through,**s}
 snaps=[x for x in h.get("snapshots",[]) if x.get("date")!=through]+[snap]
 write_history(path,sorted(snaps,key=lambda x:x.get("date",""))[-400:])

def backfill_history(client,pid,path,start_date,end_date,step_days):
 start=date.fromisoformat(start_date)
 end=date.fromisoformat(end_date)
 if end >= date.today():
  end=date.today()-timedelta(days=1)
 if start > end:
  raise SystemExit("Backfill start date must be on or before the end date.")
 snapshots=[]
 cursor=start
 while cursor <= end:
  window_start=cursor-timedelta(days=27)
  summary=collect(
   client,pid,
   (window_start.isoformat(),cursor.isoformat())
  )["summary"]
  snapshots.append({"date":cursor.isoformat(),**summary})
  print(
   "Backfill",
   cursor.isoformat(),
   "sessions=",summary["sessions"],
   "confirmed_bookings=",summary["confirmed_bookings"]
  )
  cursor+=timedelta(days=step_days)
 write_history(path,snapshots)
 print("Wrote historical backfill",path)
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--property",default="487638948")
 ap.add_argument("--client-secret",default=str(Path.home()/".tbs-gsc"/"client_secret.json"))
 ap.add_argument("--token",default=str(Path.home()/".tbs-ga4"/"token.json"))
 ap.add_argument("--out",default=str(ROOT/"cloudflare-site/seo-dashboard/data/ai.json"))
 ap.add_argument("--history-out",default=str(ROOT/"cloudflare-site/seo-dashboard/data/ai-history.json"))
 ap.add_argument("--backfill-history",action="store_true")
 ap.add_argument("--backfill-start",default="2026-04-01")
 ap.add_argument("--backfill-end",default=None)
 ap.add_argument("--backfill-step-days",type=int,default=7)
 a=ap.parse_args();secret=Path(a.client_secret);token=Path(a.token)
 if not secret.exists():raise SystemExit(f"Google OAuth client secret not found: {secret}")
 client=BetaAnalyticsDataClient(credentials=credentials(secret,token))
 if a.backfill_history:
  end=a.backfill_end or (date.today()-timedelta(days=1)).isoformat()
  backfill_history(
   client,a.property,Path(a.history_out),
   a.backfill_start,end,a.backfill_step_days
  )
  return
 periods={}
 for days in (7,28,90):
  periods[str(days)]={"days":days,
   "current":collect(client,a.property,(f"{days}daysAgo","yesterday")),
   "previous":collect(client,a.property,(f"{days*2}daysAgo",f"{days+1}daysAgo"))}
 payload={"schema_version":1,"generated_at":datetime.now(timezone.utc).isoformat(),"data_through":"yesterday",
  "property_id":a.property,"definition":"Conservative classification of identifiable AI-assistant GA4 acquisition sources. Ordinary Organic Search is excluded.","periods":periods}
 out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(payload,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
 history(Path(a.history_out),payload);print("Wrote",out);print("Wrote",a.history_out)
if __name__=="__main__":main()
