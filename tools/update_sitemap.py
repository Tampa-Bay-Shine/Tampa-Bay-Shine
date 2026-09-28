from pathlib import Path
import sys, datetime, xml.etree.ElementTree as ET
from urllib.parse import urlparse

NS='http://www.sitemaps.org/schemas/sitemap/0.9'
ET.register_namespace('',NS)

def main():
    if len(sys.argv)<3:
        raise SystemExit('Usage: python tools/update_sitemap.py cloudflare-site /slug [/slug2 ...]')
    root=Path(sys.argv[1]); sitemap=root/'sitemap.xml'
    tree=ET.parse(sitemap); urlset=tree.getroot()
    wanted={x.rstrip('/') or '/' for x in sys.argv[2:]}
    today=datetime.date.today().isoformat(); found=set()
    for url in urlset.findall(f'{{{NS}}}url'):
        loc=url.find(f'{{{NS}}}loc')
        if loc is None or not loc.text: continue
        path=urlparse(loc.text).path.rstrip('/') or '/'
        if path in wanted:
            lm=url.find(f'{{{NS}}}lastmod')
            if lm is None: lm=ET.SubElement(url,f'{{{NS}}}lastmod')
            lm.text=today; found.add(path)
    missing=wanted-found
    if missing: raise SystemExit('URLs not found in sitemap: '+', '.join(sorted(missing)))
    tree.write(sitemap,encoding='utf-8',xml_declaration=True)
    print('Updated lastmod to',today,'for',', '.join(sorted(found)))

if __name__=='__main__':
    main()
