# BuddhistBench

An open benchmark for how well AI models know the Buddhist traditions: their histories, texts, doctrines and practices, and which tradition holds which view.

BuddhistBench has two parts:

- **Core track**: questions shared by every tradition. Pan-Buddhist facts, plus questions that test whether a model attributes views to the right tradition and avoids presenting one school as "Buddhism".
- **Tradition tracks**: each tradition writes, reviews and owns questions about itself, in its own languages (Theravāda, Tibetan, Chan/Zen, Pure Land, Tendai, Shingon, Nichiren and more).

It is maintained in the open by Buddhist organizations working together. Founded by WeBuddhist.

> **Status: 0.1.0, scaffold.** The structure, schema, scorer and rules are in place. The only items so far are clearly marked format examples (`example.jsonl`); there is no real data yet. See [CONTRIBUTING.md](./CONTRIBUTING.md) to help write it.

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
  track.json                     track version and owners
  data/<lang>/example.jsonl      format examples (never on a leaderboard)
  data/<lang>/dev.jsonl          public items
  results/<lang>/LEADERBOARD.md  ranked runs
prompts/                         standard answer prompt and judge prompt
scripts/check.py                 validate everything
scripts/score.py                 score responses
scripts/export_hf.py             build the Hugging Face release
docs/                            design, schema, scoring, review process
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

Use the prompt in [prompts/answer.md](./prompts/answer.md). Short and open answers that do not match automatically need grades from human experts or a judge panel ([prompts/judge.md](./prompts/judge.md)). Then add a row to the track's leaderboard.

## Versions

Semantic versioning for the whole benchmark (`VERSION`, git tags `vX.Y.Z`) and for each track (`track.json`):

- **patch**: fix a gold answer, typo, alias or citation
- **minor**: add items, traditions, languages or tracks
- **major**: change the item format, the scorer or the judge panel

Each release is mirrored to Hugging Face at [BuddhistAI/buddhist-bench](https://huggingface.co/datasets/BuddhistAI/buddhist-bench). Leaderboard rows cite the release and track version; never compare rows across versions.

## Related

- [BuddhistAI/buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks): task benchmarks for text-processing skills (TOC extraction, alignment, translation)
- [BuddhistAI/buddhist-skills](https://github.com/BuddhistAI/buddhist-skills): agent skills for Buddhist texts

## License

MIT, for code and data. Only contribute questions you wrote or that come from sources compatible with MIT, and say where each came from (`sources_license`).
