
from pathlib import Path
import argparse, json, re, subprocess

DISALLOWED = ("St. Petersburg", "Clearwater", "Carrollwood")
ABOUT_NEW = (
    "We serve homeowners, renters, property managers, Airbnb hosts, and businesses throughout "
    "Tampa Bay—including Tampa, Brandon, Riverview, Wesley Chapel, Apollo Beach, Ruskin, "
    "Sun City Center, Lutz, Temple Terrace, Bradenton, and surrounding communities."
)

def branch(repo):
    p = subprocess.run(["git","branch","--show-current"], cwd=str(repo), text=True, capture_output=True)
    return p.stdout.strip()

def transform_json(obj):
    if isinstance(obj, list):
        vals = [transform_json(x) for x in obj]
        out, seen = [], set()
        for x in vals:
            if isinstance(x, dict) and isinstance(x.get("name"), str):
                key = x["name"].strip().lower()
                if key in seen:
                    continue
                seen.add(key)
            out.append(x)
        return out
    if isinstance(obj, dict):
        out = {k: transform_json(v) for k, v in obj.items()}
        if isinstance(out.get("itemListElement"), list) and "numberOfItems" in out:
            out["numberOfItems"] = len(out["itemListElement"])
        return out
    if isinstance(obj, str):
        s = obj.replace("St. Petersburg, FL", "Temple Terrace, FL")
        s = s.replace("St. Petersburg", "Temple Terrace")
        s = re.sub(r",\s*Carrollwood\b", "", s, flags=re.I)
        s = re.sub(r",\s*Clearwater\b", "", s, flags=re.I)
        s = re.sub(r"\bCarrollwood,\s*", "", s, flags=re.I)
        s = re.sub(r"\bClearwater,\s*", "", s, flags=re.I)
        return s
    return obj

def patch_jsonld(text):
    pat = re.compile(
        r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
        re.I | re.S
    )
    def repl(m):
        try:
            data = json.loads(m.group(2))
        except Exception:
            return m.group(0)
        data = transform_json(data)
        return m.group(1) + json.dumps(data, ensure_ascii=False, separators=(",",":")) + m.group(3)
    return pat.sub(repl, text)

def route_for(site, p):
    return "/" if p == site/"index.html" else "/" + p.parent.relative_to(site).as_posix()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    site = repo/"cloudflare-site"
    if a.apply and branch(repo) != "cloudflare-staging":
        raise SystemExit("Run --apply only on cloudflare-staging.")

    changed = []
    for p in sorted(site.rglob("*.html")):
        src = p.read_text(encoding="utf-8", errors="ignore")
        out = patch_jsonld(src)
        out = out.replace("St. Petersburg", "Temple Terrace")
        route = route_for(site, p)
        if route == "/about":
            out = re.sub(
                r"We serve homeowners,\s*renters,\s*property managers,\s*Airbnb hosts,\s*and businesses throughout Tampa Bay—including\s*Apollo Beach,\s*Riverview,\s*Brandon,\s*Tampa,\s*Wesley Chapel,\s*Carrollwood,\s*Clearwater,\s*Temple Terrace,\s*and surrounding communities\.",
                ABOUT_NEW,
                out,
                flags=re.I
            )
        if out != src:
            changed.append(route)
            if a.apply:
                p.write_text(out, encoding="utf-8")

    hits = []
    for p in sorted(site.rglob("*.html")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        route = route_for(site, p)
        for term in DISALLOWED:
            if term.lower() in txt.lower():
                hits.append((route, term))

    print("Changed routes:", len(changed))
    for r in changed:
        print(" ", r)

    if hits:
        print("Remaining references:")
        for r, term in hits:
            print(f" {r}: {term}")
        return 1

    print("SERVICE AREA AUDIT: PASS")
    print("Legacy _redirects entries are intentionally preserved.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
