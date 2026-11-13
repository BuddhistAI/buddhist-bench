# Item schema

One JSON object per line in `tracks/<track>/data/<lang>/<split>.jsonl`. Machine-readable schema: [`schema/item.schema.json`](../schema/item.schema.json). Examples: `tracks/*/data/en/example.jsonl`.

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | `<track>-<lang>-<number>`, or `example-<track>-<lang>-<number>`. Permanent. |
| `track`, `language` | yes | Must match the folder. |
| `type` | yes | `factual`, `attributed`, `comparative`, `contested`, `default-probe`, `citation`, `false-premise` |
| `format` | yes | `mcq`, `short` or `open` |
| `difficulty` | no | `basic`, `intermediate`, `advanced` |
| `traditions` | yes | Tradition IDs the item is about (most specific). |
| `topics` | yes | Topic IDs. |
| `question` | yes | The question as shown to the model. |
| `choices` | mcq | `[{"id": "A", "text": "..."}]` |
| `positions` | yes | Accepted answers: `[{"traditions": [...], "answer": "...", "aliases": [...], "consensus": true, "sources": [{"ref": "SN 56.11"}]}]` |
| `rubric` | open | `[{"id": "r1", "criterion": "...", "weight": 2, "tradition": "..."}]`; negative weights are penalties. |
| `accept_decline` | false-premise | Declining or rejecting the premise counts as correct. |
| `status` | yes | `active`, `disputed` (needs `dispute` link; not scored) or `retired` (kept for history; not scored or exported). |
| `example` | examples | `true` only in `example.jsonl`. |
| `since`, `changed` | yes | Release versions that added and last changed the item. |
| `authors` | yes | GitHub handles. |
| `reviewers` | yes | `[{"who": "@handle", "tradition": "theravada.thailand", "role": "same-tradition" or "cross-tradition"}]` |
| `sources_license` | yes | Origin and license, e.g. `original, MIT`. |
| `translation_of` | no | ID of the item this adapts from another language. |
| `notes` | no | Anything reviewers should know. |
| `passage` | text tracks | Verses or sections the question is about, e.g. `["v12"]`. |
| `commentaries` | text tracks | Commentary IDs (the track's `commentaries.json`) that the question names. Positions may also carry `commentaries`: the commentaries that give that answer. |

## How each type uses positions

- **factual / citation**: one position with `consensus: true` (or tagged to the tradition whose canon it is).
- **attributed**: one position, tagged with the named tradition.
- **comparative / contested**: one position per tradition, plus a rubric.
- **default-probe**: mcq, one position per tradition, each pointing at a different choice.
- **false-premise**: one position explaining the false premise, `accept_decline: true`, and a rubric.

## Text tracks

A text track (`"kind": "text"` in `tracks/index.json`) is about one work. Its `commentaries.json` lists the commentaries answers can be keyed to, each with a tradition. A question that names a commentary is `attributed` and keyed to that commentary's position; a question about a verse that commentaries read differently is `contested`, with one position per commentary. Every position cites the commentary and page in `sources`. See [intervention-study.md](./intervention-study.md).

## Other schemas

- `schema/call.schema.json`: one model call written by the OpenRouter runner.
- `schema/study.schema.json` and `schema/intervention.schema.json`: intervention studies and their log.
- Run folders: [results.md](./results.md).
