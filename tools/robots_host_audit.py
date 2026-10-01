
from __future__ import annotations

import argparse
import http.client
import ssl
from urllib.parse import urlparse, urljoin

DEFAULT_URLS = [
    "http://tampabayshine.com/robots.txt",
    "https://tampabayshine.com/robots.txt",
    "http://www.tampabayshine.com/robots.txt",
    "https://www.tampabayshine.com/robots.txt",
]

USER_AGENTS = {
    "browser": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/154 Safari/537.36",
    "googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
}


def request_once(url: str, user_agent: str, timeout=15):
    p = urlparse(url)
    cls = http.client.HTTPSConnection if p.scheme == "https" else http.client.HTTPConnection
    kwargs = {"timeout": timeout}
    if p.scheme == "https":
        kwargs["context"] = ssl.create_default_context()
    conn = cls(p.netloc, **kwargs)
    path = p.path or "/"
    if p.query:
        path += "?" + p.query
    conn.request(
        "GET",
        path,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/plain,*/*;q=0.8",
            "Connection": "close",
        },
    )
    resp = conn.getresponse()
    body = resp.read(4000)
    headers = dict(resp.getheaders())
    conn.close()
    return resp.status, resp.reason, headers, body


def trace(url: str, ua: str, max_hops=10):
    hops = []
    current = url
    for _ in range(max_hops + 1):
        try:
            status, reason, headers, body = request_once(current, ua)
        except Exception as exc:
            hops.append((current, "ERROR", str(exc), "", b""))
            break
        location = headers.get("Location") or headers.get("location") or ""
        hops.append((current, status, reason, location, body))
        if status not in {301, 302, 303, 307, 308} or not location:
            break
        current = urljoin(current, location)
    return hops


def main():
    ap = argparse.ArgumentParser(description="Check robots.txt across http/https and apex/www using browser and Googlebot user agents.")
    ap.add_argument("--url", action="append", default=[], help="Optional URL; may be repeated.")
    args = ap.parse_args()
    urls = args.url or DEFAULT_URLS

    print("TAMPA BAY SHINE ROBOTS/HOST AUDIT")
    print("=================================")

    failures = 0
    for label, ua in USER_AGENTS.items():
        print("")
        print(f"USER AGENT: {label}")
        for url in urls:
            hops = trace(url, ua)
            final = hops[-1]
            chain = " -> ".join(str(h[1]) for h in hops)
            print(f"{url}")
            print(f"  chain: {chain}")
            for h in hops:
                loc = f" -> {h[3]}" if h[3] else ""
                print(f"    {h[1]} {h[0]}{loc}")
            if isinstance(final[1], int) and final[1] == 200:
                text = final[4].decode("utf-8", errors="replace").strip().replace("\r", "")
                preview = " | ".join(text.splitlines()[:5])
                print(f"  final robots preview: {preview}")
            else:
                failures += 1

    print("")
    if failures:
        print(f"RESULT: ATTENTION ({failures} request paths did not end in HTTP 200)")
        raise SystemExit(1)
    print("RESULT: PASS - all tested variants ultimately returned HTTP 200.")

if __name__ == "__main__":
    main()
