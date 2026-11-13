# Publishing to Hugging Face

GitHub is the source of truth: items, reviews, disputes and every change happen here through pull requests. Each release is then published automatically to [BuddhistAI/buddhist-bench](https://huggingface.co/datasets/BuddhistAI/buddhist-bench) on Hugging Face, tagged with its version, so researchers can find it and load it with `datasets`. Nothing is edited on Hugging Face by hand.

```python
from datasets import load_dataset
ds = load_dataset("BuddhistAI/buddhist-bench", "nak-tham-th", revision="v0.4.0")  # pin the release you report
```

## What is published

- One config per track and language (`core-en`, `nak-tham-th`, ...), with the **public splits only**: `dev` and `example`.
- Never published: `test` (private, never committed), retired items, and exam items whose paper in `papers.json` is not `granted` / `published-open` or is `held_out`. `scripts/export_hf.py` enforces this itself, on top of `check.py`.
- The dataset card (`docs/hf-dataset-card.md`, filled in by the exporter) lists every config with its item count, the source commit, and a **Licenses and credits** section. Imported tracks keep their own license: the card's `license:` list includes it (for example `apache-2.0` for `nak-tham`), and the track's `SOURCE.md` and `LICENSE` are copied to `sources/`.
- Also copied: `LICENSE`, `CHANGELOG.md`, `schema/`, `taxonomy/`.

Nested fields (`choices`, `positions`, ...) are stored as JSON strings so all configs share one flat schema.

## How a release reaches Hugging Face

1. A maintainer bumps `VERSION` (and the changed tracks' `track.json`), adds the CHANGELOG entry and merges ([CONTRIBUTING.md](../CONTRIBUTING.md#releasing-maintainers)).
2. The `hf-sync` workflow ([hf-sync.yml](../.github/workflows/hf-sync.yml)) runs on that push to main (it also runs on a pushed `v*` tag and by hand from the Actions tab).
3. It runs `check.py`, builds the folder, checks the card and loads every config with `datasets` (dry run), then creates the git tag `vX.Y.Z` if it is missing.
4. If the `HF_TOKEN` secret is set, it uploads the release and tags it `vX.Y.Z` on Hugging Face, unless that tag is already there. Without the secret it stops after the dry run and the run stays green.

## The HF_TOKEN secret

One Hugging Face token with **write access to the BuddhistAI organization** (it may need to create the dataset repo), saved as the GitHub Actions secret `HF_TOKEN`. An organization secret on BuddhistAI (Settings → Secrets and variables → Actions → New organization secret, repository access: buddhist-bench and buddhist-benchmarks) covers both repos. Details: [buddhist-benchmarks docs/huggingface.md](https://github.com/BuddhistAI/buddhist-benchmarks/blob/main/docs/huggingface.md#the-hf_token-secret).

## Running it locally

```bash
python3 scripts/export_hf.py --out build/hf                  # build only (no dependencies)
pip install datasets huggingface_hub
python3 scripts/export_hf.py --out build/hf --validate       # dry run: check the card, load every config
HF_TOKEN=... python3 scripts/export_hf.py --out build/hf --push   # publish (normally CI does this)
```

Task benchmarks in [buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks) follow the same conventions: one Hugging Face dataset per task and language, tagged `v<version>`.
