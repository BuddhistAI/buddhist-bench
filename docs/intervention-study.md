# Text tracks, the OpenRouter runner and intervention studies

Design for three additions to BuddhistBench (release 0.2.0):

1. **Text tracks**: Q&A on one text, such as *The Thirty-Seven Practices of Bodhisattvas*, with answers keyed to specific commentaries and traditions.
2. **An OpenRouter runner** that asks many models the same questions in several search modes and records what each model searched, read and cited.
3. **Intervention studies**: publish accurate, sourced material about a text, re-run the benchmark daily, and measure whether, when and through which models the material reaches answers.

Status: scaffold. The runner, schemas, checks and analysis exist and pass a dry run with a fake model; no live OpenRouter call has been made yet. The only items, studies and interventions are clearly marked examples. Still to build: an automatic judge panel for open answers.

## 1. Text tracks

A text track is a track with `"kind": "text"` in `tracks/index.json`. Its `track.json` describes the work (title, author, editions) and its `commentaries.json` lists the commentaries that answers can be keyed to:

```json
{"id": "dilgo-khyentse-heart-of-compassion", "commentator": "Dilgo Khyentse Rinpoche",
 "title": "The Heart of Compassion", "tradition": "tibetan.nyingma", "language": "en",
 "edition": "Shambhala, 2007", "verified": false}
```

Items use the existing schema plus three optional fields:

| Field | Where | Meaning |
| --- | --- | --- |
| `passage` | item | Verse or section the question is about, e.g. `["v12"]`. |
| `commentaries` | item | Commentaries the question names ("According to Dilgo Khyentse..."). |
| `commentaries` | position | Commentaries that give this answer. A position can now be keyed to traditions, commentaries or both. |

Every position cites where its answer comes from (`sources[].ref`, with page or folio in `sources[].note`). The scorer reports `by_commentary` beside `by_tradition`.

The same rules apply as everywhere in BuddhistBench: questions that name a commentary are scored against that commentary; questions that name none, where commentaries differ, are `contested` and rewarded for attributing each reading. Real items need a human author and two reviewers, one of them from the commentary's tradition. Example items carry `"example": true` and their gold answers are placeholders unless they are uncontroversial facts (who wrote the root text).

## 2. The OpenRouter runner

`scripts/openrouter_run.py` sends every item to every chosen model in each chosen mode, using the standard prompts in `prompts/answer.md`, and writes one record per call (`schema/call.schema.json`) plus leaderboard-ready results (`docs/results.md`).

### Modes

| Mode | How | Who decides to search | What we can observe |
| --- | --- | --- | --- |
| `closed-book` | No tools. | Nobody. | Answer only. Measures memory. |
| `native-search` | OpenRouter's `openrouter:web_search` server tool with `engine: "native"`: the provider's own search (OpenAI, Anthropic, Google, xAI, Perplexity); other models fall back to Exa. | The model. | Number of searches (`usage.server_tool_use_details.web_search_requests`) and cited URLs (`url_citation` annotations). **Not** the queries or the uncited results. |
| `logged-search` | Our own `web_search` and `fetch_url` function tools, backed by a search API we choose (Brave by default). | The model. | Everything: each query, every result shown, every page fetched, every cited URL. |
| `forced-search` (optional) | OpenRouter's `web` plugin. Always searches once with the prompt as query. | Nobody (always on). Deprecated by OpenRouter. | Cited URLs. |

Why three: `closed-book` is the baseline; `native-search` is closest to what users of commercial assistants get; `logged-search` is the only mode where we can see which queries a model writes and whether our page appeared in its results but was ignored. All modes use the same items, prompts, answer extraction and scorer, so scores are comparable across modes; differences between modes are the effect of search.

**Prompt variants.** Each mode runs with `plain` (the standard prompt) and optionally `sourced` (the same question plus "give reliable sources"), because asking for sources is what we expect to trigger searching. Variant is a column in every result.

### What OpenRouter does not show

- With native search we see how many searches ran and which URLs were cited, not the queries or the results the model saw and did not cite. "Our page was found but not used" is only measurable in `logged-search`.
- A request names a model, but OpenRouter may route to different providers, and providers update models silently. Every record stores the served `model` and `provider` from the response; the analysis flags changes.
- Search results also change daily for reasons unrelated to us. Controls (below) absorb this.
- Native search in consumer apps (ChatGPT, Claude.ai, Gemini) can differ from the API. Results describe API behaviour.

### All models

`--models all` reads OpenRouter's model list and keeps text-output models; tool modes keep only models that list `tools` support. Skipped models and the reason are written to the run. A full sweep is costly, so studies use a fixed **panel** of models daily and a full sweep only occasionally. The runner prints an estimate and stops at `--max-cost`.

## 3. Intervention studies

A study lives in `studies/<study-id>/`:

```
study.json                 design, fixed before the first intervention
interventions.jsonl        the intervention log, one line per publication
intervention_status.jsonl  daily liveness checks (still online? reverted? indexed?)
runs/<date>/<run-id>/      daily runs (calls.jsonl, responses.jsonl, scores.json, run.json)
timeseries.jsonl           daily aggregates (generated)
REPORT.md, report.json     effects (generated)
```

### The intervention log

Each publication is one line (`schema/intervention.schema.json`): what was published (`content_summary`, `check_text`, sources cited), where (`venue_type`: own-site, wikipedia, wikidata, forum, social, video, other; `venue`, e.g. `bo.wikipedia.org`), in which `language`, the `url` (plus alternative URLs that count as the same page), Wikipedia `revision_id`, an archive snapshot, the `published_at` timestamp, which items it targets, the conflict-of-interest disclosure, and its current `status` (live, reverted, removed). `scripts/check_interventions.py` checks every live intervention daily and records whether it is still online and still contains `check_text`; for Wikipedia it records the current revision, so a revert is dated.

### Design and controls

- **Pre-registration.** `study.json` fixes the items, the panel of models, the modes, the number of repeats, the planned targets and the analysis rule before the first intervention.
- **Baseline.** At least 7 days of daily runs before anything is published, so day-to-day noise (sampling, provider updates, search-index churn) is measured.
- **Control items.** A random subset of the study's items is never targeted. Their scores move only for reasons unrelated to us; the effect is measured against them (difference in differences).
- **Random targets, staggered dates.** Targets are drawn at random from matched items, and interventions go out on different days, so one model update cannot look like an effect.
- **Repeats.** Each item is asked 3 times per day per model and mode (provider-default sampling, recorded), so reliability is a rate, not an anecdote.

### What is measured

Per day, model, mode, variant and group (each intervention's targets, or the controls):

- accuracy against the commentary-keyed gold answers;
- **search rate**: share of calls that searched (known in `native-search` and `logged-search`);
- **seen rate**: share of calls whose search results included an intervention URL (`logged-search` only);
- **citation rate**: share of calls citing an intervention URL;
- served model and provider.

Per intervention, model and mode (`scripts/analyze_study.py`):

- **effect size**: (target after − target baseline) − (control after − control baseline), with a 95% bootstrap interval resampling items;
- **time to first citation**: days from `published_at` to the first call citing the URL;
- **time to impact**: days from `published_at` to the first day that starts a run of 3 days where the daily target-minus-control gap exceeds its baseline mean by 2 baseline standard deviations;
- **reliability**: share of post-impact calls on target items that are correct, and share of days after impact on which the effect holds;
- which models search at all, and which answer from memory even in search modes.

**Grading.** Daily runs are scored automatically, so studies should rely mostly on `mcq` and `short` items. Open items need a judge panel (`prompts/judge.md`); until `scripts/judge.py` exists their calls are `ungraded` and left out of accuracy (the report counts them).

Time to index (when a search engine first returns the page) is recorded separately by the liveness check where a search key is available, so "not indexed yet" and "indexed but not used" can be told apart.

## 4. Results and the leaderboard

Each (model, mode, variant) run is a folder with `run.json`, `responses.jsonl`, `scores.json` and `calls.jsonl`, the same shape as buddhist-benchmarks runs, so the BuddhistAI leaderboard site can read both. One-off leaderboard runs go in `tracks/<track>/results/<lang>/runs/`; daily study runs stay in the study folder and are not leaderboard rows. Details: [results.md](./results.md).

## 5. Daily runs

`.github/workflows/daily.yml` runs at 03:00 UTC (and on demand): liveness checks, then the panel for every study in `baseline` or `running` status, then the analysis, then a commit to `main`. It needs the repository secret `OPENROUTER_API_KEY`, and `BRAVE_API_KEY` for `logged-search`; without them it does nothing. Rough cost: 30 items × 3 repeats × 3 modes × 10 models is 2,700 calls a day, about $10 to $50 depending on the panel and search pricing; `budget_usd_per_day` in `study.json` caps it.

## 6. Ethics and platform policy

The point of the study is to learn whether accurate, sourced information about a text reaches AI answers, not to steer them. So:

- **Only publish what is accurate and sourced**: material from the commentaries, attributed and cited, that a reviewer from the tradition has approved. Never publish claims the gold answers do not support, and never write text designed to be picked up by models (keyword stuffing, hidden text, prompt-like instructions, invisible markers).
- **Wikipedia**: follow each language edition's policies. Content needs reliable published sources and no original research. Editors connected to the study must disclose their conflict of interest (on the user page, and on the article talk page for substantive edits) and, on English Wikipedia, propose substantive changes on the talk page rather than edit the article directly. Research that involves Wikipedia or its editors is expected to be announced and coordinated with the community (see Meta-Wiki's research pages) before it starts. If a community objects, stop and log it.
- **Reverts are data, not obstacles.** If an edit is reverted, record it; do not re-insert it to keep the study going.
- **Own sites** (WeBuddhist and partners) should say who wrote the material and where it comes from.
- **Copyright**: quote commentaries within fair use and cite them; summaries in our own words otherwise.
- **Publish the findings**, including null results, with the intervention log, so others can check them.
