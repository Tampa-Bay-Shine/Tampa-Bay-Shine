from pathlib import Path
import json,sys
from bs4 import BeautifulSoup
repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
p=repo/"cloudflare-site/cleaning-tips/index.html"; out=repo/"site-management/blog/medium-posts.json"
s=BeautifulSoup(p.read_text(encoding="utf-8",errors="ignore"),"html.parser"); seen=set(); rows=[]
for a in s.find_all("a",href=True):
 u=a["href"].strip()
 if "medium.com/" not in u or u in seen: continue
 seen.add(u); card=a.find_parent("article"); h=card.find(["h2","h3"]) if card else None
 rows.append({"url":u,"title":h.get_text(" ",strip=True) if h else "","status":"audit"})
out.write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"Wrote {len(rows)} Medium references -> {out}")
