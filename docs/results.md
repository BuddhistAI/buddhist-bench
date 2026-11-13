# Results format

Every model run is a folder with four files. The BuddhistAI leaderboard site reads `run.json` and `scores.json`; the same shape is used by buddhist-benchmarks runs (`run.json` + `scores.json`), so one site can read both.

- One-off leaderboard runs: `tracks/<track>/results/<lang>/runs/<run-id>/`
- Daily study runs: `studies/<study>/runs/<date>/<run-id>/` (not leaderboard rows)

`<run-id>` is `<date>-<model-slug>-<mode>-<variant>`, e.g. `2026-11-20-openai-gpt-5-native-search-sourced`. One folder holds one model, one mode and one prompt variant.

## run.json

| Field | Meaning |
| --- | --- |
| `benchmark` | `buddhist-bench` |
| `release`, `track`, `track_version`, `language`, `split` | What was run. Never compare rows across release or track versions. |
| `model` | OpenRouter model ID requested. |
| `served_models`, `providers` | What OpenRouter reports actually served the calls. |
| `mode` | `closed-book`, `native-search`, `logged-search` or `forced-search` ([design](./intervention-study.md#modes)). |
| `variant` | `plain` or `sourced` prompt. |
| `prompt_version`, `scorer_version`, `judge_panel` | Prompt and scorer used; judge panel models with versions, or null. |
| `repeats`, `temperature`, `engine`, `search_backend` | Run settings (`temperature: null` = provider default). |
| `harness` | `BuddhistAI/buddhist-bench@<commit>:scripts/openrouter_run.py (runner x.y.z)` |
| `study` | Study ID, or null. |
| `date`, `started_at`, `finished_at`, `calls`, `cost_usd`, `dry_run`, `by` | Bookkeeping. Dry runs are never published. |

## scores.json

The `scripts/score.py` report for repeat 0 (`overall`, `by_tradition`, `by_commentary`, `by_type`, `by_format`, `consensus_subset`, `default_probe`, `per_item`), plus:

- `repeats`: `{n, overall_scores, mean}` across repeats;
- `search`: `{responses, search_known, search_rate, citing_rate, cited_domains}`;
- `errors`: calls that failed.

The headline number is `overall.score`; leaderboards also show `overall.incorrect`, `overall.not_attempted` and `search.search_rate`. A row needs `ungraded: 0` (open answers graded by humans or a judge panel).

## calls.jsonl and responses.jsonl

`calls.jsonl` has one record per item and repeat (`schema/call.schema.json`): answer, extracted response, score, served model, usage and cost, and the full search record (queries, results, fetched and cited URLs, intervention matches). `responses.jsonl` is repeat 0 in the scorer's input format (`schema/response.schema.json`), so anyone can re-score a run.

## Study outputs

`studies/<study>/timeseries.jsonl` has one row per date, model, mode, variant and group (`control` or an intervention ID): `n`, `graded`, `accuracy`, `search_rate`, `seen_rate` (logged-search only), `cited_rate`, `served_models`. `report.json` has one `effects` row per intervention, model, mode and variant (fields in `scripts/analyze_study.py`). A site can plot accuracy and citation rate over time per model with the publication date marked.
