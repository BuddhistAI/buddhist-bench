#!/usr/bin/env python3
"""Compare one model's results on the same questions asked in different languages.

python3 scripts/crosslingual.py RUN_DIR [RUN_DIR ...] [--reference en] > crosslingual.json

Each RUN_DIR holds scores.json (and run.json) for one language of the same
track, model, mode and prompt variant. Items are matched by parallel group:
an original item and its translations (translation_of) share a group. Only
groups answered in every language are compared, so the gap reflects the
language of the question, not different questions. Items with origin
"adapted" are not strict parallels; read their gaps with care.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--reference", default="en", help="language the gaps are measured against")
    args = ap.parse_args()

    by_lang, meta = {}, {}
    for d in map(Path, args.runs):
        rep = json.loads((d / "scores.json").read_text(encoding="utf-8"))
        run = json.loads((d / "run.json").read_text(encoding="utf-8")) if (d / "run.json").exists() else {}
        rows = [r for r in rep["per_item"] if r.get("parallel")]
        if not rows:
            sys.exit(f"{d}: scores.json has no parallel ids (needs scorer 0.3.0 or later)")
        lang = rows[0]["language"]
        if lang in by_lang:
            sys.exit(f"two runs for language {lang}")
        by_lang[lang] = {r["parallel"]: r for r in rows}
        meta[lang] = {k: run.get(k) for k in ("model", "mode", "variant", "track", "release", "fix")}
    models = {m["model"] for m in meta.values()}
    if len(models) > 1:
        print(f"warning: runs are for different models: {sorted(models, key=str)}", file=sys.stderr)

    shared = sorted(set.intersection(*(set(v) for v in by_lang.values())))
    if not shared:
        sys.exit("no question is answered in every language")
    scores = {lang: round(sum(rows[g]["score"] for g in shared) / len(shared), 4) for lang, rows in by_lang.items()}
    ref = args.reference if args.reference in scores else max(scores, key=scores.get)
    out = {
        "runs": meta,
        "parallel_questions": len(shared),
        "score_by_language": dict(sorted(scores.items(), key=lambda kv: -kv[1])),
        "reference": ref,
        "gap_vs_reference": {l: round(s - scores[ref], 4) for l, s in scores.items() if l != ref},
        "max_gap": round(max(scores.values()) - min(scores.values()), 4),
        "inconsistent": [
            {"group": g, **{l: by_lang[l][g]["outcome"] for l in by_lang}}
            for g in shared if len({by_lang[l][g]["outcome"] == "correct" for l in by_lang}) > 1
        ],
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
