# Notes for agents working in this repo

- Layout: `tracks/<track>/data/<lang>/<split>.jsonl`. Track IDs in `tracks/index.json`; tradition IDs in `taxonomy/traditions.json`; language codes in `taxonomy/languages.json` (keep in sync with buddhist-skills `languages.json`).
- One item per line; schema in `schema/item.schema.json`, explained in `docs/schema.md`. IDs are permanent: never reuse or renumber.
- Never invent real items. Example items live only in `example.jsonl` with `example: true`. Real items need human authors and two human reviewers (same-tradition and cross-tradition).
- Never commit test data (`test.jsonl` is private).
- Any change to items or the scorer needs a version bump (`VERSION`, the track's `track.json`) and a CHANGELOG entry: patch = gold fixes, minor = new items/tracks/languages, major = format/scorer/judge changes.
- Run `python3 scripts/check.py` before pushing.
