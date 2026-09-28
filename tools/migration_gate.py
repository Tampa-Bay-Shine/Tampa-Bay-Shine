
from pathlib import Path
import argparse, json, re, socket, ssl, subprocess, sys, urllib.request, urllib.error
from datetime import datetime, timezone

DEV_BRANCH="cloudflare-staging"
PROD_BRANCH="cloudflare-production"
SITE_DIR="cloudflare-site"
DEV_URL="https://tampa-bay-shine-staging.pages.dev"
PROD_URL="https://tampabayshine.com"
BOOKING_URL="https://booking.tampabayshine.com"
BOOKING_IPS={"162.159.141.169","172.66.1.165"}
TX=["/booknow","/login","/gift-card","/referrals","/floor-calculator"]
STALE={
"airbnb-cleaning-st-petersburg","apartment-cleaning-st-petersburg",
"house-cleaning-st-petersburg-fl","move-out-cleaning-st-petersburg",
"office-cleaning-st-petersburg"}
CHECK=["/","/services","/locations","/standard-cleaning-services-tampa",
"/move-out-cleaning-tampa-1","/office-cleaning","/window-cleaning",
"/privacy-policy","/terms","/sms-opt-in"]

def cmd(a,cwd,t=120):
    return subprocess.run(a,cwd=str(cwd),text=True,capture_output=True,timeout=t)

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"TBS-Gate/2.5.7"})
    try:
        with urllib.request.urlopen(req,timeout=15,context=ssl.create_default_context()) as r:
            return {"ok":200<=r.status<400,"status":r.status,"url":r.geturl(),
                    "headers":dict(r.headers.items()),
                    "body":r.read(250000).decode("utf-8","ignore"),"error":""}
    except urllib.error.HTTPError as e:
        return {"ok":False,"status":e.code,"url":url,"headers":dict(e.headers.items()),
                "body":"","error":str(e)}
    except Exception as e:
        return {"ok":False,"status":0,"url":url,"headers":{},"body":"","error":repr(e)}

def noindex(r):
    hs=" ".join(f"{k}:{v}" for k,v in r.get("headers",{}).items()).lower().replace(" ","")
    body=r.get("body","").lower()
    return "x-robots-tag:noindex" in hs or bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',body))

def add(out,name,ok,detail="",kind="BLOCK"):
    out.append({"name":name,"ok":bool(ok),"detail":detail,"kind":kind})

def common(repo,out):
    site=repo/SITE_DIR
    add(out,"cloudflare-site exists",(site/"index.html").exists(),str(site))
    stale=[x for x in sorted(STALE) if (site/x).exists()]
    add(out,"No stale St. Petersburg directories",not stale,", ".join(stale) or "none")
    sm=(site/"sitemap.xml").read_text(encoding="utf-8",errors="ignore") if (site/"sitemap.xml").exists() else ""
    add(out,"No St. Petersburg URLs in sitemap","st-petersburg" not in sm.lower())

    rd=(site/"_redirects").read_text(encoding="utf-8",errors="ignore") if (site/"_redirects").exists() else ""
    bad=[r for r in TX if f"{r} {BOOKING_URL}{r}" not in rd]
    add(out,"Transactional redirects target booking subdomain",not bad,", ".join(bad) or "all correct")

    val=repo/"tools"/"validate_site.py"
    if val.exists():
        p=cmd([sys.executable,str(val),str(site)],repo,180)
        add(out,"validate_site.py passes",p.returncode==0,(p.stdout+p.stderr)[-2500:])
    else:
        add(out,"validate_site.py present",False,"tools/validate_site.py missing")

    report=repo/"ahrefs_preflight_report.json"
    if report.exists():
        try:
            d=json.loads(report.read_text(encoding="utf-8"))
            add(out,"Ahrefs-style preflight clean",d.get("errors")==0 and d.get("warnings")==0,
                f"errors={d.get('errors')} warnings={d.get('warnings')} pages={d.get('pages')}")
        except Exception as e:
            add(out,"Ahrefs-style preflight readable",False,repr(e))
    else:
        add(out,"Ahrefs-style preflight report present",False,"Run Option 36 first.")

def booking(out):
    try:
        ips=set(socket.gethostbyname_ex("booking.tampabayshine.com")[2])
        add(out,"Booking DNS resolves to BK",BOOKING_IPS.issubset(ips),"resolved="+",".join(sorted(ips)))
    except Exception as e:
        add(out,"Booking DNS resolves to BK",False,repr(e))
    for pth in ["/","/login","/booknow"]:
        r=fetch(BOOKING_URL+pth)
        add(out,f"Booking HTTPS reachable {pth}",r["ok"],f"HTTP {r['status']} -> {r['url']} {r['error']}")

def manual(repo,out):
    p=repo/"site-management"/"release_gate_manual.json"
    try:
        d=json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        d={}
    checks={
    "bk_support_domain_change_confirmed":"BK support confirmed domain/provider/admin behavior",
    "bk_ssl_valid":"booking.tampabayshine.com SSL validated",
    "bk_admin_login_tested":"BK admin login tested",
    "bk_provider_app_tested":"Provider app/session tested",
    "bk_customer_login_tested":"Customer login tested",
    "bk_owner_sender_email_tested":"owner@tampabayshine.com sender test passed",
    "bk_sms_links_tested":"BK SMS links tested",
    "bk_recurring_booking_tested":"Recurring booking/job visibility tested"}
    for k,label in checks.items():
        add(out,label,d.get(k) is True,f"{k}={d.get(k,False)}; edit {p}","MANUAL")

def staging(repo,out):
    b=cmd(["git","branch","--show-current"],repo).stdout.strip()
    add(out,"On development branch",b==DEV_BRANCH,f"current={b}")
    s=cmd(["git","status","--porcelain"],repo).stdout.strip()
    add(out,"Git working tree clean",not s,s or "clean")
    common(repo,out)
    hp=(repo/SITE_DIR/"_headers").read_text(encoding="utf-8",errors="ignore")
    add(out,"Development has global noindex",bool(re.search(r"X-Robots-Tag:\s*noindex",hp,re.I)))
    booking(out)
    for pth in CHECK:
        r=fetch(DEV_URL+pth)
        add(out,f"Dev reachable {pth}",r["ok"],f"HTTP {r['status']} -> {r['url']}")
        if pth!="/sms-opt-in":
            add(out,f"Dev noindex {pth}",noindex(r))
    manual(repo,out)

def production(repo,out):
    b=cmd(["git","branch","--show-current"],repo).stdout.strip()
    add(out,"On production branch",b==PROD_BRANCH,f"current={b}")
    s=cmd(["git","status","--porcelain"],repo).stdout.strip()
    add(out,"Git working tree clean",not s,s or "clean")
    common(repo,out)
    hp=(repo/SITE_DIR/"_headers").read_text(encoding="utf-8",errors="ignore")
    add(out,"Production global noindex removed",not bool(re.search(r"X-Robots-Tag:\s*noindex",hp,re.I)))
    booking(out)
    manual(repo,out)

def postcut(out):
    booking(out)
    for pth in CHECK:
        r=fetch(PROD_URL+pth)
        add(out,f"Production reachable {pth}",r["ok"],f"HTTP {r['status']} -> {r['url']}")
        add(out,f"Production indexing state {pth}",noindex(r) if pth=="/sms-opt-in" else not noindex(r),
            "expected noindex" if pth=="/sms-opt-in" else "expected indexable")
    for pth in TX:
        r=fetch(PROD_URL+pth)
        add(out,f"Redirect {pth} -> booking",r["url"].startswith(BOOKING_URL+pth),r["url"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo",default=".")
    ap.add_argument("--phase",choices=["staging","production","post-cutover"],default="staging")
    a=ap.parse_args()
    repo=Path(a.repo).resolve()
    out=[]
    {"staging":staging,"production":production}.get(a.phase,lambda r,o:postcut(o))(repo,out)

    block=[x for x in out if not x["ok"] and x["kind"]=="BLOCK"]
    man=[x for x in out if not x["ok"] and x["kind"]=="MANUAL"]
    verdict="RED" if block else ("YELLOW" if man else "GREEN")
    print("\nTAMPA BAY SHINE MIGRATION GATE")
    print("="*32)
    print("Phase:",a.phase)
    for x in out:
        mark="PASS" if x["ok"] else ("WAIT" if x["kind"]=="MANUAL" else "FAIL")
        print(f"[{mark}] {x['name']}")
        if not x["ok"] and x["detail"]:
            print("       "+x["detail"].replace("\n","\n       "))
    print("\nVERDICT:",verdict)
    dest=repo/"reports"/f"migration_gate_{a.phase}.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),
        "phase":a.phase,"verdict":verdict,"results":out},indent=2),encoding="utf-8")
    print("Report:",dest)
    return 0 if verdict=="GREEN" else (2 if verdict=="YELLOW" else 1)

if __name__=="__main__":
    raise SystemExit(main())
