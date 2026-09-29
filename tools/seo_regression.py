from pathlib import Path
import json, re, sys
from bs4 import BeautifulSoup

PRIORITY_PAGES = [
    ("homepage", "index.html"),
    ("house cleaning", "standard-cleaning-services-tampa/index.html"),
    ("deep cleaning", "deep-cleaning-services-tampa/index.html"),
    ("move-out Tampa", "move-out-cleaning-tampa/index.html"),
    ("move-out regional hub", "move-out-cleaning-tampa-1/index.html"),
    ("office cleaning", "office-cleaning/index.html"),
    ("commercial cleaning", "commercial-cleaning-tampa/index.html"),
    ("locations", "locations/index.html"),
]

REQUIRED_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000",
    "X-Frame-Options": "SAMEORIGIN",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
REQUIRED_CSP_PARTS = ("frame-ancestors 'self'", "base-uri 'self'", "object-src 'none'")

def check_page(site, label, rel, issues, warnings):
    p = site / rel
    if not p.is_file():
        issues.append(f"{label}: missing {rel}")
        return
    raw = p.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    if not title:
        issues.append(f"{label}: title missing")
    elif label == "homepage" and len(title) > 60:
        issues.append(f"{label}: title too long: {len(title)} chars")
    elif len(title) > 65:
        warnings.append(f"{label}: title is {len(title)} chars")
    md = soup.find("meta", attrs={"name":"description"})
    desc = (md.get("content") or "").strip() if md else ""
    if not desc:
        issues.append(f"{label}: meta description missing")
    elif len(desc) > 165:
        warnings.append(f"{label}: meta description is {len(desc)} chars")
    canon = soup.find("link", attrs={"rel":"canonical"})
    if not canon or not (canon.get("href") or "").startswith("https://tampabayshine.com"):
        issues.append(f"{label}: production canonical missing/invalid")
    if len(soup.find_all("h1")) != 1:
        issues.append(f"{label}: expected exactly one H1")
    if not soup.find("meta", attrs={"property":"og:image"}):
        issues.append(f"{label}: og:image missing")
    if not soup.find("meta", attrs={"name":"twitter:card"}):
        issues.append(f"{label}: twitter:card missing")
    hero = soup.find("img", id="primaryimage")
    if hero and not soup.find("link", attrs={"rel":"preload","as":"image"}):
        issues.append(f"{label}: primary image preload missing")
    for sc in soup.find_all("script", attrs={"type":"application/ld+json"}):
        try:
            json.loads(sc.get_text())
        except Exception as exc:
            issues.append(f"{label}: invalid JSON-LD: {exc}")
    levels = [(int(h.name[1]), h.get_text(" ", strip=True)[:80]) for h in soup.find_all(re.compile(r"^h[1-6]$"))]
    for (a,ta),(b,tb) in zip(levels, levels[1:]):
        if b > a + 1:
            msg = f"{label}: heading skip h{a}->h{b}: {ta!r} -> {tb!r}"
            if label == "homepage": issues.append(msg)
            else: warnings.append(msg)
            break
    if label == "homepage":
        skip = soup.find("a", class_="skip-link")
        target = soup.find(id="main-content")
        if not skip or skip.get("href") != "#main-content" or not target:
            issues.append("homepage: skip-to-content link/target missing")

def main():
    repo = Path(sys.argv[1] if len(sys.argv)>1 else ".").resolve()
    site = repo / "cloudflare-site"
    headers = site / "_headers"
    issues=[]; warnings=[]
    for label, rel in PRIORITY_PAGES:
        check_page(site, label, rel, issues, warnings)
    if not headers.is_file():
        issues.append("_headers missing")
    else:
        ht = headers.read_text(encoding="utf-8", errors="ignore")
        for name, value in REQUIRED_HEADERS.items():
            if not re.search(rf"(?im)^\s*{re.escape(name)}:\s*{re.escape(value)}\s*$", ht):
                issues.append(f"missing required security header: {name}: {value}")
        csp = re.search(r"(?im)^\s*Content-Security-Policy:\s*(.+)$", ht)
        if not csp:
            issues.append("Content-Security-Policy missing")
        else:
            for part in REQUIRED_CSP_PARTS:
                if part not in csp.group(1): issues.append(f"CSP missing directive: {part}")
    print("TAMPA BAY SHINE SEO REGRESSION")
    print("="*36)
    print("Priority pages:", len(PRIORITY_PAGES))
    print("Errors:", len(issues))
    print("Warnings:", len(warnings))
    for x in issues: print("ERROR:", x)
    for x in warnings: print("WARN:", x)
    print("RESULT:", "FAIL" if issues else "PASS")
    return 1 if issues else 0

if __name__ == "__main__":
    raise SystemExit(main())
