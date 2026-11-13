# BuddhistBench

An open benchmark for how well AI models know the Buddhist traditions: their histories, texts, doctrines and practices, and which tradition holds which view.

**Goal:** find out where commercial AI gets Buddhism wrong, and which fixes (instructions, reference material, skills, published sources) make it more reliable. Coverage grows bottom-up: small, expert-made sets on specific traditions, texts and exams, built with the communities that own them, adding up over time.

BuddhistBench is made of tracks:

- **Core track**: questions shared by every tradition. Pan-Buddhist facts, plus questions that test whether a model attributes views to the right tradition and avoids presenting one school as "Buddhism".
- **Tradition tracks**: each tradition writes, reviews and owns questions about itself, in its own languages (Theravāda, Tibetan, Chan/Zen, Pure Land, Tendai, Shingon, Nichiren and more).
- **Text tracks**: questions on one work, such as *The Thirty-Seven Practices of Bodhisattvas*, answered from its commentaries and keyed to commentary and tradition.
- **Exam tracks**: real exam papers from monasteries, shedras, Buddhist universities and national exam systems, used with permission, so models are tested the way students are ([docs/exams.md](./docs/exams.md)).

**Language is an axis.** The same model can do well in English and fail in Tibetan or Thai, so items are asked in many languages, as native questions and as reviewed translations linked to their originals. Results can be filtered by language, and the gap between languages on the same questions is a headline number ([docs/languages.md](./docs/languages.md)). Reading and translating source languages (Classical Tibetan, Pali, Sanskrit, Classical Chinese) is tested separately in [buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks).

**Existing benchmarks are brought in, not rebuilt.** Openly licensed sets such as the Thai Nak Tham exams are imported as tracks, credited and pinned to their source version, and count in aggregate scores. Because published sets may already be in models' training data, they are marked `contamination: public`, results always show each source separately, and `score.py --exclude-public` leaves them out. The full list of related benchmarks, imported or linked: [docs/related-benchmarks.md](./docs/related-benchmarks.md).

Graders tag *what kind* of mistake each wrong answer makes (misattribution, invented sources, flattening one school into "Buddhism", ...), and **fixes** are measured against a baseline on the same items ([docs/fixes.md](./docs/fixes.md)).

Models are run through OpenRouter in several modes (closed-book, the provider's own web search, and a search tool whose every query we log), and **intervention studies** measure whether accurate, sourced material published about a text reaches AI answers, how fast, and through which models. Design: [docs/intervention-study.md](./docs/intervention-study.md).

It is maintained in the open by Buddhist organizations working together. Founded by WeBuddhist.

> **Status: 0.4.0, scaffold.** The structure, schema, scorer and rules are in place. The only items so far are clearly marked format examples (`example.jsonl`); there is no real data yet. See [CONTRIBUTING.md](./CONTRIBUTING.md) to help write it.

## The key rule

- If a question **names a tradition**, the right answer is that tradition's answer, without hedging.
- If it **does not name one** and traditions differ, the right answer lays out the differing positions and attributes each one.

Results are always reported per tradition, never only as one number.

## Layout

```
VERSION                          release version (semver)
CHANGELOG.md                     every release, item changes included
taxonomy/traditions.json         tradition tree (dotted IDs, e.g. tibetan.gelug)
taxonomy/topics.json             topic tags
taxonomy/languages.json          language codes for data folders
schema/                          item, response and grade JSON schemas
tracks/index.json                every track (active or planned)
tracks/<track>/
  TRACK.md                       scope, sources, owners
  commentaries.json              text tracks: commentaries answers are keyed to
  papers.json                    exam tracks: papers, institutions and permissions
  track.json                     track version and owners
  data/<lang>/example.jsonl      format examples (never on a leaderboard)
  data/<lang>/dev.jsonl          public items
  results/<lang>/LEADERBOARD.md  ranked runs
  results/<lang>/runs/<run-id>/  one model x mode x variant run (docs/results.md)
studies/<study>/                 intervention studies: design, intervention log, daily runs, report
prompts/                         standard answer prompt and judge prompt
scripts/check.py                 validate everything
scripts/score.py                 score responses
scripts/openrouter_run.py        run items on OpenRouter models in each search mode
scripts/check_interventions.py   daily liveness check of published interventions
scripts/analyze_study.py         time series and effects for a study
scripts/export_hf.py             build, check and publish the Hugging Face release
docs/                            design, schema, scoring, review process
fixes/<id>/                      model-side fixes (system prompt, reference material, skill)
```

## Question types

| Type | Format | Scored by |
| --- | --- | --- |
| factual | mcq or short | exact match |
| citation | short | exact canonical reference |
| attributed (names a tradition) | mcq or short | that tradition's key |
| comparative | open | expert rubric |
| contested (traditions differ, none named) | open | rubric that rewards attribution, penalises flattening |
| false-premise | open | declining or flagging the premise is correct |
| default-probe | mcq | not accuracy: shows which tradition a model defaults to |

Details in [docs/schema.md](./docs/schema.md) and [docs/scoring.md](./docs/scoring.md).

## Scoring a model

```bash
python3 scripts/score.py --items tracks/core/data/en/dev.jsonl \
  --responses my-run/responses.jsonl --grades my-run/grades.jsonl > scores.json
```

Or let the runner ask the models, extract answers and score them:

```bash
OPENROUTER_API_KEY=... python3 scripts/openrouter_run.py --items tracks/core/data/en/dev.jsonl \
  --models openai/gpt-5 anthropic/claude-sonnet-4.5 --modes closed-book native-search \
  --out tracks/core/results/en/runs
python3 scripts/openrouter_run.py --study studies/example-37-practices --dry-run --out /tmp/run   # no key needed
```

Use the prompt in [prompts/answer.md](./prompts/answer.md). Short and open answers that do not match automatically need grades from human experts or a judge panel ([prompts/judge.md](./prompts/judge.md)). Then add a row to the track's leaderboard.

## Versions

Semantic versioning for the whole benchmark (`VERSION`, git tags `vX.Y.Z`) and for each track (`track.json`):

- **patch**: fix a gold answer, typo, alias or citation
- **minor**: add items, traditions, languages or tracks
- **major**: change the item format, the scorer or the judge panel

Each release is published automatically to Hugging Face at [BuddhistAI/buddhist-bench](https://huggingface.co/datasets/BuddhistAI/buddhist-bench), public splits only, tagged `vX.Y.Z` (`load_dataset("BuddhistAI/buddhist-bench", "core-en", revision="vX.Y.Z")`). GitHub stays the source of truth; see [docs/huggingface.md](./docs/huggingface.md). Leaderboard rows cite the release and track version; never compare rows across versions.

## Related

- [BuddhistAI/buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks): task benchmarks for text-processing skills (TOC extraction, alignment, translation)
- [BuddhistAI/buddhist-skills](https://github.com/BuddhistAI/buddhist-skills): agent skills for Buddhist texts

## License

MIT, for code and data. Only contribute questions you wrote or that come from sources compatible with MIT, and say where each came from (`sources_license`).

Imported tracks keep their own license, recorded in `tracks/<id>/track.json` and `SOURCE.md` (for example, `nak-tham` is Apache-2.0). Only MIT-compatible sets are imported.
