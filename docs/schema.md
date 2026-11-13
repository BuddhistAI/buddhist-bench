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

## How each type uses positions

- **factual / citation**: one position with `consensus: true` (or tagged to the tradition whose canon it is).
- **attributed**: one position, tagged with the named tradition.
- **comparative / contested**: one position per tradition, plus a rubric.
- **default-probe**: mcq, one position per tradition, each pointing at a different choice.
- **false-premise**: one position explaining the false premise, `accept_decline: true`, and a rubric.
