from pathlib import Path
import argparse

GA4="G-XK4CTL9KWM"
ADS="AW-17001979579"
EVENTS=["booknow_click","phone_click","contact_click","commercial_quote_start","coupon_click","review_click"]
DOMAINS=["tampabayshine.com","tampabayshine.bookingkoala.com","booking.tampabayshine.com"]

# Internal operational apps intentionally do not carry the production
# marketing analytics stack; tracking them would contaminate GA4/Ads data.
INTERNAL_ROUTE_PREFIXES = ("seo-dashboard",)

def is_internal_html(path, site):
    rel = path.relative_to(site).as_posix()
    return any(rel == f"{p}/index.html" or rel.startswith(p + "/") for p in INTERNAL_ROUTE_PREFIXES)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("repo",nargs="?",default=".")
    a=ap.parse_args()
    repo=Path(a.repo).resolve()
    site=repo/"cloudflare-site"
    errors=[]
    html=list(site.rglob("*.html"))
    checked_html=[p for p in html if not is_internal_html(p,site)]
    for p in checked_html:
        s=p.read_text(encoding="utf-8",errors="ignore")
        if s.count("TBS_GOOGLE_TAG_START")!=1:
            errors.append(f"{p.relative_to(repo)}: Google tag marker count={s.count('TBS_GOOGLE_TAG_START')}")
        if GA4 not in s: errors.append(f"{p.relative_to(repo)}: missing GA4 ID")
        if ADS not in s: errors.append(f"{p.relative_to(repo)}: missing Ads ID")
        for d in DOMAINS:
            if d not in s: errors.append(f"{p.relative_to(repo)}: missing linker domain {d}")
    js=(site/"assets/js/main.js").read_text(encoding="utf-8",errors="ignore")
    for ev in EVENTS:
        if ev not in js: errors.append(f"main.js: missing {ev}")
    if "window.gtag('event'" not in js: errors.append("main.js: missing GA4 forwarding")
    if "send_to:'G-XK4CTL9KWM'" not in js: errors.append("main.js: missing GA4 send_to target")
    if "new URL(h,location.href)" not in js: errors.append("main.js: transaction classifier must support absolute production URLs")
    print("TAMPA BAY SHINE ANALYTICS REGRESSION")
    print("="*40)
    print("HTML pages:",len(html))
    print("Marketing pages checked:",len(checked_html))
    print("Internal pages excluded:",len(html)-len(checked_html))
    print("Errors:",len(errors))
    for e in errors: print("ERROR:",e)
    print("RESULT:","PASS" if not errors else "FAIL")
    return 0 if not errors else 1

if __name__=="__main__":
    raise SystemExit(main())
