from pathlib import Path
import json,sys
from bs4 import BeautifulSoup
repo=Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve(); root=repo/"cloudflare-site/blog"; e=[]; w=[]
if not root.exists(): w.append("No deployable /blog/ yet; foundation only.")
else:
 for p in root.rglob("index.html"):
  route="/blog/" if p.parent==root else f"/blog/{p.parent.name}/"; raw=p.read_text(encoding="utf-8",errors="ignore"); s=BeautifulSoup(raw,"html.parser")
  if len(s.find_all("h1"))!=1:e.append(route+": H1 count")
  if not s.title:e.append(route+": title missing")
  c=s.find("link",rel="canonical")
  if not c or c.get("href")!="https://tampabayshine.com"+route:e.append(route+": canonical mismatch")
  dependency_raw = raw
  start = dependency_raw.find("<!-- TBS_GOOGLE_TAG_START -->")
  end = dependency_raw.find("<!-- TBS_GOOGLE_TAG_END -->")
  if start != -1 and end != -1:
   end += len("<!-- TBS_GOOGLE_TAG_END -->")
   dependency_raw = dependency_raw[:start] + dependency_raw[end:]
  if "bookingkoala.com" in dependency_raw:e.append(route+": BookingKoala content/CDN dependency")
  if route!="/blog/":
   blob=" ".join(x.get_text() for x in s.find_all("script",attrs={"type":"application/ld+json"}))
   if "BlogPosting" not in blob and "Article" not in blob:e.append(route+": article schema missing")
   if "BreadcrumbList" not in blob:e.append(route+": breadcrumb schema missing")
  for im in s.find_all("img"):
   if not im.get("width") or not im.get("height"):w.append(route+": image dimensions missing")
print("TBS BLOG V23 AUDIT\n"+"="*28); print("Errors:",len(e),"Warnings:",len(w))
for x in e:print("ERROR:",x)
for x in w:print("WARN:",x)
raise SystemExit(1 if e else 0)
