from pathlib import Path
import sys, json, urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else 'cloudflare-site')
    if not root.exists():
        raise SystemExit(f'Not found: {root}')

    htmls=list(root.rglob('index.html'))
    routes=set()
    for p in htmls:
        rel=p.relative_to(root).as_posix()
        route='/' if rel=='index.html' else '/'+p.parent.relative_to(root).as_posix()
        routes.add(route.rstrip('/') or '/')

    redirects=set(); redirect_map={}
    rp=root/'_redirects'
    if rp.exists():
        for line in rp.read_text(encoding='utf-8',errors='ignore').splitlines():
            parts=line.split()
            if parts and not line.lstrip().startswith('#'):
                redirects.add(parts[0].rstrip('/') or '/')
                if len(parts)>=3:
                    redirect_map[parts[0]]=(parts[1],parts[2])

    issues=[]; warnings=[]
    for p in htmls:
        text=p.read_text(encoding='utf-8',errors='ignore')
        s=BeautifulSoup(text,'html.parser')
        rel=p.relative_to(root).as_posix()
        route='/' if rel=='index.html' else '/'+p.parent.relative_to(root).as_posix()

        if not s.title or not s.title.get_text(strip=True): issues.append(f'{route}: missing title')
        descriptions=s.find_all('meta',attrs={'name':'description'})
        if not descriptions: issues.append(f'{route}: missing meta description')
        elif len(descriptions)!=1: issues.append(f'{route}: meta description count={len(descriptions)}')
        canonicals=s.find_all('link',rel='canonical')
        expected_canonical='https://tampabayshine.com/' if route=='/' else 'https://tampabayshine.com'+route
        if not canonicals: issues.append(f'{route}: missing production canonical')
        elif len(canonicals)!=1: issues.append(f'{route}: canonical count={len(canonicals)}')
        elif canonicals[0].get('href','')!=expected_canonical:
            issues.append(f'{route}: canonical {canonicals[0].get("href","")} != {expected_canonical}')
        if not s.find('meta',attrs={'name':'robots'}): issues.append(f'{route}: missing robots')
        h1=len(s.find_all('h1'))
        if route not in {'/terms','/privacy-policy'} and h1!=1: warnings.append(f'{route}: H1 count={h1}')
        if 'cdn.bookingkoala.com/uploads/' in text: issues.append(f'{route}: BookingKoala CDN remains')
        if 'customer-build/' in text or '<bk-root' in text or 'ng-version=' in text: issues.append(f'{route}: BookingKoala runtime leaked')
        for sc in s.find_all('script',attrs={'type':'application/ld+json'}):
            try: json.loads(sc.get_text())
            except Exception: issues.append(f'{route}: invalid JSON-LD')
        for a in s.find_all('a',href=True):
            h=a['href'].strip(); pr=urllib.parse.urlparse(h)
            if pr.netloc and pr.netloc not in {'tampabayshine.com','www.tampabayshine.com'}: continue
            if not pr.netloc and not h.startswith('/'): continue
            path=(pr.path or '/').rstrip('/') or '/'
            if path.startswith('/assets/'): continue
            if path not in routes and path not in redirects: issues.append(f'{route}: unresolved internal link {path}')

    # Every static non-root route must normalize its trailing-slash variant.
    for route in sorted(routes):
        if route=='/': continue
        src=route+'/'
        if redirect_map.get(src)!=(route,'301'):
            issues.append(f'{route}: missing trailing-slash canonical redirect {src} -> {route} 301')

    # Sitemap URLs must use the same canonical host and slashless URL form.
    smp=root/'sitemap.xml'
    if smp.exists():
        try:
            tree=ET.parse(smp)
            ns={'sm':'http://www.sitemaps.org/schemas/sitemap/0.9'}
            sitemap_urls=[(n.text or '').strip() for n in tree.findall('.//sm:loc',ns)]
            for u in sitemap_urls:
                pr=urllib.parse.urlparse(u)
                path=pr.path or '/'
                if pr.scheme!='https' or pr.netloc!='tampabayshine.com':
                    issues.append(f'sitemap non-canonical host/scheme: {u}')
                    continue
                if path!='/' and path.endswith('/'):
                    issues.append(f'sitemap trailing slash URL: {u}')
                normalized=path.rstrip('/') or '/'
                if normalized not in routes:
                    issues.append(f'sitemap URL has no static route: {u}')
        except Exception as e:
            issues.append(f'invalid sitemap.xml: {e}')

    for x in ['robots.txt','sitemap.xml','_redirects','3631fda1114542beac8b749d5ed827ad.txt','llms.txt']:
        if not (root/x).exists(): issues.append(f'missing required/support file: {x}')

    print(f'HTML pages: {len(htmls)}')
    print(f'Errors: {len(issues)}')
    print(f'Warnings: {len(warnings)}')
    for x in issues[:50]: print('ERROR:',x)
    for x in warnings[:50]: print('WARN:',x)
    raise SystemExit(1 if issues else 0)

if __name__=='__main__':
    main()
