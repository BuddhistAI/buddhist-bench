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
                           "dispute", "example", "notes", "passage", "commentaries", "exam"}
STUDY_STATUSES = {"example", "planned", "baseline", "running", "ended"}
MODES = {"closed-book", "native-search", "logged-search", "forced-search"}
IV_REQUIRED = ["id", "study", "published_at", "venue_type", "venue", "language", "url", "content_summary",
               "target_items", "sources_cited", "disclosure", "author", "status"]
VENUES = {"own-site", "partner-site", "wikipedia", "wikidata", "wikisource", "forum", "social", "video", "other"}
IV_STATUSES = {"planned", "live", "edited", "reverted", "removed"}

errors = []
PERMISSION_STATUSES = {"granted", "published-open", "pending", "example"}
FAILURE_TAGS = set(json.loads((ROOT / "schema" / "grade.schema.json").read_text(encoding="utf-8"))
                   ["properties"]["failures"]["items"]["enum"])


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
    commentaries = set()
    if tr.get("kind", "tradition") not in ("tradition", "text", "exam"):
        err(f"tracks/index.json: {tid} kind must be tradition, text or exam")
    papers = {}
    if tr.get("kind") == "exam":
        ppath = tdir / "papers.json"
        if not ppath.exists():
            err(f"tracks/{tid}: exam tracks need papers.json")
        else:
            for pp in json.loads(ppath.read_text(encoding="utf-8"))["papers"]:
                pid = pp.get("id")
                if pid in papers:
                    err(f"tracks/{tid}/papers.json: duplicate id {pid}")
                papers[pid] = pp
                for k in ("institution", "tradition", "level", "language", "year", "permission"):
                    if k not in pp:
                        err(f"tracks/{tid}/papers.json: {pid} missing '{k}'")
                if pp.get("tradition") not in traditions:
                    err(f"tracks/{tid}/papers.json: {pid} has unknown tradition '{pp.get('tradition')}'")
                if pp.get("language") not in languages:
                    err(f"tracks/{tid}/papers.json: {pid} has unknown language '{pp.get('language')}'")
                perm = pp.get("permission", {})
                if perm.get("status") not in PERMISSION_STATUSES:
                    err(f"tracks/{tid}/papers.json: {pid} permission.status must be one of {sorted(PERMISSION_STATUSES)}")
                if perm.get("status") in ("granted", "published-open") and not perm.get("license"):
                    err(f"tracks/{tid}/papers.json: {pid} needs permission.license")
    if tr.get("kind") == "text":
        cpath = tdir / "commentaries.json"
        if not cpath.exists():
            err(f"tracks/{tid}: text tracks need commentaries.json")
        else:
            for c in json.loads(cpath.read_text(encoding="utf-8"))["commentaries"]:
                if c["id"] in commentaries:
                    err(f"tracks/{tid}/commentaries.json: duplicate id {c['id']}")
                commentaries.add(c["id"])
                if c.get("tradition") not in traditions:
                    err(f"tracks/{tid}/commentaries.json: {c['id']} has unknown tradition '{c.get('tradition')}'")
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
            used = list(it.get("commentaries", [])) + [c for p in it.get("positions", []) for c in p.get("commentaries", [])]
            for c in used:
                if c not in commentaries:
                    err(f"{where}: unknown commentary '{c}' (add it to tracks/{tid}/commentaries.json)")
            if tr.get("kind") == "exam":
                ex = it.get("exam") or {}
                pp = papers.get(ex.get("paper"))
                if pp is None:
                    err(f"{where}: exam items need exam.paper from tracks/{tid}/papers.json")
                elif split == "dev":
                    perm = pp.get("permission", {})
                    if perm.get("status") not in ("granted", "published-open") or perm.get("held_out"):
                        err(f"{where}: paper {pp['id']} is not cleared for the public dev split "
                            "(needs permission granted or published-open, and held_out false)")
                if pp is not None and pp.get("language") != lang and not it.get("translation_of"):
                    err(f"{where}: items in another language than the paper need translation_of")
            elif "exam" in it:
                err(f"{where}: 'exam' is only for exam tracks")
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

# ------------------------------------------------------------ intervention studies
track_by_id = {t["id"]: t for t in tracks}
n_studies = 0
for spath in sorted((ROOT / "studies").glob("*/study.json")):
    n_studies += 1
    rel = spath.relative_to(ROOT)
    st = json.loads(spath.read_text(encoding="utf-8"))
    for k in ["id", "status", "track", "language", "split", "control_items", "planned_targets", "panel", "baseline",
              "analysis", "owners"]:
        if k not in st:
            err(f"{rel}: missing '{k}'")
    if st.get("id") != spath.parent.name:
        err(f"{rel}: id must match the folder name")
    if st.get("status") not in STUDY_STATUSES:
        err(f"{rel}: bad status")
    if (st.get("status") == "example") != bool(st.get("example")):
        err(f"{rel}: example studies (and only those) have status example and example: true")
    if st.get("track") not in track_by_id:
        err(f"{rel}: unknown track '{st.get('track')}'")
    for m in st.get("panel", {}).get("modes", []):
        if m not in MODES:
            err(f"{rel}: unknown mode '{m}'")
    known_items = {i for i, w in seen_ids.items()
                   if w.startswith(f"tracks/{st.get('track')}/data/{st.get('language')}/{st.get('split')}.jsonl")}
    check_items = st.get("split") != "test"  # test items are private
    control = set(st.get("control_items", []))
    planned = {i for v in st.get("planned_targets", {}).values() for i in v}
    for i in control | planned:
        if check_items and i not in known_items:
            err(f"{rel}: item {i} is not in the study's track/language/split")
    if control & planned:
        err(f"{rel}: control items cannot be planned targets: {sorted(control & planned)}")
    ivp = spath.parent / "interventions.jsonl"
    iv_ids = set()
    for n, line in enumerate(ivp.read_text(encoding="utf-8").splitlines() if ivp.exists() else [], 1):
        if not line.strip():
            continue
        where = f"{ivp.relative_to(ROOT)}:{n}"
        iv = json.loads(line)
        for k in IV_REQUIRED:
            if k not in iv:
                err(f"{where}: missing '{k}'")
        if not re.match(r"^int-[0-9]{4,}$", str(iv.get("id", ""))):
            err(f"{where}: id must look like int-0001")
        if iv.get("id") in iv_ids:
            err(f"{where}: duplicate id")
        iv_ids.add(iv.get("id"))
        if iv.get("study") != st.get("id"):
            err(f"{where}: study must be '{st.get('id')}'")
        if bool(iv.get("example")) != bool(st.get("example")):
            err(f"{where}: example flag must match the study")
        if iv.get("venue_type") not in VENUES:
            err(f"{where}: bad venue_type")
        if iv.get("status") not in IV_STATUSES:
            err(f"{where}: bad status")
        if iv.get("language") not in languages:
            err(f"{where}: unknown language '{iv.get('language')}'")
        if "coi_disclosed" not in iv.get("disclosure", {}):
            err(f"{where}: disclosure needs coi_disclosed")
        for i in iv.get("target_items", []):
            if i in control:
                err(f"{where}: targets control item {i}")
            if check_items and i not in known_items:
                err(f"{where}: target {i} is not in the study's items")

# ------------------------------------------------------------ model-side fixes
FIX_KINDS = {"system-prompt", "reference", "skill"}
n_fixes = 0
for fpath in sorted((ROOT / "fixes").glob("*/fix.json")):
    n_fixes += 1
    d, rel = fpath.parent, fpath.relative_to(ROOT)
    try:
        fx = json.loads(fpath.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err(f"{rel}: invalid JSON ({e})")
        continue
    if fx.get("id") != d.name:
        err(f"{rel}: id must match the folder name")
    if fx.get("kind") not in FIX_KINDS:
        err(f"{rel}: kind must be one of {sorted(FIX_KINDS)}")
    if not SEMVER.match(str(fx.get("version", ""))):
        err(f"{rel}: version must be semver")
    if d.name.startswith("example-") != bool(fx.get("example")):
        err(f"{rel}: example fixes (and only those) are named example-* with example: true")
    if fx.get("kind") == "skill" and not fx.get("source"):
        err(f"{rel}: skill fixes cite their source (owner/repo@commit:path)")
    if not ((d / "system.md").exists() or (d / "context.md").exists()):
        err(f"{rel}: needs system.md and/or context.md")
    for t in fx.get("targets", []):
        if t not in FAILURE_TAGS:
            err(f"{rel}: unknown failure tag '{t}' in targets")

for e in errors:
    print("ERROR", e)
print(f"{len(seen_ids)} items, {n_studies} studies, {n_fixes} fixes checked, {len(errors)} errors")
sys.exit(1 if errors else 0)
