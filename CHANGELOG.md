# Changelog

Every release of BuddhistBench. Versions follow semver:

- **patch**: fixed gold answers, typos, aliases, citations
- **minor**: new items, traditions, languages or tracks
- **major**: changed item format, scorer or judge panel

For each release, list track versions and changed item IDs, so anyone can see why a score moved.

## [0.1.0] - 2026-11-13

First scaffold. No real data yet.

- Repository structure: core track plus tradition tracks (`theravada`, `tibetan` active; nine more planned).
- Tradition tree, topics and languages in `taxonomy/`.
- Item, response and grade schemas.
- Scorer (`scripts/score.py`, scorer 0.1.0) with per-tradition, per-type and consensus reporting and a default-school probe.
- Validator, Hugging Face export and release workflow.
- Format examples only: `example-core-en-0001`..`0007`, `example-theravada-en-0001`..`0002`, `example-tibetan-en-0001`..`0002`.

Track versions: core 0.1.0, theravada 0.1.0, tibetan 0.1.0.
