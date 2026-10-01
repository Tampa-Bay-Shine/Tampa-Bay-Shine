
from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
import argparse,re,html as htmlmod,urllib.parse,sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import faq_consistency as fc

LOCAL_NAMES=r"(tampa bay|south tampa|tampa|brandon|riverview|ruskin|apollo beach|sun city center|wesley chapel|florida|fl)"

def route_for(root,p):
    rel=p.relative_to(root).as_posix()
    return "/" if rel=="index.html" else "/"+p.parent.relative_to(root).as_posix()
def clean(s): return re.sub(r"\s+"," ",s or "").strip()
def norm_exact(s):
    s=htmlmod.unescape(s or "").replace("’","'").replace("‘","'").lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()
def norm_family(s):
    s=htmlmod.unescape(s or "").lower()
    s=re.sub(r"\b"+LOCAL_NAMES+r"\b"," ",s)
    s=re.sub(r"[^a-z0-9]+"," ",s)
    return clean(s)
def visible_words(soup):
    x=BeautifulSoup(str(soup),"html.parser")
    for tag in x(["script","style","noscript","svg"]):tag.decompose()
    return len(clean(x.get_text(" ")).split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",nargs="?",default="cloudflare-site")
    a=ap.parse_args();root=Path(a.root)
    routes=set(route_for(root,p) for p in root.rglob("index.html"))
    pages=[];exactq=defaultdict(list);familyq=defaultdict(list);exacta=defaultdict(list);inbound=defaultdict(int)

    for p in sorted(root.rglob("index.html")):
        route=route_for(root,p);text=p.read_text(encoding="utf-8",errors="ignore")
        soup=BeautifulSoup(text,"html.parser")
        robots=soup.find("meta",attrs={"name":"robots"})
        if robots and "noindex" in (robots.get("content","").lower()):continue

        title=clean(soup.title.get_text(" ") if soup.title else "")
        desc=soup.find("meta",attrs={"name":"description"});desc=clean(desc.get("content","") if desc else "")
        faqs=fc.visible_faqs(text);schema=fc.schema_questions(text)

        for q,ans in faqs:
            exactq[norm_exact(q)].append((route,q))
            familyq[norm_family(q)].append((route,q))
            exacta[norm_exact(ans)].append((route,q))

        for at in soup.find_all("a",href=True):
            h=at["href"].strip();pr=urllib.parse.urlparse(h)
            if pr.netloc and pr.netloc not in {"tampabayshine.com","www.tampabayshine.com"}:continue
            if not pr.netloc and not h.startswith("/"):continue
            path=(pr.path or "/").rstrip("/") or "/"
            if path in routes:inbound[path]+=1

        pages.append(dict(
            route=route,words=visible_words(soup),title_len=len(title),desc_len=len(desc),
            h1_count=len(soup.find_all("h1")),canonical_count=len(soup.find_all("link",rel="canonical")),
            faq_count=len(faqs),schema_count=len(schema),faqpage_count=fc.faqpage_count(text),
            qmatch=fc.faq_questions_match(text),amatch=fc.faq_answers_match(text),
            marked_count=len(soup.select('details[data-tbs-faq-item="1"]'))
        ))

    issues=[]
    for x in pages:
        r=x["route"]
        if x["h1_count"]!=1 and r not in {"/terms","/privacy-policy"}:issues.append(f"{r}: H1 count={x['h1_count']}")
        if x["canonical_count"]!=1:issues.append(f"{r}: canonical count={x['canonical_count']}")
        if x["title_len"]<30 or x["title_len"]>65:issues.append(f"{r}: title length={x['title_len']}")
        if x["desc_len"]<90 or x["desc_len"]>170:issues.append(f"{r}: meta description length={x['desc_len']}")
        if x["words"]<300:issues.append(f"{r}: thin visible content ~{x['words']} words")
        if x["faq_count"] or x["schema_count"]:
            if x["marked_count"]!=x["faq_count"]:issues.append(f"{r}: FAQ HTML not fully canonical-marked ({x['marked_count']} marked vs {x['faq_count']} detected)")
            if x["faqpage_count"]!=1:issues.append(f"{r}: expected exactly 1 FAQPage schema, found {x['faqpage_count']}")
            if x["faq_count"]!=x["schema_count"]:issues.append(f"{r}: visible FAQ count {x['faq_count']} != schema question count {x['schema_count']}")
            if not x["qmatch"]:issues.append(f"{r}: visible FAQ questions do not match FAQPage schema")
            if not x["amatch"]:issues.append(f"{r}: visible FAQ answers do not match FAQPage schema")
        if inbound[r]==0 and r!="/":issues.append(f"{r}: no internal inbound links detected")

    exact_dups=[v for k,v in exactq.items() if k and len(v)>1]
    exact_ans=[v for k,v in exacta.items() if k and len(v)>1]
    family_dups=[v for k,v in familyq.items() if k and len(v)>1 and len({q.lower() for r,q in v})>1]

    print("TAMPA BAY SHINE SEO / AI CONTENT AUDIT V6")
    print("=========================================")
    print(f"Indexable HTML pages: {len(pages)}")
    print(f"Pages with visible FAQs: {sum(1 for x in pages if x['faq_count'])}")
    print(f"Visible FAQ questions: {sum(x['faq_count'] for x in pages)}")
    print(f"Exact duplicate FAQ question groups: {len(exact_dups)}")
    print(f"Exact-normalized duplicate FAQ answer groups: {len(exact_ans)}")
    print(f"Local-family FAQ similarity groups (review, not automatic errors): {len(family_dups)}")
    print(f"General content/metadata/internal-link issues: {len(issues)}")
    print("")
    if exact_dups:
        print("EXACT DUPLICATE FAQ QUESTIONS")
        for g in exact_dups[:50]:print(" - "+" | ".join(f"{r}: {q}" for r,q in g))
        print("")
    if exact_ans:
        print("EXACT DUPLICATE FAQ ANSWERS")
        for g in exact_ans[:40]:print(" - "+" | ".join(f"{r}: {q}" for r,q in g))
        print("")
    if family_dups:
        print("LOCAL-FAMILY FAQ SIMILARITIES (INFORMATIONAL)")
        for g in family_dups[:30]:print(" - "+" | ".join(f"{r}: {q}" for r,q in g))
        print("")
    if issues:
        print("CONTENT / TECHNICAL CONTENT ISSUES")
        for i in issues[:200]:print(" - "+i)

    print("")
    print("Interpretation:")
    print(" - Canonical FAQ discovery includes both marked items and legacy details.faq.")
    print(" - Every FAQ page should end with marked visible FAQ items and exactly one matching FAQPage schema.")
    print(" - Local-family similarities remain informational, not automatic SEO defects.")

if __name__=="__main__":
    main()
