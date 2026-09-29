from __future__ import annotations
import argparse, datetime as dt, json, urllib.error, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path

ENDPOINT="https://api.indexnow.org/indexnow"
UA="TampaBayShine-IndexNow/1.0"

def cfg(repo):
    return json.loads((repo/"site-management"/"release_targets.json").read_text(encoding="utf-8"))

def key_from_site(site):
    found=[]
    for p in site.glob("*.txt"):
        v=p.read_text(encoding="utf-8").strip()
        if p.stem==v and 8<=len(v)<=128:
            found.append((v,p))
    if len(found)!=1:
        raise SystemExit(f"ERROR: expected exactly one root IndexNow key file, found {len(found)}")
    return found[0]

def parse_sitemap(data, host):
    root=ET.fromstring(data)
    out=[]; seen=set()
    for e in root.iter():
        if e.tag.endswith("loc") and e.text:
            u=e.text.strip(); p=urllib.parse.urlparse(u)
            if p.scheme!="https" or p.netloc.lower()!=host.lower():
                raise SystemExit(f"ERROR: sitemap URL is not canonical for {host}: {u}")
            if u not in seen:
                seen.add(u); out.append(u)
    if not out: raise SystemExit("ERROR: sitemap contains no URLs")
    return out

def get(url, timeout):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.status,r.read()
    except urllib.error.HTTPError as e:
        return e.code,e.read()

def post(url,payload,timeout):
    body=json.dumps(payload,separators=(",",":")).encode()
    req=urllib.request.Request(url,data=body,method="POST",headers={
        "Content-Type":"application/json; charset=utf-8","User-Agent":UA})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            return r.status,r.read()
    except urllib.error.HTTPError as e:
        return e.code,e.read()

def main():
    ap=argparse.ArgumentParser(description="Validate and submit Tampa Bay Shine URLs to IndexNow.")
    ap.add_argument("--repo",default=".")
    ap.add_argument("--live",action="store_true",help="Send the IndexNow request; otherwise dry-run only.")
    ap.add_argument("--url",action="append",dest="selected",help="Absolute production URL or path; repeatable.")
    ap.add_argument("--endpoint",default=ENDPOINT)
    ap.add_argument("--timeout",type=int,default=30)
    a=ap.parse_args()

    repo=Path(a.repo).resolve(); site=repo/"cloudflare-site"
    if not site.is_dir(): raise SystemExit(f"ERROR: missing {site}")
    c=cfg(repo); prod=c["production_url"].rstrip("/"); host=urllib.parse.urlparse(prod).netloc
    if not host or "pages.dev" in host.lower(): raise SystemExit(f"ERROR: refusing non-canonical host: {host}")

    key,keyfile=key_from_site(site)
    keyloc=f"{prod}/{keyfile.name}"
    live_sitemap=f"{prod}/sitemap.xml"

    if a.live:
        ks,kb=get(keyloc,a.timeout)
        if ks!=200: raise SystemExit(f"ERROR: key file returned HTTP {ks}")
        if kb.decode().strip()!=key: raise SystemExit("ERROR: live key contents do not match local key")
        ss,sb=get(live_sitemap,a.timeout)
        if ss!=200: raise SystemExit(f"ERROR: live sitemap returned HTTP {ss}")
        urls=parse_sitemap(sb,host); source=live_sitemap
    else:
        sm=site/"sitemap.xml"
        urls=parse_sitemap(sm.read_bytes(),host); source=str(sm)

    if a.selected:
        sset=set(urls); chosen=[]
        for raw in a.selected:
            u=prod+raw if raw.startswith("/") else raw
            candidates=[u,u.rstrip("/"),u.rstrip("/")+"/"]
            match=next((x for x in candidates if x in sset),None)
            if not match: raise SystemExit(f"ERROR: selected URL is not in sitemap: {u}")
            if match not in chosen: chosen.append(match)
        urls=chosen

    print("TAMPA BAY SHINE INDEXNOW")
    print("="*34)
    print("Mode:","LIVE SUBMISSION" if a.live else "DRY RUN")
    print("Production host:",host)
    print("Sitemap source:",source)
    print("Key location:",keyloc)
    print("URLs:",len(urls))
    print("Endpoint:",a.endpoint)

    if not a.live:
        print("\nDRY RUN ONLY: nothing was sent.")
        print("Use --live only after production deployment is verified.")
        return 0

    result={"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
            "host":host,"sitemap_source":source,"key_location":keyloc,
            "endpoint":a.endpoint,"url_count":len(urls),"urls":urls,"requests":[]}

    failures=0
    for i in range(0,len(urls),10000):
        batch=urls[i:i+10000]
        payload={"host":host,"key":key,"keyLocation":keyloc,"urlList":batch}
        status,body=post(a.endpoint,payload,a.timeout)
        accepted=status in (200,202)
        if not accepted: failures+=1
        txt=body.decode(errors="replace").strip()
        result["requests"].append({"batch":i//10000+1,"url_count":len(batch),
                                   "http_status":status,"accepted":accepted,"response_body":txt})
        print(f"Batch {i//10000+1}: {'ACCEPTED' if accepted else 'FAILED'} HTTP {status} ({len(batch)} URLs)")
        if txt: print("Response:",txt[:1000])

    reports=repo/"reports"; reports.mkdir(exist_ok=True)
    stamp=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rp=reports/f"indexnow_submission_{stamp}.json"
    rp.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Report:",rp)
    if failures:
        print("\nRESULT: FAILED"); return 1
    print("\nRESULT: ACCEPTED")
    print("Receipt confirmed; crawl timing and indexing are not guaranteed.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
