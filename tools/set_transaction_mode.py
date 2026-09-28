
from pathlib import Path
import argparse,json
ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['fallback','custom']); ap.add_argument('--repo',default='.'); a=ap.parse_args(); repo=Path(a.repo).resolve(); p=repo/'site-management'/'release_targets.json'; d=json.loads(p.read_text(encoding='utf-8')); d['transaction_mode']='bookingkoala_fallback' if a.mode=='fallback' else 'custom_booking'; p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8'); active=d['fallback_base'] if a.mode=='fallback' else d['custom_booking_base']; print('Transaction mode:',d['transaction_mode']); print('Active target:',active); print('Commit this config change on cloudflare-staging, validate, then promote normally.')
