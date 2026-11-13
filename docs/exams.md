# Exam tracks

Monasteries, shedras, Buddhist universities and national exam systems already test students on exactly what their tradition considers important, at known levels, with answers marked by teachers. Testing AI on the same papers gives tradition-defined, level-graded results that are easy to explain ("this model would pass the intermediate exam at X, but not the advanced one").

## Track layout

One exam track per institution or exam system, `"kind": "exam"` in `tracks/index.json`:

```
tracks/<exam-track>/
  TRACK.md
  track.json
  papers.json                 one entry per paper, with its permission record
  data/<lang>/dev.jsonl       public items (only from papers cleared for publication)
  data/<lang>/example.jsonl
```

Items carry `exam: {paper, question, marks, marking}`; `marking` says where the gold answer came from (`official-key`, `marking-scheme`, `model-answer`, `examiner-review`). Results are reported `by_paper`, beside `by_tradition`.

## papers.json

```json
{"id": "nalanda-shedra-2025-year2-madhyamaka",
 "institution": "…", "institution_type": "shedra",
 "tradition": "tibetan.kagyu", "level": "year 2", "language": "bo", "year": 2025,
 "subject": "Madhyamaka", "source": "Paper supplied by the exam office",
 "published_online": false,
 "permission": {"status": "granted", "license": "MIT", "granted_by": "Exam office, by email",
                "date": "2026-12-01", "held_out": true}}
```

`permission.status`:

- `granted`: the institution gave written permission, including the license for the items we publish. Keep the letter or email outside GitHub and record who granted it and when.
- `published-open`: already published under an open license (e.g. the Thai Nak Tham papers released under Apache-2.0).
- `pending`: asked but not yet granted. Items may only be used in the private test split.
- `example`: format examples.

`held_out: true` keeps a paper's items out of the public `dev` split even when permission allows publishing. `scripts/check.py` enforces both rules.

## Contamination

Published papers may already be in models' training data, which inflates scores.

- Prefer **recent and unpublished papers**, and hold them out (`held_out: true`) for the private test split.
- Ask institutions for each new year's paper after the exam, and add it as a new paper ID.
- Report scores separately for papers that were `published_online` and those that were not; a large gap suggests memorisation.

## Questions and grading

- **Multiple choice and short answers**: keyed from the official answer key.
- **Essays**: turn the marking scheme or a model answer into a weighted rubric (`rubric`, weights matching the marks), written with the examiner where possible. Grade with human examiners or a calibrated judge panel ([scoring.md](./scoring.md)).
- Keep the paper's own wording. If a question depends on a figure or a set text passage, include the passage in the question or leave the item out.
- Tag the `traditions` the paper belongs to, and `type` as usual: most exam questions are `attributed` to the institution's tradition even when they don't name it, so a correct answer is that tradition's answer.

## Languages

Test in the **original language** first. An English (or other) version is a separate item with `translation_of` pointing at the original, translated and checked by a bilingual reviewer. Comparing the two shows how much a model's knowledge depends on the language of the question.

## Asking an institution

What to ask for: recent papers with answer keys or marking schemes; permission to use them for evaluating AI, and which ones may be published (under MIT) and which kept private; a contact who can review the rubrics. What they get: a report on how current AI models do on their exams, which mistakes the models make about their tradition, and credit in the benchmark.
