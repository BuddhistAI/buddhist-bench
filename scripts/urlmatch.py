"""URL helpers shared by the runner, the intervention checker and the analysis.

Two URLs count as the same page when their normalised forms are equal:
lower-case host without www. or m. (Wikipedia mobile), no fragment, no
tracking parameters, no trailing slash, percent-decoding, and Wikipedia
index.php?title=X / oldid links reduced to /wiki/X.
"""
import re
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "fbclid", "gclid"}


def norm_url(url):
    try:
        u = urlsplit(url.strip().rstrip(".,;:"))
    except ValueError:
        return url.strip().lower()
    host = (u.hostname or "").lower()
    for prefix in ("www.", "m."):
        if host.startswith(prefix):
            host = host[len(prefix):]
    host = host.replace(".m.wikipedia.org", ".wikipedia.org").replace(".m.wikidata.org", ".wikidata.org")
    path = unquote(u.path).replace(" ", "_")
    query = [(k, v) for k, v in parse_qsl(u.query) if k.lower() not in TRACKING]
    if host.endswith(("wikipedia.org", "wikidata.org", "wikisource.org")):
        q = dict(query)
        if "title" in q:
            path = "/wiki/" + q["title"].replace(" ", "_")
        query = []  # oldid, diff, action ... all point at the same page
    path = path.rstrip("/") or "/"
    qs = urlencode(sorted(query))
    return f"{host}{path}" + (f"?{qs}" if qs else "")


def urls_in_text(text):
    return [m.group(0).rstrip(".,;:") for m in URL_RE.finditer(text or "")]


def intervention_index(interventions):
    """normalised URL -> intervention id."""
    idx = {}
    for iv in interventions:
        for u in [iv.get("url", ""), *iv.get("match_urls", [])]:
            if u:
                idx[norm_url(u)] = iv["id"]
    return idx


def match(urls, index):
    return sorted({index[n] for n in (norm_url(u) for u in urls) if n in index})
