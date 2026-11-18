# Notes for agents working in this repo

## Start here (every BuddhistAI repo)

- Read the maintainer handbook first: https://buddhistai.github.io/knowledge-base/handbook/ (source: BuddhistAI/knowledge-base `handbook/`). Follow its rules and conventions.
- Check the Development board for cards assigned to you: https://github.com/orgs/BuddhistAI/projects/3. Status and next steps: `handbook/status.md`.
- Rules: plain English for non-native readers, no idioms. "Buddhist tasks", not only texts. "Top performance" and "Best value". Neutral credits: WeBuddhist is one contributor among others. Never invent data, scores, votes or links. Never edit generated files by hand.
- buddhist-benchmarks stays clean (short `result.json`, outputs, scores). Provenance records (`buddhistai/provenance@1`) live in the skill's own repo.
- When you change something the handbook describes, update the handbook in the same pull request.
- Before you change anything users see (pages, forms, install steps, app screens), write a design in `docs/designs/` and run an EGM review with our personas: skills `buddhistai-elephant` and `buddhistai-ux-review` (handbook `ux.md`). Small text or bug fixes skip this.
- EGM artifact directory: docs/designs
- This repo: BuddhistBench, a Q&A benchmark of Buddhist knowledge (one benchmark among others). Run `python3 scripts/check.py`.

## This repo

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
- Imported tracks (`source.kind: imported` in track.json) need SOURCE.md, a pinned revision and an MIT-compatible license; mark published sets `contamination: public`. Keep docs/related-benchmarks.md up to date when importing or finding a set.
