# Contributing to BuddhistBench

BuddhistBench is built by people from many Buddhist traditions. Each tradition owns its own track; the core track is owned jointly.

## Ways to help

- **Write questions** for your tradition's track or for core.
- **Review questions**, for your own tradition (same-tradition review) or another (cross-tradition review).
- **Dispute a key** you believe is wrong for your tradition: open a "Dispute an answer" issue.
- **Start a new track** for a tradition that has none: open a "Propose a track" issue.
- **Add a language**: translate and adapt a track's items with a native-speaking reviewer.

## Writing an item

1. Read [docs/schema.md](./docs/schema.md) and look at `tracks/*/data/en/example.jsonl`.
2. Add one JSON object per line to `tracks/<track>/data/<lang>/dev.jsonl`. Use the next free ID: `<track>-<lang>-<number>` (e.g. `core-en-0001`). IDs are permanent: never reuse or renumber one.
3. Tag the most specific tradition the item is about (e.g. `tibetan.sakya`, not `tibetan`, when the view is Sakya's).
4. Give sources for every key: a canonical reference (Pali `SN 56.11`, Taishō `T0262`, Tōhoku `D3871`) or a published work.
5. Fill `sources_license`: `original, MIT` for your own writing, or where it came from and its license. Do not copy questions or translations whose license is not MIT-compatible (for example CC BY-NC or ND).
6. Set `status: "active"`, `since` and `changed` to the next release version, and add yourself to `authors`.
7. Run `python3 scripts/check.py`.

### Writing good items

- **Name the tradition** whenever the answer depends on it. "According to Jōdo Shinshū, ..." not "Do Buddhists believe ...".
- **For contested questions**, write a rubric with one criterion per tradition's position, plus penalties for presenting one school's view as "Buddhism" and for invented sources.
- **Avoid loaded terms** except when quoting ("Hīnayāna"), and avoid framing any tradition as "original" or "pure".
- **Cover practice and devotion**, not only philosophy: ritual, festivals, lay life, monastic life.
- **Make it hard.** Plain multiple choice saturates quickly; prefer items a well-read generalist would get wrong.
- **LLM-drafted items** are allowed only as drafts that a human expert rewrites and signs off. Say so in `notes`.
- **Politically live disputes** (e.g. succession controversies, Dorje Shugden, disputes between Nichiren organisations) are attributed-only, reviewed by both sides, or left out.

## Review

Every non-example item needs two reviewers before it is `active` (checked by `scripts/check.py`):

- a **same-tradition** reviewer, who confirms the key is what that tradition teaches;
- a **cross-tradition** reviewer, who checks the item is clear, is not mislabelled as universal, and does not caricature another tradition.

When reviewers disagree because traditions legitimately differ, do not drop the item: add a position, turn it into a `contested` item, or mark it `disputed` with a link to the issue. Core items keyed as `consensus` need reviewers from at least three traditions.

Track owners (`.github/CODEOWNERS`) approve changes to their track.

## Disputing a key

Open a "Dispute an answer" issue with the item ID, what you think is wrong, and your sources. While it is discussed, the item can be set to `status: "disputed"` (it is then left out of scoring). The fix ships in the next patch release and is listed in the CHANGELOG.

## Submitting a run

1. Use `prompts/answer.md` exactly, at temperature 0 where possible.
2. Score with `scripts/score.py`. Grade short/open items that do not match automatically with human experts or a judge panel of at least three models from different vendors (`prompts/judge.md`); record exact model versions.
3. Add a row to `tracks/<track>/results/<lang>/LEADERBOARD.md` and put responses, grades and `scores.json` in `tracks/<track>/results/<lang>/runs/<date>-<model>/`, so anyone can re-score them.

## Releasing (maintainers)

1. Bump `VERSION` and the changed tracks' `track.json` (patch / minor / major, see README).
2. Add the CHANGELOG entry with changed item IDs.
3. Run `python3 scripts/check.py`, merge, then tag `vX.Y.Z`. The release workflow mirrors the public splits to Hugging Face.
