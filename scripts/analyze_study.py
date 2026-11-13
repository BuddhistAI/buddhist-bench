#!/usr/bin/env python3
"""Turn a study's daily runs into a time series and per-intervention effects.

python3 scripts/analyze_study.py studies/<id>

Reads study.json, interventions.jsonl (planned ones ignored) and runs/*/*/calls.jsonl.
Writes timeseries.jsonl, report.json and REPORT.md into the study folder.

Groups: each intervention's target items, and the study's control items (never targeted).
Per intervention x model x mode x variant:
  effect        difference in differences on item accuracy:
                (target after - target before) - (control after - control before),
                95% interval from a bootstrap that resamples items
  time_to_impact_days   first day after publication that starts a run of `impact_window_days`
                days whose target-minus-control gap exceeds its baseline mean by
                `impact_threshold_sd` baseline SDs (SD floored at 0.05)
  first_seen_hours / first_cited_hours   from published_at to the first call whose search
                results included / whose answer cited the intervention URL
  reliability   share of target calls correct after impact, and share of post-impact days
                on which the gap stays above the threshold
Calls with errors or ungraded outcomes are left out of accuracy (counted separately).
Standard library only. See docs/intervention-study.md.
"""
import json
import random
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def load_jsonl(p):
    return [json.loads(ln) for ln in Path(p).read_text(encoding="utf-8").splitlines() if ln.strip()]


def ts(s):
    d = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def r4(x):
    return None if x is None else round(x, 4)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sdir = Path(sys.argv[1])
    study = json.loads((sdir / "study.json").read_text(encoding="utf-8"))
    ivp = sdir / "interventions.jsonl"
    ivs = [iv for iv in (load_jsonl(ivp) if ivp.exists() else []) if iv.get("status") != "planned"]
    cfg = {"impact_window_days": 3, "impact_threshold_sd": 2.0, "bootstrap": 1000, "seed": 1, **study.get("analysis", {})}
    control = set(study["control_items"])
    calls = [c for p in sorted(sdir.glob("runs/*/*/calls.jsonl")) for c in load_jsonl(p)]
    errors = sum(1 for c in calls if c.get("error"))
    ungraded = sum(1 for c in calls if c.get("outcome") == "ungraded")

    item_group = defaultdict(set)  # item -> groups
    for i in control:
        item_group[i].add("control")
    for iv in ivs:
        for i in iv["target_items"]:
            item_group[i].add(iv["id"])
            if i in control:
                print(f"WARNING {iv['id']} targets control item {i}", file=sys.stderr)

    # ------------------------------------------------------------ time series
    cells = defaultdict(list)  # (date, model, mode, variant, group) -> calls
    for c in calls:
        if c.get("error"):
            continue
        c["_date"] = c["timestamp"][:10]
        for g in item_group.get(c["item_id"], ()):
            cells[(c["_date"], c["model"], c["mode"], c["variant"], g)].append(c)

    series = []
    for (date, model, mode, variant, g), cs in sorted(cells.items()):
        graded = [x for x in cs if x.get("outcome") != "ungraded"]
        known = [x for x in cs if (x.get("search") or {}).get("triggered") is not None]
        ivids = [g] if g != "control" else [iv["id"] for iv in ivs]
        hit = lambda x, k: any(i in ((x.get("interventions") or {}).get(k) or []) for i in ivids)  # noqa: E731
        series.append({
            "date": date, "model": model, "mode": mode, "variant": variant, "group": g, "n": len(cs),
            "graded": len(graded), "accuracy": r4(mean([x["score"] for x in graded])),
            "search_rate": r4(mean([1.0 if x["search"]["triggered"] else 0.0 for x in known])),
            "seen_rate": r4(mean([1.0 if hit(x, "seen") else 0.0 for x in cs])) if mode == "logged-search" else None,
            "cited_rate": r4(mean([1.0 if hit(x, "cited") else 0.0 for x in cs])),
            "served_models": sorted({x.get("served_model") for x in cs if x.get("served_model")}),
        })
    with open(sdir / "timeseries.jsonl", "w", encoding="utf-8") as f:
        for row in series:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------ effects
    rng = random.Random(cfg["seed"])
    combos = sorted({(c["model"], c["mode"], c["variant"]) for c in calls if not c.get("error")})
    effects = []
    for iv in ivs:
        pub = ts(iv["published_at"])
        targets = set(iv["target_items"])
        for model, mode, variant in combos:
            cs = [c for c in calls if not c.get("error") and c["model"] == model and c["mode"] == mode
                  and c["variant"] == variant]
            graded = [c for c in cs if c.get("outcome") != "ungraded"]

            def per_item(items, after):
                out = {}
                for i in items:
                    xs = [c["score"] for c in graded if c["item_id"] == i and (ts(c["timestamp"]) >= pub) == after]
                    if xs:
                        out[i] = mean(xs)
                return out

            tb, ta = per_item(targets, False), per_item(targets, True)
            cb, ca = per_item(control, False), per_item(control, True)
            td = [ta[i] - tb[i] for i in ta if i in tb]
            cd = [ca[i] - cb[i] for i in ca if i in cb]
            effect = mean(td) - mean(cd) if td and cd else None
            ci = None
            if td and cd and cfg["bootstrap"]:
                boots = sorted(mean(rng.choices(td, k=len(td))) - mean(rng.choices(cd, k=len(cd)))
                               for _ in range(cfg["bootstrap"]))
                ci = [r4(boots[int(0.025 * len(boots))]), r4(boots[int(0.975 * len(boots)) - 1])]

            # daily gaps
            day = defaultdict(lambda: {"t": [], "c": []})
            for c in graded:
                key = "t" if c["item_id"] in targets else "c" if c["item_id"] in control else None
                if key:
                    day[c["timestamp"][:10]][key].append(c["score"])
            gaps = {d: mean(v["t"]) - mean(v["c"]) for d, v in sorted(day.items()) if v["t"] and v["c"]}
            pub_day = pub.strftime("%Y-%m-%d")
            pre = [g for d, g in gaps.items() if d < pub_day]
            post = [(d, g) for d, g in gaps.items() if d >= pub_day]
            thr = None
            impact_day = None
            days_holding = None
            if len(pre) >= 2:
                thr = mean(pre) + cfg["impact_threshold_sd"] * max(statistics.stdev(pre), 0.05)
                w = cfg["impact_window_days"]
                for k in range(len(post) - w + 1):
                    if all(g > thr for _, g in post[k:k + w]):
                        impact_day = post[k][0]
                        break
                if impact_day:
                    after = [g for d, g in post if d >= impact_day]
                    days_holding = r4(sum(1 for g in after if g > thr) / len(after))

            def first(kind):
                hits = [ts(c["timestamp"]) for c in cs if iv["id"] in ((c.get("interventions") or {}).get(kind) or [])
                        and ts(c["timestamp"]) >= pub]
                return round((min(hits) - pub).total_seconds() / 3600, 1) if hits else None

            after_impact = [c["score"] for c in graded if c["item_id"] in targets and impact_day
                            and c["timestamp"][:10] >= impact_day]
            known_post = [c for c in cs if c["item_id"] in targets and ts(c["timestamp"]) >= pub
                          and (c.get("search") or {}).get("triggered") is not None]
            served = sorted({c.get("served_model") for c in cs if c.get("served_model")})
            warn = []
            if len({d for d in gaps if d < pub_day}) < study["baseline"]["min_days"]:
                warn.append(f"fewer than {study['baseline']['min_days']} baseline days")
            if len(targets) < 20 or len(control) < 20:
                warn.append("fewer than 20 items in a group: effect is indicative only")
            if len(served) > 1:
                warn.append(f"served model changed: {', '.join(served)}")
            if iv.get("status") in ("reverted", "removed"):
                warn.append(f"intervention {iv['status']} at {iv.get('status_changed_at', '?')}")
            effects.append({
                "intervention": iv["id"], "venue": iv["venue"], "language": iv["language"], "model": model,
                "mode": mode, "variant": variant, "effect": r4(effect), "effect_ci95": ci,
                "target_before": r4(mean(list(tb.values()))), "target_after": r4(mean(list(ta.values()))),
                "control_before": r4(mean(list(cb.values()))), "control_after": r4(mean(list(ca.values()))),
                "baseline_days": len(pre), "post_days": len(post), "threshold": r4(thr),
                "time_to_impact_days": (ts(impact_day + "T00:00:00Z") - ts(pub_day + "T00:00:00Z")).days
                if impact_day else None,
                "first_seen_hours": first("seen") if mode == "logged-search" else None,
                "first_cited_hours": first("cited"),
                "reliability_after_impact": r4(mean(after_impact)), "days_effect_holds": days_holding,
                "search_rate_after": r4(mean([1.0 if c["search"]["triggered"] else 0.0 for c in known_post])),
                "warnings": warn,
            })

    # who searches
    searchers = []
    for model, mode, variant in combos:
        known = [c for c in calls if c["model"] == model and c["mode"] == mode and c["variant"] == variant
                 and not c.get("error") and (c.get("search") or {}).get("triggered") is not None]
        if mode != "closed-book":
            searchers.append({"model": model, "mode": mode, "variant": variant, "calls": len(known),
                              "search_rate": r4(mean([1.0 if c["search"]["triggered"] else 0.0 for c in known]))})

    report = {"study": study["id"], "example": bool(study.get("example")),
              "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "calls": len(calls), "errors": errors, "ungraded": ungraded,
              "days": sorted({c["timestamp"][:10] for c in calls}), "analysis": cfg,
              "interventions": [{k: iv.get(k) for k in ("id", "venue_type", "venue", "language", "url",
                                                        "published_at", "status")} for iv in ivs],
              "effects": effects, "search_behaviour": searchers}
    (sdir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def fmt(x, signed=False):
        if x is None:
            return ""
        if isinstance(x, float):
            return f"{x:+.3f}" if signed else f"{x:.3g}"
        return str(x)

    lines = [f"# {study.get('title', study['id'])}", "",
             "Generated by `scripts/analyze_study.py`; do not edit. Design: docs/intervention-study.md.", ""]
    if study.get("example"):
        lines += ["> **Example study.** Interventions are not real publications and runs are dry runs.", ""]
    lines += [f"{len(calls)} calls over {len(report['days'])} days; {errors} errors, {ungraded} ungraded "
              "(ungraded calls need a judge and are left out of accuracy).", "",
              "## Effects", "",
              "| Intervention | Model | Mode | Variant | Effect (DiD) | 95% CI | Days to impact | "
              "First cited (h) | First seen (h) | Search rate after | Warnings |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for e in effects:
        ci = f"{e['effect_ci95'][0]:+.3f} to {e['effect_ci95'][1]:+.3f}" if e["effect_ci95"] else ""
        lines.append(f"| {e['intervention']} ({e['venue']}, {e['language']}) | {e['model']} | {e['mode']} | "
                     f"{e['variant']} | {fmt(e['effect'], True)} | {ci} | {fmt(e['time_to_impact_days'])} | "
                     f"{fmt(e['first_cited_hours'])} | {fmt(e['first_seen_hours'])} | "
                     f"{fmt(e['search_rate_after'])} | {'; '.join(e['warnings'])} |")
    lines += ["", "## Who searches", "", "| Model | Mode | Variant | Calls | Search rate |", "| --- | --- | --- | --- | --- |"]
    for s in searchers:
        lines.append(f"| {s['model']} | {s['mode']} | {s['variant']} | {s['calls']} | {fmt(s['search_rate'])} |")
    (sdir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(calls)} calls, {len(effects)} effect rows -> {sdir}/REPORT.md", file=sys.stderr)


if __name__ == "__main__":
    main()
