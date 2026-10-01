
from bs4 import BeautifulSoup
import re, json, html as htmlmod, unicodedata

SCRIPT_RE = re.compile(
    r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)([\s\S]*?)(</script>)',
    re.I
)

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def canonical_text(s):
    s = htmlmod.unescape(s or "")
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.lower()
    return re.sub(r"\s+", " ", s).strip()

def _pair_from_details(d):
    sm = d.find("summary")
    if not sm:
        return None
    q = clean(sm.get_text(" "))
    clone = BeautifulSoup(str(d), "html.parser")
    sm2 = clone.find("summary")
    if sm2:
        sm2.decompose()
    a = clean(clone.get_text(" "))
    return (q, a) if q and a else None

def visible_faq_nodes(text):
    soup = BeautifulSoup(text, "html.parser")

    # 1) Canonical standardized format wins.
    marked = soup.select('details[data-tbs-faq-item="1"]')
    if marked:
        return marked

    # 2) BookingKoala/static migration FAQ pattern:
    #    <details class="faq"> inside otherwise generic section/div containers.
    #    This is the pattern v8 missed on 25 pages.
    classed = soup.select("details.faq")
    if classed:
        return classed

    # 3) Legacy pages where FAQ details have no class but sit in an FAQ-labelled container.
    candidates = []
    for sec in soup.find_all(["section", "div"]):
        sid = (sec.get("id") or "").lower()
        aria = (sec.get("aria-label") or "").lower()
        classes = " ".join(sec.get("class") or []).lower()
        if sid == "faq" or sid.endswith("-faq") or "faq" in classes or "frequently asked" in aria:
            ds = sec.find_all("details")
            if ds:
                candidates.append((sec, ds))

    if not candidates:
        return []

    def score(item):
        sec, ds = item
        sid = (sec.get("id") or "").lower()
        classes = " ".join(sec.get("class") or []).lower()
        pri = 0 if sid == "faq" else 1 if sid.endswith("-faq") else 2 if "faq" in classes else 3
        return (pri, len(ds))

    return sorted(candidates, key=score)[0][1]

def visible_faqs(text):
    out = []
    for d in visible_faq_nodes(text):
        pair = _pair_from_details(d)
        if pair:
            out.append(pair)
    return out

def _collect_faqpages(node, collector):
    if isinstance(node, dict):
        t = node.get("@type")
        types = t if isinstance(t, list) else [t]
        if "FAQPage" in types:
            collector.append(node)
        for v in node.values():
            _collect_faqpages(v, collector)
    elif isinstance(node, list):
        for v in node:
            _collect_faqpages(v, collector)

def schema_faqpages(text):
    pages = []
    for m in SCRIPT_RE.finditer(text):
        try:
            data = json.loads(m.group(2))
        except Exception:
            continue
        _collect_faqpages(data, pages)
    return pages

def schema_questions(text):
    out = []
    for page in schema_faqpages(text):
        for q in page.get("mainEntity") or []:
            if not isinstance(q, dict) or q.get("@type") != "Question":
                continue
            name = clean(q.get("name") or "")
            ans = q.get("acceptedAnswer") or {}
            answer = clean(ans.get("text") or "") if isinstance(ans, dict) else ""
            out.append((name, answer))
    return out

def faqpage_count(text):
    return len(schema_faqpages(text))

def faq_questions_match(text):
    return [canonical_text(q) for q,a in visible_faqs(text)] == [canonical_text(q) for q,a in schema_questions(text)]

def faq_answers_match(text):
    v=[(canonical_text(q),canonical_text(a)) for q,a in visible_faqs(text)]
    s=[(canonical_text(q),canonical_text(a)) for q,a in schema_questions(text)]
    return v == s
