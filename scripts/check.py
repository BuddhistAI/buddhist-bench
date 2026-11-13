#!/usr/bin/env python3
"""Validate the BuddhistBench repo: taxonomy, tracks, items, versions.

python3 scripts/check.py
Exit code 1 on errors. No third-party dependencies.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
TYPES = {"factual", "attributed", "comparative", "contested", "default-probe", "citation", "false-premise"}
FORMATS = {"mcq", "short", "open"}
STATUSES = {"active", "disputed", "retired"}
SPLITS = {"example", "dev"}  # the test split is private and never committed
REQUIRED = ["id", "track", "language", "type", "format", "traditions", "topics", "question",
            "positions", "status", "since", "changed", "authors", "reviewers", "sources_license"]
ALLOWED = set(REQUIRED) | {"translation_of", "difficulty", "choices", "rubric", "accept_decline",
                           "dispute", "example", "notes"}

errors = []


def err(msg):
    errors.append(msg)


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


version = (ROOT / "VERSION").read_text().strip()
if not SEMVER.match(version):
    err(f"VERSION: '{version}' is not semver")
if f"## [{version}]" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
    err(f"CHANGELOG.md: no '## [{version}]' entry for the current VERSION")

traditions = {t["id"] for t in load("taxonomy/traditions.json")["traditions"]}
for t in traditions:
    parent = t.rsplit(".", 1)[0]
    if "." in t and parent not in traditions:
        err(f"taxonomy/traditions.json: '{t}' has no parent '{parent}'")
topics = {t["id"] for t in load("taxonomy/topics.json")["topics"]}
languages = {l["code"] for l in load("taxonomy/languages.json")["languages"]}

tracks = load("tracks/index.json")["tracks"]
track_ids = [t["id"] for t in tracks]
if len(track_ids) != len(set(track_ids)):
    err("tracks/index.json: duplicate track IDs")
codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")

seen_ids = {}
for tr in tracks:
    tid = tr["id"]
    for c in tr.get("covers", []):
        if c not in traditions:
            err(f"tracks/index.json: {tid} covers unknown tradition '{c}'")
    tdir = ROOT / "tracks" / tid
    if tr["status"] == "planned":
        continue
    if tr["status"] != "active":
        err(f"tracks/index.json: {tid} status must be active or planned")
        continue
    for f in ("TRACK.md", "track.json"):
        if not (tdir / f).exists():
            err(f"tracks/{tid}: missing {f}")
    if f"/tracks/{tid}/" not in codeowners:
        err(f".github/CODEOWNERS: no owner line for /tracks/{tid}/")
    if (tdir / "track.json").exists():
        meta = json.loads((tdir / "track.json").read_text(encoding="utf-8"))
        if not SEMVER.match(meta.get("version", "")):
            err(f"tracks/{tid}/track.json: version must be semver")
    files = sorted((tdir / "data").glob("*/*.jsonl"))
    if not files:
        err(f"tracks/{tid}: active track has no data files")
    for path in files:
        lang, split = path.parent.name, path.stem
        rel = path.relative_to(ROOT)
        if lang not in languages:
            err(f"{rel}: unknown language code '{lang}'")
        if split not in SPLITS:
            err(f"{rel}: split must be one of {sorted(SPLITS)} (test data is private)")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            where = f"{rel}:{n}"
            try:
                it = json.loads(line)
            except json.JSONDecodeError as e:
                err(f"{where}: invalid JSON ({e})")
                continue
            iid = it.get("id", "?")
            where = f"{where} {iid}"
            for k in REQUIRED:
                if k not in it:
                    err(f"{where}: missing '{k}'")
            for k in it:
                if k not in ALLOWED:
                    err(f"{where}: unknown field '{k}'")
            if iid in seen_ids:
                err(f"{where}: duplicate id (also {seen_ids[iid]})")
            seen_ids[iid] = where
            if it.get("track") != tid or it.get("language") != lang:
                err(f"{where}: track/language fields must match the folder ({tid}/{lang})")
            prefix = f"{'example-' if split == 'example' else ''}{tid}-{lang}-"
            if not str(iid).startswith(prefix):
                err(f"{where}: id must start with '{prefix}'")
            if (split == "example") != bool(it.get("example")):
                err(f"{where}: example items (and only those) go in example.jsonl with example: true")
            if it.get("type") not in TYPES:
                err(f"{where}: bad type")
            if it.get("format") not in FORMATS:
                err(f"{where}: bad format")
            if it.get("status") not in STATUSES:
                err(f"{where}: bad status")
            if it.get("status") == "disputed" and not it.get("dispute"):
                err(f"{where}: disputed items need a 'dispute' link")
            for k in ("since", "changed"):
                if not SEMVER.match(str(it.get(k, ""))):
                    err(f"{where}: '{k}' must be semver")
            tags = list(it.get("traditions", []))
            for p in it.get("positions", []):
                tags += p.get("traditions", [])
            tags += [r["tradition"] for r in it.get("rubric", []) if "tradition" in r]
            tags += [r["tradition"] for r in it.get("reviewers", [])]
            for t in tags:
                if t not in traditions:
                    err(f"{where}: unknown tradition '{t}'")
            for t in it.get("topics", []):
                if t not in topics:
                    err(f"{where}: unknown topic '{t}'")
            if not it.get("positions"):
                err(f"{where}: needs at least one position")
            fmt = it.get("format")
            if fmt == "mcq":
                choice_ids = {c["id"] for c in it.get("choices", [])}
                if len(choice_ids) < 2:
                    err(f"{where}: mcq needs at least two choices")
                for p in it.get("positions", []):
                    if p.get("answer") not in choice_ids:
                        err(f"{where}: position answer '{p.get('answer')}' is not a choice id")
            if fmt == "open" and not it.get("rubric"):
                err(f"{where}: open items need a rubric")
            if fmt == "open" and not any(r["weight"] > 0 for r in it.get("rubric", [])):
                err(f"{where}: rubric needs at least one positive criterion")
            if it.get("type") == "default-probe" and (fmt != "mcq" or len(it.get("positions", [])) < 2):
                err(f"{where}: default-probe items are mcq with one position per tradition")
            if it.get("type") == "false-premise" and not it.get("accept_decline"):
                err(f"{where}: false-premise items need accept_decline: true")
            if split == "dev" and it.get("status") == "active":
                roles = {r["role"] for r in it.get("reviewers", [])}
                if roles != {"same-tradition", "cross-tradition"}:
                    err(f"{where}: active dev items need a same-tradition and a cross-tradition reviewer")

for e in errors:
    print("ERROR", e)
print(f"{len(seen_ids)} items checked, {len(errors)} errors")
sys.exit(1 if errors else 0)
