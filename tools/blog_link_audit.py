from pathlib import Path
import json,sys
from bs4 import BeautifulSoup
repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve(); site=repo/"cloudflare-site"; inv=json.loads((repo/"site-management/blog/content-map.json").read_text())
rules={"move-out":["move out","move-out","final walkthrough","security deposit"],"commercial-office":["office cleaning","commercial cleaning","janitorial"],"apartment":["apartment cleaning","leasing"],"realtor":["realtor","real estate","listing"],"deep-cleaning":["deep cleaning"],"cleaning-tips":["floor","mop","streak","vinegar","dust"],"house-cleaning":["house cleaning","recurring cleaning","maintenance cleaning"]}
by={}
for x in inv: by.setdefault(x["category"],[]).append(x)
rows=[]
for p in site.rglob("index.html"):
 if "/blog/" in p.as_posix():continue
 rel=p.relative_to(site).as_posix(); route="/" if rel=="index.html" else "/"+p.parent.relative_to(site).as_posix()+"/"; txt=BeautifulSoup(p.read_text(encoding="utf-8",errors="ignore"),"html.parser").get_text(" ",strip=True).lower()
 for c,terms in rules.items():
  hits=sum(txt.count(t) for t in terms)
  if hits: rows.append({"page":route,"category":c,"signal_hits":hits,"candidate_articles":[x["future_url"] for x in sorted(by.get(c,[]),key=lambda y:y["gsc_6mo"]["impressions"],reverse=True)[:3]]})
rows.sort(key=lambda x:-x["signal_hits"]); d=repo/"reports/blog-v23"; d.mkdir(parents=True,exist_ok=True); (d/"internal-link-opportunities.json").write_text(json.dumps(rows,indent=2),encoding="utf-8"); print(f"Wrote {len(rows)} opportunities")
