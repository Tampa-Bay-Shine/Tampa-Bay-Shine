
from pathlib import Path
import argparse,json,re,subprocess,sys
DEV='cloudflare-staging'; PROD='cloudflare-production'; TX=['booknow','login','gift-card','referrals','floor-calculator']; TX_ALT='|'.join(re.escape(x) for x in TX)
def run(a,cwd,check=False):
    p=subprocess.run(a,cwd=str(cwd),text=True,capture_output=True)
    if check and p.returncode: raise RuntimeError(' '.join(a)+'\n'+p.stdout+'\n'+p.stderr)
    return p
def branch(repo): return run(['git','branch','--show-current'],repo).stdout.strip()
def load_active(repo):
    d=json.loads((repo/'site-management'/'release_targets.json').read_text(encoding='utf-8')); mode=d['transaction_mode']
    if mode=='bookingkoala_fallback': return d['fallback_base'].rstrip('/')
    if mode=='custom_booking': return d['custom_booking_base'].rstrip('/')
    raise RuntimeError('Invalid transaction_mode')
def transform(repo,active):
    site=repo/'cloudflare-site'; hp=site/'_headers'; lines=hp.read_text(encoding='utf-8').splitlines(); hp.write_text('\n'.join(x for x in lines if not re.match(r'\s*X-Robots-Tag:\s*noindex\s*$',x,re.I)).rstrip()+'\n',encoding='utf-8')
    rp=site/'_redirects'; out=[]; seen=set()
    for line in rp.read_text(encoding='utf-8').splitlines():
        s=line.strip(); hit=False
        for r in TX:
            if s.startswith(f'/{r} '):
                parts=s.split(); code=parts[2] if len(parts)>2 else '302'; out.append(f'/{r} {active}/{r} {code}'); seen.add(r); hit=True; break
        if not hit: out.append(line)
    for r in TX:
        if r not in seen: out.append(f'/{r} {active}/{r} 302')
    rp.write_text('\n'.join(out).rstrip()+'\n',encoding='utf-8')
    anchor_re=re.compile(r'(<a\\b[^>]*?\\bhref=)(["\\\'])(/(?:(?:'+TX_ALT+r'))(?:/)?(?:[?#][^"\\\']*)?)\\2',re.I)
    for html in site.rglob('*.html'):
        src=html.read_text(encoding='utf-8')
        def repl(m):
            return m.group(1)+m.group(2)+active+m.group(3)+m.group(2)
        dst,n=anchor_re.subn(repl,src)
        if n:
            html.write_text(dst,encoding='utf-8')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',default='.'); ap.add_argument('--push',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    if branch(repo)!=DEV: raise SystemExit(f'Start on {DEV}; current={branch(repo)}')
    if run(['git','status','--porcelain'],repo).stdout.strip(): raise SystemExit('Working tree must be clean.')
    gate=repo/'tools'/'migration_gate.py'; p=subprocess.run([sys.executable,str(gate),'--repo',str(repo),'--phase','staging'],cwd=str(repo))
    if p.returncode!=0: raise SystemExit('Staging gate is not GREEN. Promotion stopped.')
    active=load_active(repo); run(['git','fetch','origin'],repo,True); sha=run(['git','rev-parse',f'origin/{DEV}'],repo,True).stdout.strip(); local=run(['git','show-ref','--verify','--quiet',f'refs/heads/{PROD}'],repo).returncode==0; remote=run(['git','show-ref','--verify','--quiet',f'refs/remotes/origin/{PROD}'],repo).returncode==0
    if local: run(['git','switch',PROD],repo,True)
    elif remote: run(['git','switch','-c',PROD,'--track',f'origin/{PROD}'],repo,True)
    else: run(['git','switch','-c',PROD,f'origin/{DEV}'],repo,True)
    run(['git','read-tree','--reset','-u',f'origin/{DEV}'],repo,True); transform(repo,active); run(['git','add','-A'],repo,True)
    if run(['git','diff','--cached','--quiet'],repo).returncode!=0: run(['git','commit','-m',f'Promote staging {sha[:12]} to Cloudflare production'],repo,True)
    p=subprocess.run([sys.executable,str(gate),'--repo',str(repo),'--phase','production'],cwd=str(repo))
    if p.returncode!=0: raise SystemExit('Production gate is not GREEN. Nothing pushed.')
    if a.push:
        args=['git','push','origin',PROD] if remote else ['git','push','-u','origin',PROD]; run(args,repo,True); print('Pushed',PROD,'using transaction target',active)
    else: print('Production branch prepared locally. NOT pushed.'); print('Transaction target:',active)
    run(['git','switch',DEV],repo,True); print('Returned to',DEV)
if __name__=='__main__': main()
