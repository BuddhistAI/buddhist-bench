# Core track

The part of BuddhistBench every tradition shares. It asks two things of a model:

1. **Pan-Buddhist knowledge**: facts every tradition's reviewers accept (the first teaching, the Three Jewels, the main canons and their languages).
2. **Correct attribution across traditions**: does the model know which tradition holds which view, answer from inside a tradition when the question names one, and lay out the differing positions when it does not?

Deep, tradition-internal questions belong in that tradition's own track, not here.

## What goes in core

| Type | Share of the track (target) | Notes |
| --- | --- | --- |
| factual | 25% | Only answers marked `consensus` by reviewers from at least three traditions |
| citation | 10% | Canonical references from several canons (Pali, Taishō, Tōhoku) |
| attributed | 25% | Spread evenly across traditions; the key is the named tradition's view |
| comparative | 15% | Rubric written with a reviewer from each side |
| contested | 15% | Rubric rewards naming positions; penalises presenting one school as "Buddhism" |
| false-premise | 5% | Invented texts, misattributed quotes |
| default-probe | 5% | Reported as a distribution, not accuracy |

Keep traditions balanced: no single tradition should be the subject of more than 25% of core items.

## Ownership and review

Core is owned jointly. A core item needs a reviewer from the tradition it is about and one from a different tradition. Factual items marked `consensus` need sign-off from reviewers of at least three traditions (for example Theravāda, East Asian and Tibetan).

## Data

- `data/<lang>/example.jsonl`: format examples, never scored on a leaderboard.
- `data/<lang>/dev.jsonl`: public items (none yet).
- Test items are private (see [docs/design.md](../../docs/design.md#public-and-private-splits)).

## Results

`results/<lang>/LEADERBOARD.md`.
