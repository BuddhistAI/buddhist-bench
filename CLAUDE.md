# Notes for agents working in this repo

- Layout: `tracks/<track>/data/<lang>/<split>.jsonl`. Track IDs in `tracks/index.json`; tradition IDs in `taxonomy/traditions.json`; language codes in `taxonomy/languages.json` (keep in sync with buddhist-skills `languages.json`).
- One item per line; schema in `schema/item.schema.json`, explained in `docs/schema.md`. IDs are permanent: never reuse or renumber.
- Never invent real items. Example items live only in `example.jsonl` with `example: true`. Real items need human authors and two human reviewers (same-tradition and cross-tradition).
- Never commit test data (`test.jsonl` is private).
- Any change to items or the scorer needs a version bump (`VERSION`, the track's `track.json`) and a CHANGELOG entry: patch = gold fixes, minor = new items/tracks/languages, major = format/scorer/judge changes.
- Run `python3 scripts/check.py` before pushing.
- Text tracks (`kind: text`) key answers to commentaries in the track's `commentaries.json`. Intervention studies live in `studies/` (design: `docs/intervention-study.md`); never edit past runs, and log interventions the day they go live.
- Never publish an intervention that is not accurate, sourced and reviewed; follow Wikipedia policies (COI disclosure, reliable sources). Never commit API keys: the runner reads `OPENROUTER_API_KEY` and `BRAVE_API_KEY` from the environment.
- Exam tracks (`kind: exam`) need `papers.json` with a permission record per paper; only `granted` or `published-open` papers that are not `held_out` may have public `dev` items. Never commit permission letters or private papers.
- Model-side fixes live in `fixes/<id>/` (docs/fixes.md); bump a fix's version when its text changes. Compare runs with `scripts/compare_runs.py`.
- Question language is an axis: translated items set `origin` and `translation_of` (pointing at the original) and need a native-speaker `language` reviewer. Source-language reading and translation tasks belong in buddhist-benchmarks, not here.
