#!/usr/bin/env python3
import argparse,csv,html,re
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
DROP_RE=re.compile(r"<(?:script|style|noscript|svg)\b.*?</(?:script|style|noscript|svg)>",re.I|re.S)
NAV_RE=re.compile(r"<(?:header|footer|nav)\b.*?</(?:header|footer|nav)>",re.I|re.S)
TAG_RE=re.compile(r"<[^>]+>"); WORD_RE=re.compile(r"\b[\w’'-]+\b",re.UNICODE)
def txt(s): return re.sub(r"\s+"," ",html.unescape(TAG_RE.sub(" ",NAV_RE.sub(" ",DROP_RE.sub(" ",s))))).strip()
def attr_tag(raw,tag,name,value,attr):
    for m in re.finditer(fr"<{tag}\b[^>]*>",raw,re.I|re.S):
        t=m.group(0)
        if re.search(fr"\b{name}\s*=\s*['\"]{re.escape(value)}['\"]",t,re.I):
            a=re.search(fr"\b{attr}\s*=\s*(['\"])(.*?)\1",t,re.I|re.S)
            return html.unescape(a.group(2)).strip() if a else ""
    return ""
def cls(n): return "HIGH REVIEW" if n<400 else "EXPANSION REVIEW" if n<650 else "INTENT REVIEW" if n<900 else "WORD COUNT OK"
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",default=".");a=p.parse_args();repo=Path(a.repo).resolve();site=repo/"cloudflare-site"
    ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"};urls=[x.text.strip() for x in ET.parse(site/"sitemap.xml").findall(".//s:loc",ns) if x.text];rows=[]
    for u in urls:
        path=urlparse(u).path
        if path.startswith("/blog/"): continue
        rel=path.strip("/");f=site/"index.html" if not rel else site/rel/"index.html"
        if not f.exists():
            rows.append(dict(url=u,file=str(f.relative_to(repo)),status="MISSING",visible_words=0,classification="INVESTIGATE",title="",h1="",meta_description="",canonical="",notes="Sitemap URL has no matching Cloudflare index.html"));continue
        raw=f.read_text(encoding="utf-8");mm=re.search(r"<main\b.*?</main>",raw,re.I|re.S);scope=mm.group(0) if mm else raw;n=len(WORD_RE.findall(txt(scope)))
        tm=re.search(r"<title[^>]*>(.*?)</title>",raw,re.I|re.S);hm=re.search(r"<h1[^>]*>(.*?)</h1>",raw,re.I|re.S);title=txt(tm.group(1)) if tm else "";h1=txt(hm.group(1)) if hm else ""
        meta=attr_tag(raw,"meta","name","description","content");canon=attr_tag(raw,"link","rel","canonical","href");notes=[] if h1 else ["missing H1"]
        if not meta:notes.append("missing meta description")
        if not canon:notes.append("missing canonical")
        rows.append(dict(url=u,file=str(f.relative_to(repo)),status="OK",visible_words=n,classification=cls(n),title=title,h1=h1,meta_description=meta,canonical=canon,notes="; ".join(notes)))
    out=repo/"reports/content_quality_audit_v21.csv";out.parent.mkdir(exist_ok=True)
    with out.open("w",newline="",encoding="utf-8-sig") as fh:w=csv.DictWriter(fh,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("TBS CONTENT QUALITY AUDIT v21.1");print("="*40);print(f"Sitemap URLs audited: {len(rows)} (BookingKoala /blog/ content excluded)")
    for k in ["HIGH REVIEW","EXPANSION REVIEW","INTENT REVIEW","WORD COUNT OK","INVESTIGATE"]:print(f"{k}: {sum(r['classification']==k for r in rows)}")
    print("\nPriority pages:")
    for r in sorted(rows,key=lambda x:x["visible_words"]):
        if r["classification"] in ("HIGH REVIEW","EXPANSION REVIEW","INVESTIGATE"):print(f"  {r['visible_words']:4}  {r['classification']:16} {urlparse(r['url']).path}")
    print(f"\nReport: {out}")
if __name__=="__main__":main()
