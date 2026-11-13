# Changelog

Every release of BuddhistBench. Versions follow semver:

- **patch**: fixed gold answers, typos, aliases, citations
- **minor**: new items, traditions, languages or tracks
- **major**: changed item format, scorer or judge panel

For each release, list track versions and changed item IDs, so anyone can see why a score moved.

## [0.3.0] - 2026-11-13

Bottom-up coverage, exam tracks, failure tags and model-side fixes. Goal stated in the README: find where commercial AI gets Buddhism wrong and which fixes make it more reliable. No real data yet.

- Exam tracks (`"kind": "exam"`): `papers.json` per track with institution, tradition, level, language, year and a permission record; items carry `exam: {paper, question, marks, marking}`. The checker keeps papers without permission, or held out, out of the public `dev` split. New format-example track `exam-example`; `nak-tham` (Thai Nak Tham exams, Apache-2.0) listed as planned. Guide: [docs/exams.md](./docs/exams.md).
- Failure tags in grades (`failures`), counted by the scorer overall and per tradition. Definitions and suggested fixes: [docs/fixes.md](./docs/fixes.md).
- Model-side fixes: `fixes/<id>/` (`system-prompt`, `reference`, `skill`), `--fix` in `scripts/openrouter_run.py` (recorded in `run.json` as `fix`), and `scripts/compare_runs.py` for baseline-vs-fix comparisons with a paired bootstrap interval. Format examples `example-attribution-prompt`, `example-37-practices-reference`.
- Scorer 0.3.0: adds `failures` and `by_paper`. No item score changes, so earlier results stay comparable.
- Language as an axis ([docs/languages.md](./docs/languages.md)): item `origin` (`native`, `translated`, `adapted`) with `translation_of` forming parallel groups; translated items need a native-speaker `language` reviewer; the checker keeps translations parallel to their source. Scorer reports `by_language`, and each item row carries `language` and `parallel`. New `scripts/crosslingual.py` reports a model's score per language on shared questions and the cross-lingual gap.
- New item format examples: `example-exam-example-en-0001`..`0002`, `example-core-zh-0001` (Chinese translation of `example-core-en-0001`).

Track versions: core 0.2.0, theravada 0.1.0, tibetan 0.1.0, 37-practices 0.1.0, exam-example 0.1.0.

## [0.2.0] - 2026-11-13

Text tracks, the OpenRouter runner and intervention studies ([design](./docs/intervention-study.md)). No real data yet.

- Text tracks (`"kind": "text"`): new track `37-practices` (*The Thirty-Seven Practices of Bodhisattvas*) with `commentaries.json` and format examples `example-37-practices-en-0001`..`0004`. Commentary answers in the examples are marked placeholders.
- Item schema: optional `passage`, `commentaries` (item and position). Existing items are unchanged.
- Scorer 0.2.0: adds `by_commentary` and search stats to reports. No item score changes, so 0.1.0 results stay comparable.
- Answer prompt 0.2.0: adds the `sourced` variant and search-mode notes; `plain` prompts unchanged.
- `scripts/openrouter_run.py`: runs items on OpenRouter models in `closed-book`, `native-search`, `logged-search` and `forced-search` modes, logs search behaviour (`schema/call.schema.json`), writes run folders ([results.md](./docs/results.md)).
- Intervention studies: `studies/`, `schema/study.schema.json`, `schema/intervention.schema.json`, `scripts/check_interventions.py`, `scripts/analyze_study.py`, example study `example-37-practices`, daily workflow `.github/workflows/daily.yml`.
- `scripts/check.py` validates text tracks, commentaries and studies.

Track versions: core 0.1.0, theravada 0.1.0, tibetan 0.1.0, 37-practices 0.1.0 (new).

## [0.1.0] - 2026-11-13

First scaffold. No real data yet.

- Repository structure: core track plus tradition tracks (`theravada`, `tibetan` active; nine more planned).
- Tradition tree, topics and languages in `taxonomy/`.
- Item, response and grade schemas.
- Scorer (`scripts/score.py`, scorer 0.1.0) with per-tradition, per-type and consensus reporting and a default-school probe.
- Validator, Hugging Face export and release workflow.
- Format examples only: `example-core-en-0001`..`0007`, `example-theravada-en-0001`..`0002`, `example-tibetan-en-0001`..`0002`.

Track versions: core 0.1.0, theravada 0.1.0, tibetan 0.1.0.
