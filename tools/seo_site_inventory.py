#!/usr/bin/env python3
"""Refresh inventory from public website's production branch, without paid API dependencies."""
import datetime as dt, json, subprocess, xml.etree.ElementTree as ET
from pathlib import Path

def main():
    proc=subprocess.run(['git','show','FETCH_HEAD:cloudflare-site/sitemap.xml'],capture_output=True,text=True)
    if proc.returncode:
        proc=subprocess.run(['git','show','origin/cloudflare-production:cloudflare-site/sitemap.xml'],capture_output=True,text=True)
    if proc.returncode:raise SystemExit('ERROR: fetch origin cloudflare-production before generating inventory: '+proc.stderr)
    root=ET.fromstring(proc.stdout)
    urls=[]
    for element in root.iter():
        if element.tag.rsplit('}',1)[-1]=='loc' and element.text:
            url=element.text.strip()
            if url.startswith('https://tampabayshine.com/') and url not in urls:urls.append(url)
    if len(urls)<60:raise SystemExit(f'ERROR: unexpectedly small production sitemap ({len(urls)} URLs)')
    output=Path('cloudflare-site/seo-dashboard/data/site-inventory.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    payload={'schema_version':2,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),'source':'origin/cloudflare-production:cloudflare-site/sitemap.xml','scope':'Submitted sitemap inventory; indexing statuses only for URLs with inspection data','count':len(urls),'urls':urls}
    output.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'Sitemap inventory refreshed: {len(urls)} production URLs')
if __name__=='__main__':main()
