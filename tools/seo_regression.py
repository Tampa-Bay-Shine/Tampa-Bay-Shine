from pathlib import Path
import json, re, sys
from bs4 import BeautifulSoup

REQUIRED_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000",
    "X-Frame-Options": "SAMEORIGIN",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
REQUIRED_CSP_PARTS = ("frame-ancestors 'self'", "base-uri 'self'", "object-src 'none'")

def main():
    repo = Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    site = repo / "cloudflare-site"
    home = site / "index.html"
    headers = site / "_headers"
    issues=[]; warnings=[]

    if not home.is_file():
        issues.append("homepage missing")
    else:
        text=home.read_text(encoding="utf-8",errors="ignore")
        s=BeautifulSoup(text,"html.parser")

        title=s.title.get_text(strip=True) if s.title else ""
        if not title:
            issues.append("homepage title missing")
        elif len(title)>60:
            issues.append(f"homepage title too long: {len(title)} chars")

        md=s.find("meta",attrs={"name":"description"})
        desc=md.get("content","").strip() if md else ""
        if not desc:
            issues.append("homepage meta description missing")
        elif len(desc)>150:
            warnings.append(f"homepage meta description is {len(desc)} chars; keep concise for SERP width")

        if not s.find("meta",attrs={"property":"og:image"}):
            issues.append("homepage og:image missing")
        if not s.find("meta",attrs={"name":"twitter:card"}):
            issues.append("homepage twitter:card missing")
        if not s.find("link",attrs={"rel":"preload","as":"image"}):
            issues.append("homepage image preload missing")

        skip=s.find("a",class_="skip-link")
        target=s.find(id="main-content")
        if not skip or skip.get("href")!="#main-content" or not target:
            issues.append("homepage skip-to-content link/target missing")

        levels=[]
        for h in s.find_all(re.compile(r"^h[1-6]$")):
            levels.append((int(h.name[1]),h.get_text(" ",strip=True)[:80]))
        for (a,ta),(b,tb) in zip(levels,levels[1:]):
            if b>a+1:
                issues.append(f"homepage heading level skips h{a}->h{b}: {ta!r} -> {tb!r}")
                break

        for sc in s.find_all("script",attrs={"type":"application/ld+json"}):
            try:
                json.loads(sc.get_text())
            except Exception as e:
                issues.append(f"invalid homepage JSON-LD: {e}")

    if not headers.is_file():
        issues.append("_headers missing")
    else:
        ht=headers.read_text(encoding="utf-8",errors="ignore")
        for name,value in REQUIRED_HEADERS.items():
            if not re.search(rf"(?im)^\s*{re.escape(name)}:\s*{re.escape(value)}\s*$",ht):
                issues.append(f"missing required security header: {name}: {value}")
        csp=re.search(r"(?im)^\s*Content-Security-Policy:\s*(.+)$",ht)
        if not csp:
            issues.append("Content-Security-Policy missing")
        else:
            policy=csp.group(1)
            for part in REQUIRED_CSP_PARTS:
                if part not in policy:
                    issues.append(f"CSP missing directive: {part}")

    print("TAMPA BAY SHINE SEO REGRESSION")
    print("="*36)
    print("Errors:",len(issues))
    print("Warnings:",len(warnings))
    for x in issues: print("ERROR:",x)
    for x in warnings: print("WARN:",x)
    if issues:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
