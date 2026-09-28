from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1] / 'cloudflare-site'
TX = {'/booknow','/login','/gift-card','/referrals','/floor-calculator'}
LIVE = 'https://tampabayshine.com'

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        p=urlsplit(self.path)
        route=p.path.rstrip('/') or '/'
        if route in TX:
            location=LIVE+route + (('?' + p.query) if p.query else '')
            self.send_response(302)
            self.send_header('Location',location)
            self.end_headers()
            return
        return super().do_GET()

def main():
    if not (ROOT/'index.html').exists():
        raise SystemExit(f'Not found: {ROOT}')
    def factory(*args,**kwargs):
        return Handler(*args,directory=str(ROOT),**kwargs)
    server=ThreadingHTTPServer(('127.0.0.1',8080),factory)
    print('Local site preview: http://localhost:8080')
    print('Press Ctrl+C to stop.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
