# Scoring

`scripts/score.py` (scorer version in the file) turns responses and grades into a report.

## Per item

| Format | Correct when |
| --- | --- |
| mcq | The chosen id equals a position's answer. |
| short | The answer matches a position's answer or alias after normalisation (case, accents, punctuation), or a grade marks it correct. |
| open | Rubric score (met positive weights + met negative weights, divided by total positive weight, clipped to 0..1) is at least 0.5. The 0..1 score itself is what is averaged. |

- A declined answer is **correct** on false-premise items and **not attempted** elsewhere.
- An empty or missing response is **not attempted**.
- Short and open answers with no automatic match and no grade are **ungraded**; reports list how many, and leaderboard rows need zero.
- `disputed`, `retired` and `example` items are skipped (`--include-examples` scores examples for format checks).

## Reports

- `overall`: mean score with counts of correct, incorrect, not attempted.
- `by_tradition`: every tradition tag, rolled up to its ancestors (an item on `tibetan.sakya` also counts for `tibetan`).
- `by_type`, `by_format`.
- `consensus_subset`: items whose positions are all `consensus`.
- `default_probe`: how often the model picked each tradition's answer. Not part of the score.

## Grades

For answers that need judgement, supply `--grades` (schema in `schema/grade.schema.json`): `grade` for short items, `criteria` (rubric id to true/false) for open items. Record the grader: a human handle, or `panel:<model>@<version>,...` for a judge panel using `prompts/judge.md`. Panels take the majority per criterion.
