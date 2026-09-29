
from pathlib import Path
import argparse

TERMS=("st. petersburg","clearwater","carrollwood")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    a=ap.parse_args()
    repo=Path(a.repo).resolve()
    site=repo/"cloudflare-site"
    hits=[]
    for p in sorted(site.rglob("*.html")):
        txt=p.read_text(encoding="utf-8",errors="ignore").lower()
        route="/" if p==site/"index.html" else "/"+p.parent.relative_to(site).as_posix()
        for term in TERMS:
            if term in txt:
                hits.append((route,term))
    if hits:
        for route,term in hits:
            print(f"FAIL {route}: {term}")
        return 1
    print("PASS: no St. Petersburg, Clearwater, or Carrollwood references in public HTML")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
