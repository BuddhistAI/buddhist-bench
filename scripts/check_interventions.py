#!/usr/bin/env python3
"""Daily check of every published intervention in a study.

python3 scripts/check_interventions.py studies/<id> [--dry-run]

Appends one line per live/edited intervention to studies/<id>/intervention_status.jsonl:
  checked_at, id, http_status, online, contains_check_text,
  current_revision (Wikipedia/Wikidata/Wikisource), indexed (if BRAVE_API_KEY is set and
  the intervention has index_query), error.
A drop in contains_check_text or a new revision dates an edit or revert; update the
intervention's status in interventions.jsonl when that happens (do not re-insert reverted
content). Standard library only.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import urlmatch  # noqa: E402
from openrouter_run import UA, Brave, http_json  # noqa: E402

WIKI = ("wikipedia.org", "wikidata.org", "wikisource.org")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(3_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""


def wiki_state(iv):
    """Current revision and wikitext of a wiki page, through the MediaWiki API."""
    host = urllib.parse.urlsplit(iv["url"]).hostname.replace(".m.", ".")
    title = iv.get("page_title") or urlmatch.norm_url(iv["url"]).split("/wiki/", 1)[-1]
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "titles": title, "rvprop": "ids|timestamp|content",
                                "rvslots": "main", "format": "json", "formatversion": "2"})
    data = http_json(f"https://{host}/w/api.php?{q}", timeout=30)
    page = data["query"]["pages"][0]
    if page.get("missing"):
        return None, None, ""
    rev = page["revisions"][0]
    return rev["revid"], rev["timestamp"], rev["slots"]["main"].get("content", "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    if len(args) != 1:
        sys.exit(__doc__)
    sdir = Path(args[0])
    ivp = sdir / "interventions.jsonl"
    if not ivp.exists():
        return
    ivs = [json.loads(ln) for ln in ivp.read_text(encoding="utf-8").splitlines() if ln.strip()]
    brave = Brave(os.environ["BRAVE_API_KEY"]) if os.environ.get("BRAVE_API_KEY") and not dry else None
    rows = []
    for iv in ivs:
        if iv.get("status") not in ("live", "edited") or iv.get("example"):
            continue  # examples point at placeholder URLs
        row = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "id": iv["id"], "error": None}
        try:
            host = urllib.parse.urlsplit(iv["url"]).hostname or ""
            if host.endswith(WIKI):
                rev, rev_ts, text = wiki_state(iv)
                row.update(online=rev is not None, current_revision=rev, current_revision_at=rev_ts,
                           since_logged_revision=(str(rev) != str(iv.get("revision_id"))) if rev else None)
            else:
                status, text = fetch(iv["url"])
                row.update(http_status=status, online=200 <= status < 300)
            if iv.get("check_text"):
                row["contains_check_text"] = iv["check_text"] in text
            if brave and iv.get("index_query"):
                idx = urlmatch.intervention_index([iv])
                row["indexed"] = bool(urlmatch.match([r["url"] for r in brave.search(iv["index_query"], 20)], idx))
        except Exception as e:
            row["error"] = str(e)[:300]
        rows.append(row)
    if rows:
        with open(sdir / "intervention_status.jsonl", "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(rows)} interventions checked", file=sys.stderr)


if __name__ == "__main__":
    main()
