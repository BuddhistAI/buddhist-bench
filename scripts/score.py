#!/usr/bin/env python3
"""Score model responses against BuddhistBench items.

python3 scripts/score.py --items tracks/core/data/en/example.jsonl \
    --responses run/responses.jsonl [--grades run/grades.jsonl] > scores.json

Items:     one JSON item per line (schema/item.schema.json).
Responses: {"id", "answer", "declined"} per line (schema/response.schema.json).
Grades:    optional, for short/open items that need a human or judge panel
           (schema/grade.schema.json).

Every item ends up as correct, incorrect, not_attempted or ungraded, plus a
0-1 score. Results are reported overall, per tradition (rolled up the tree),
per type, and for the consensus subset. default-probe items are not scored
for accuracy; they are reported as a distribution over traditions.
"""
import argparse
import json
import sys
import unicodedata
from collections import defaultdict

SCORER_VERSION = "0.1.0"


def load_jsonl(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as e:
                    sys.exit(f"{path}:{n}: {e}")
    return out


def norm(text):
    """Case-, accent- and punctuation-insensitive form for short answers."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = "".join(c if c.isalnum() or c.isspace() else " " for c in text.casefold())
    return " ".join(text.split())


def ancestors(tid):
    parts = tid.split(".")
    return [".".join(parts[: i + 1]) for i in range(len(parts))]


def rubric_score(rubric, met):
    pos = sum(c["weight"] for c in rubric if c["weight"] > 0)
    got = sum(c["weight"] for c in rubric if met.get(c["id"]))
    return max(0.0, min(1.0, got / pos)) if pos else 0.0


def grade_item(item, resp, grade):
    """Return (outcome, score, matched_traditions)."""
    declined = bool(resp and resp.get("declined"))
    answer = (resp or {}).get("answer", "")
    if resp is None or (not declined and not str(answer).strip()):
        return "not_attempted", 0.0, []
    if declined:
        return ("correct", 1.0, []) if item.get("accept_decline") else ("not_attempted", 0.0, [])

    fmt = item["format"]
    if fmt == "mcq":
        for p in item["positions"]:
            if str(answer).strip().upper() == p["answer"].upper():
                return "correct", 1.0, p["traditions"]
        return "incorrect", 0.0, []

    if fmt == "short":
        a = norm(answer)
        for p in item["positions"]:
            if a in {norm(x) for x in [p["answer"], *p.get("aliases", [])]}:
                return "correct", 1.0, p["traditions"]
        if grade and grade.get("grade"):
            g = grade["grade"]
            t = [grade["matched_tradition"]] if grade.get("matched_tradition") else []
            return g, 1.0 if g == "correct" else 0.0, t
        return "ungraded", 0.0, []

    # open
    if grade and "criteria" in grade:
        s = rubric_score(item.get("rubric", []), grade["criteria"])
        return ("correct" if s >= 0.5 else "incorrect"), s, []
    return "ungraded", 0.0, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--responses", required=True)
    ap.add_argument("--grades")
    ap.add_argument("--include-examples", action="store_true",
                    help="Score example items (format checks only; never for leaderboards).")
    args = ap.parse_args()

    items = [i for p in args.items for i in load_jsonl(p)]
    items = [i for i in items if i.get("status") == "active"]
    if not args.include_examples:
        items = [i for i in items if not i.get("example")]
    resps = {r["id"]: r for r in load_jsonl(args.responses)}
    grades = {g["id"]: g for g in load_jsonl(args.grades)} if args.grades else {}

    per_item = []
    buckets = defaultdict(lambda: defaultdict(list))  # group -> key -> [score]
    outcomes = defaultdict(lambda: defaultdict(int))
    probe = defaultdict(lambda: defaultdict(int))  # item id -> tradition -> count

    for it in items:
        outcome, score, matched = grade_item(it, resps.get(it["id"]), grades.get(it["id"]))
        per_item.append({"id": it["id"], "outcome": outcome, "score": round(score, 4), "matched": matched})
        if it["type"] == "default-probe":
            for t in matched or ["none"]:
                probe["all"][t] += 1
            continue
        keys = [("overall", "all"), ("type", it["type"]), ("format", it["format"])]
        if all(p.get("consensus") for p in it["positions"]):
            keys.append(("subset", "consensus"))
        for t in {a for t in it["traditions"] for a in ancestors(t)}:
            keys.append(("tradition", t))
        for group, key in keys:
            buckets[group][key].append(score)
            outcomes[f"{group}:{key}"][outcome] += 1

    def summary(group):
        return {
            k: {"n": len(v), "score": round(sum(v) / len(v), 4), **outcomes[f"{group}:{k}"]}
            for k, v in sorted(buckets[group].items())
        }

    report = {
        "scorer_version": SCORER_VERSION,
        "items": len(items),
        "ungraded": sum(1 for p in per_item if p["outcome"] == "ungraded"),
        "overall": summary("overall").get("all", {}),
        "by_tradition": summary("tradition"),
        "by_type": summary("type"),
        "by_format": summary("format"),
        "consensus_subset": summary("subset").get("consensus", {}),
        "default_probe": {k: dict(v) for k, v in probe.items()},
        "per_item": per_item,
    }
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
