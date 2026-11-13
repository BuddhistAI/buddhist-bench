#!/usr/bin/env python3
"""Build, check and publish the Hugging Face copy of a release.

python3 scripts/export_hf.py --out build/hf              # build the folder (stdlib only; run by check.yml)
python3 scripts/export_hf.py --out build/hf --validate   # also check the card and load every config with `datasets`
python3 scripts/export_hf.py --out build/hf --push       # publish as tag v<VERSION> if Hugging Face lacks it (needs HF_TOKEN)

GitHub is the source of truth; https://huggingface.co/datasets/BuddhistAI/buddhist-bench is a
published copy, one tag per release (v<VERSION>). One config per track and language
(<track>-<lang>) with the public splits only (dev, example). Never published: the test split,
retired items, and exam items whose paper is not granted/published-open or is held out.
Imported tracks keep their own license and credits in the card. Run by .github/workflows/hf-sync.yml;
see docs/huggingface.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF_REPO = "BuddhistAI/buddhist-bench"
GH_REPO = "BuddhistAI/buddhist-bench"
PUBLIC_SPLITS = {"dev", "example"}  # test.jsonl is private and never committed; never publish it even if present
PUBLISHABLE = {"granted", "published-open", "example"}


def commit():
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "main"


def public_papers(track_dir):
    """Paper IDs whose items may be public. None means the track has no papers.json."""
    f = track_dir / "papers.json"
    if not f.exists():
        return None
    ok = set()
    for p in json.loads(f.read_text(encoding="utf-8"))["papers"]:
        perm = p.get("permission", {})
        if perm.get("status") in PUBLISHABLE and not perm.get("held_out"):
            ok.add(p["id"])
    return ok


def build(out):
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)
    version = (ROOT / "VERSION").read_text().strip()
    sha = commit()
    configs, languages, dropped = [], set(), {}
    licenses = {"mit"}
    imported = []
    for path in sorted((ROOT / "tracks").glob("*/data/*/*.jsonl")):
        track, lang, split = path.parts[-4], path.parts[-2], path.stem
        if split not in PUBLIC_SPLITS:
            continue
        tdir = ROOT / "tracks" / track
        papers = public_papers(tdir)
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        keep = []
        for r in rows:
            if r.get("status") == "retired":
                continue
            paper = (r.get("exam") or {}).get("paper")
            if papers is not None and paper not in papers:
                dropped[f"{track}-{lang}/{split}"] = dropped.get(f"{track}-{lang}/{split}", 0) + 1
                continue
            keep.append(r)
        if not keep:
            continue
        name = f"{track}-{lang}"
        dest = out / "data" / name / f"{split}.jsonl"
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Nested fields are stored as JSON strings so every config shares one flat schema.
        with dest.open("w", encoding="utf-8") as f:
            for r in keep:
                flat = {k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()}
                f.write(json.dumps(flat, ensure_ascii=False) + "\n")
        configs.append((name, split, len(keep)))
        languages.add(lang)
        meta = json.loads((tdir / "track.json").read_text(encoding="utf-8"))
        src = meta.get("source") or {}
        if src.get("kind") == "imported" and name not in {i["config"] for i in imported}:
            licenses.add(src["license"].lower())
            imported.append({"config": name, **src, "has_source_md": (tdir / "SOURCE.md").exists(), "track": track})

    lines = ["configs:"]
    for name in sorted({c for c, _, _ in configs}):
        lines.append(f"- config_name: {name}")
        lines.append("  data_files:")
        for c, split, _ in configs:
            if c == name:
                lines.append(f"  - split: {split}")
                lines.append(f"    path: data/{name}/{split}.jsonl")
    table = ["| Config | Split | Items |", "| --- | --- | --- |"]
    table += [f"| `{c}` | {s} | {n} |" for c, s, n in sorted(configs)]
    credits = []
    for i in imported:
        source_md = f"https://github.com/{GH_REPO}/blob/{sha}/tracks/{i['track']}/SOURCE.md"
        credits.append(
            f"- **`{i['config']}`** is imported from [{i['name']}]({i['url']}) (revision `{i.get('revision', '?')[:12]}`), "
            f"made by {i['maker']}. License: **{i['license']}** (not MIT); redistributed under its terms with this "
            f"attribution (license text: `sources/{i['track']}.LICENSE`). Contamination: `{i.get('contamination', 'unknown')}`. Details and changes made on import: "
            f"[SOURCE.md]({source_md})."
        )
    card = (ROOT / "docs" / "hf-dataset-card.md").read_text(encoding="utf-8")
    card = (card.replace("# {{CONFIGS}}", "\n".join(lines))
                .replace("{{LICENSES}}", "\n".join(f"- {l}" for l in sorted(licenses)))
                .replace("{{LANGUAGES}}", "\n".join(f"- {l}" for l in sorted(languages)))
                .replace("{{VERSION}}", version)
                .replace("{{COMMIT}}", sha)
                .replace("{{SHORT}}", sha[:7])
                .replace("{{TABLE}}", "\n".join(table))
                .replace("{{CREDITS}}", "\n".join(credits) or "None in this release."))
    (out / "README.md").write_text(card, encoding="utf-8")
    for f in ("LICENSE", "CHANGELOG.md"):
        shutil.copy(ROOT / f, out / f)
    shutil.copytree(ROOT / "taxonomy", out / "taxonomy")
    shutil.copytree(ROOT / "schema", out / "schema")
    for i in imported:
        if i["has_source_md"]:
            (out / "sources").mkdir(exist_ok=True)
            shutil.copy(ROOT / "tracks" / i["track"] / "SOURCE.md", out / "sources" / f"{i['track']}.md")
        if (ROOT / "tracks" / i["track"] / "LICENSE").exists():  # e.g. Apache-2.0 asks for its text to travel with the data
            (out / "sources").mkdir(exist_ok=True)
            shutil.copy(ROOT / "tracks" / i["track"] / "LICENSE", out / "sources" / f"{i['track']}.LICENSE")
    for k, n in dropped.items():
        print(f"left out {n} items of {k}: paper not public (pending or held out)")
    print(f"{len(configs)} files for release {version} in {out}")
    return version, configs


def validate(out, configs):
    from huggingface_hub import DatasetCard
    import datasets
    meta = DatasetCard.load(out / "README.md").data.to_dict()
    assert meta.get("license"), "card has no license"
    expected = {(c, s): n for c, s, n in configs}
    for cfg in meta["configs"]:
        ds = datasets.load_dataset(str(out), cfg["config_name"])
        for split, d in ds.items():
            n = expected[(cfg["config_name"], split)]
            if len(d) != n:
                sys.exit(f"{cfg['config_name']}/{split}: wrote {n} rows, loaded {len(d)}")
            print(f"  {cfg['config_name']}/{split}: {len(d)} rows")
    print("dry run OK: card parses and every config loads")


def push(out, version):
    token = os.environ.get("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set: nothing published")
        return
    from huggingface_hub import HfApi
    from huggingface_hub.utils import RepositoryNotFoundError
    api = HfApi(token=token)
    tag = f"v{version}"
    try:
        have = {t.name for t in api.list_repo_refs(HF_REPO, repo_type="dataset").tags}
    except RepositoryNotFoundError:
        have = set()
    if tag in have:
        print(f"{HF_REPO}@{tag} already published")
        return
    api.create_repo(HF_REPO, repo_type="dataset", exist_ok=True)
    # delete_patterns drops files this release no longer has (.gitattributes is always kept).
    api.upload_folder(folder_path=str(out), repo_id=HF_REPO, repo_type="dataset",
                      commit_message=f"Release {tag} ({commit()[:7]})", delete_patterns=["*", "**/*"])
    api.create_tag(HF_REPO, tag=tag, repo_type="dataset", tag_message=f"Release {tag}", exist_ok=True)
    print(f"published {HF_REPO}@{tag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build/hf")
    ap.add_argument("--validate", action="store_true", help="load every config with `datasets`")
    ap.add_argument("--push", action="store_true", help="publish to Hugging Face (needs HF_TOKEN)")
    args = ap.parse_args()
    out = Path(args.out)
    version, configs = build(out)
    if args.validate or args.push:
        validate(out, configs)
    if args.push:
        push(out, version)


if __name__ == "__main__":
    main()
