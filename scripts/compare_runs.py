#!/usr/bin/env python3
"""Compare a baseline run with a fixed run on the same items.

python3 scripts/compare_runs.py BASELINE_RUN_DIR FIXED_RUN_DIR > comparison.json

Each run dir holds scores.json (from scripts/openrouter_run.py or scripts/score.py).
Reports the overall and per-tradition change, items the fix repaired or broke,
changes in failure-tag counts, and a paired bootstrap 95% interval on the overall
change. Only items present in both runs are compared.
"""
import json
import random
import sys
from pathlib import Path


def load(d):
    d = Path(d)
    rep = json.loads((d / "scores.json").read_text(encoding="utf-8"))
    run = json.loads((d / "run.json").read_text(encoding="utf-8")) if (d / "run.json").exists() else {}
    return rep, run


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    (base, brun), (fixd, frun) = load(sys.argv[1]), load(sys.argv[2])
    a = {r["id"]: r for r in base["per_item"]}
    b = {r["id"]: r for r in fixd["per_item"]}
    ids = sorted(set(a) & set(b))
    if not ids:
        sys.exit("no items in common")
    diffs = [b[i]["score"] - a[i]["score"] for i in ids]
    rng = random.Random(0)
    boots = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(2000))
    for key in ("release", "track", "track_version", "model", "mode", "variant", "prompt_version", "scorer_version"):
        if brun.get(key) != frun.get(key):
            print(f"warning: runs differ in {key}: {brun.get(key)} vs {frun.get(key)}", file=sys.stderr)

    def tradition_delta():
        out = {}
        for t, v in fixd.get("by_tradition", {}).items():
            if t in base.get("by_tradition", {}):
                out[t] = round(v["score"] - base["by_tradition"][t]["score"], 4)
        return out

    def failure_delta():
        fa, fb = base.get("failures", {}).get("all", {}), fixd.get("failures", {}).get("all", {})
        return {k: fb.get(k, 0) - fa.get(k, 0) for k in sorted(set(fa) | set(fb))}

    out = {
        "baseline": {"model": brun.get("model"), "fix": brun.get("fix")},
        "fixed": {"model": frun.get("model"), "fix": frun.get("fix")},
        "items": len(ids),
        "baseline_score": round(sum(a[i]["score"] for i in ids) / len(ids), 4),
        "fixed_score": round(sum(b[i]["score"] for i in ids) / len(ids), 4),
        "change": round(sum(diffs) / len(diffs), 4),
        "change_ci95": [round(boots[49], 4), round(boots[1949], 4)],
        "repaired": [i for i in ids if a[i]["outcome"] != "correct" and b[i]["outcome"] == "correct"],
        "broken": [i for i in ids if a[i]["outcome"] == "correct" and b[i]["outcome"] != "correct"],
        "change_by_tradition": tradition_delta(),
        "failure_count_change": failure_delta(),
        "targets": (frun.get("fix") or {}).get("targets"),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
