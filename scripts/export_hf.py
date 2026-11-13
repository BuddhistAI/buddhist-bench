#!/usr/bin/env python3
"""Build the Hugging Face dataset folder for a release.

python3 scripts/export_hf.py --out build/hf

Writes one config per track and language (<track>-<lang>) with the public
splits (dev, example), copies the dataset card, and stamps the release
version. Retired items are dropped; the private test split is never here.
Upload is done by .github/workflows/release.yml.
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="build/hf")
args = ap.parse_args()
out = Path(args.out)
if out.exists():
    shutil.rmtree(out)
(out / "data").mkdir(parents=True)

version = (ROOT / "VERSION").read_text().strip()
configs = []
for path in sorted((ROOT / "tracks").glob("*/data/*/*.jsonl")):
    track, lang, split = path.parts[-4], path.parts[-2], path.stem
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("status") != "retired"]
    if not rows:
        continue
    name = f"{track}-{lang}"
    dest = out / "data" / name / f"{split}.jsonl"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Nested fields are stored as JSON strings so every config shares one flat schema.
    with dest.open("w", encoding="utf-8") as f:
        for r in rows:
            flat = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()}
            f.write(json.dumps(flat, ensure_ascii=False) + "\n")
    configs.append((name, split))

card = (ROOT / "docs" / "hf-dataset-card.md").read_text(encoding="utf-8")
lines = ["configs:"]
for name in sorted({c for c, _ in configs}):
    lines.append(f"- config_name: {name}")
    lines.append("  data_files:")
    for c, split in configs:
        if c == name:
            lines.append(f"  - split: {split}")
            lines.append(f"    path: data/{name}/{split}.jsonl")
card = card.replace("# {{CONFIGS}}", "\n".join(lines)).replace("{{VERSION}}", version)
(out / "README.md").write_text(card, encoding="utf-8")
for f in ("LICENSE", "CHANGELOG.md"):
    shutil.copy(ROOT / f, out / f)
shutil.copytree(ROOT / "taxonomy", out / "taxonomy")
shutil.copytree(ROOT / "schema", out / "schema")
print(f"{len(configs)} files for release {version} in {out}")
