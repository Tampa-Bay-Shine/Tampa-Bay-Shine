from pathlib import Path
import argparse,json,time,urllib.parse,requests
from bs4 import BeautifulSoup
def browser_html(url):
 try:
  from playwright.sync_api import sync_playwright
 except Exception:return None
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1440,"height":1200})
  pg.goto(url,wait_until="networkidle",timeout=60000); h=pg.content(); b.close(); return h
ap=argparse.ArgumentParser(); ap.add_argument("--repo",default="."); ap.add_argument("--browser",action="store_true"); ap.add_argument("--limit",type=int,default=0); a=ap.parse_args()
repo=Path(a.repo).resolve(); inv=json.loads((repo/"site-management/blog/bk-posts.json").read_text()); dest=repo/"reports/blog-v23/bk-extract"; dest.mkdir(parents=True,exist_ok=True); summary=[]
for i,r in enumerate(inv[:a.limit or None],1):
 try:
  h=browser_html(r["source_url"]) if a.browser else None
  method="playwright" if h else "requests"
  if not h:
   q=requests.get(r["source_url"],timeout=30,headers={"User-Agent":"Mozilla/5.0"}); q.raise_for_status(); h=q.text
  s=BeautifulSoup(h,"html.parser"); candidates=s.find_all(["article","main","section"])
  body=max(candidates,key=lambda n:len(n.get_text(" ",strip=True))) if candidates else s.body or s
  h1=body.find("h1"); title=h1.get_text(" ",strip=True) if h1 else (s.title.get_text(" ",strip=True) if s.title else "")
  imgs=[{"src":urllib.parse.urljoin(r["source_url"],im.get("src") or im.get("data-src") or ""),"alt":im.get("alt","")} for im in body.find_all("img") if im.get("src") or im.get("data-src")]
  text=body.get_text("\n",strip=True); rec={"slug":r["slug"],"url":r["source_url"],"method":method,"title":title,"text":text,"images":imgs,"html":str(body)}
  (dest/f'{r["slug"]}.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False),encoding="utf-8"); summary.append({"slug":r["slug"],"ok":True,"chars":len(text),"images":len(imgs)})
  print(f'[{i}/{len(inv)}] {r["slug"]}: {len(text)} chars / {len(imgs)} images')
 except Exception as e:
  summary.append({"slug":r["slug"],"ok":False,"error":str(e)}); print("FAIL",r["slug"],e)
 time.sleep(.2)
(repo/"reports/blog-v23/bk-extract-summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
