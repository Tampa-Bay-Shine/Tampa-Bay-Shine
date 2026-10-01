
from pathlib import Path
from bs4 import BeautifulSoup
import argparse, re

TARGETS = {
    "/": {
        "path":"index.html",
        "required_links":[
            "/standard-cleaning-services-tampa/",
            "/deep-cleaning-services-tampa/",
            "/move-out-cleaning-tampa-1/",
            "/office-cleaning/",
            "/locations/",
        ],
        "answer":True,
    },
    "/services": {
        "path":"services/index.html",
        "required_links":[
            "/standard-cleaning-services-tampa/",
            "/deep-cleaning-services-tampa/",
            "/move-out-cleaning-tampa-1/",
            "/office-cleaning/",
            "/commercial-cleaning-tampa/",
            "/locations/",
            "/checklist/",
        ],
        "answer":True,
    },
    "/standard-cleaning-services-tampa":{"path":"standard-cleaning-services-tampa/index.html","answer":True},
    "/deep-cleaning-services-tampa":{"path":"deep-cleaning-services-tampa/index.html","answer":True},
    "/move-out-cleaning-tampa-1":{"path":"move-out-cleaning-tampa-1/index.html","answer":True},
    "/office-cleaning":{"path":"office-cleaning/index.html","answer":True},
    "/commercial-cleaning-tampa":{"path":"commercial-cleaning-tampa/index.html","answer":True},
    "/locations":{"path":"locations/index.html","answer":True},
}

def clean(s):
    return re.sub(r"\s+"," ",s or "").strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",nargs="?",default="cloudflare-site")
    a=ap.parse_args()
    root=Path(a.root)

    errors=[];warnings=[]
    print("TAMPA BAY SHINE PAGE-INTENT AUDIT")
    print("=================================")

    for route,cfg in TARGETS.items():
        p=root/cfg["path"]
        if not p.exists():
            errors.append(f"{route}: missing file")
            continue
        text=p.read_text(encoding="utf-8",errors="ignore")
        soup=BeautifulSoup(text,"html.parser")
        title=clean(soup.title.get_text(" ") if soup.title else "")
        desc=soup.find("meta",attrs={"name":"description"})
        desc=clean(desc.get("content","") if desc else "")
        h1s=soup.find_all("h1")
        blocks=soup.select(".tbs-answer-block")
        links={a.get("href","") for a in soup.find_all("a",href=True)}

        if not (30 <= len(title) <= 65):
            errors.append(f"{route}: title length={len(title)}")
        if not (90 <= len(desc) <= 170):
            errors.append(f"{route}: meta description length={len(desc)}")
        if len(h1s)!=1:
            errors.append(f"{route}: H1 count={len(h1s)}")
        if cfg.get("answer") and not blocks:
            errors.append(f"{route}: missing concise answer block")

        for href in cfg.get("required_links",[]):
            if href not in links:
                errors.append(f"{route}: missing required contextual/internal link {href}")

        print(f"{route}: title={len(title)} desc={len(desc)} h1={len(h1s)} answer_blocks={len(blocks)}")

    print("")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    if errors:
        for x in errors: print("ERROR:",x)
        raise SystemExit(1)
    print("RESULT: PASS")

if __name__=="__main__":
    main()
