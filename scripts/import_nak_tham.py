#!/usr/bin/env python3
"""Import the Thai Nak Tham / Dhamma Studies exam questions into tracks/nak-tham/.

Source: https://huggingface.co/datasets/biodatlab/thai_buddhist_studies_exam
(Mahidol University biodatlab, Apache-2.0).

    # 1. See what the downloaded files contain (column names, a sample row):
    python3 scripts/import_nak_tham.py --inspect path/to/file.parquet [more files]

    # 2. Convert, naming the columns if the defaults don't match:
    python3 scripts/import_nak_tham.py --revision <hf-commit> path/to/*.parquet \
        [--col-question question --col-choices choices --col-answer answer \
         --col-year year --col-level level --col-track track --col-number number]

Reads .parquet (needs pandas + pyarrow), .csv or .jsonl. Choices may be one
list column or four columns (--col-choices a,b,c,d). Answers may be a Thai
letter (ก ข ค ง), a Latin letter, a 1-based number, or the choice text.

Writes tracks/nak-tham/data/th/dev.jsonl and tracks/nak-tham/papers.json, and
prints a summary. IDs are assigned in a stable order (year, level, track,
question number), so re-importing the same revision gives the same IDs.
Rows it cannot convert are listed, not guessed.
"""
import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACK = ROOT / "tracks" / "nak-tham"
THAI = {"ก": "A", "ข": "B", "ค": "C", "ง": "D"}
LEVELS = {"ตรี": "elementary", "โท": "intermediate", "เอก": "advanced",
          "elementary": "elementary", "intermediate": "intermediate", "advanced": "advanced"}


def read(path):
    p = Path(path)
    if p.suffix == ".parquet":
        import pandas as pd  # noqa: PLC0415
        return pd.read_parquet(p).to_dict("records")
    if p.suffix == ".csv":
        with p.open(encoding="utf-8") as f:
            return list(csv.DictReader(f))
    if p.suffix in (".jsonl", ".json"):
        text = p.read_text(encoding="utf-8")
        return json.loads(text) if text.lstrip().startswith("[") else [json.loads(l) for l in text.splitlines() if l.strip()]
    sys.exit(f"{p}: unsupported file type")


def to_list(v):
    if hasattr(v, "tolist"):
        v = v.tolist()
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            v = [x.strip() for x in re.split(r"\n+", v) if x.strip()]
    return list(v)


def strip_label(text):
    """'ก. คำตอบ' -> 'คำตอบ'"""
    return re.sub(r"^\s*([กขคง]|[A-Da-d]|[1-4])\s*[.)]\s*", "", str(text)).strip()


def answer_letter(ans, choices):
    a = str(ans).strip()
    a = re.sub(r"[.)]$", "", a)
    if a in THAI:
        return THAI[a]
    if a.upper() in "ABCD" and len(a) == 1:
        return a.upper()
    if a.isdigit() and 1 <= int(a) <= len(choices):
        return "ABCD"[int(a) - 1]
    for i, c in enumerate(choices):
        if strip_label(c) == strip_label(a):
            return "ABCD"[i]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--inspect", action="store_true")
    ap.add_argument("--revision", help="Hugging Face commit of the source files (required to import)")
    ap.add_argument("--col-question", default="question")
    ap.add_argument("--col-choices", default="a,b,c,d", help="list column, or comma-separated four columns")
    ap.add_argument("--col-answer", default="answer")
    ap.add_argument("--col-year", default="year")
    ap.add_argument("--col-level", default="exam_level")
    ap.add_argument("--col-group", default="education_level",
                    help="column that splits candidates into groups (kept as-is in the paper ID)")
    ap.add_argument("--col-number", default="", help="question-number column; default: position in its source file")
    ap.add_argument("--version", default=None, help="release version to stamp as since/changed (default: VERSION)")
    args = ap.parse_args()

    rows = []
    for f in args.files:
        for r in read(f):
            r["_file"] = Path(f).name
            rows.append(r)
    if args.inspect:
        print(f"{len(rows)} rows; columns: {sorted(k for k in rows[0] if k != '_file')}")
        print(json.dumps({k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in rows[0].items()},
                         ensure_ascii=False, indent=2, default=str))
        return
    if not args.revision:
        ap.error("--revision is required to import (pin the source version)")
    version = args.version or (ROOT / "VERSION").read_text().strip()

    def get(r, col, default=None):
        return r.get(col, default) if col else default

    converted, problems, papers = [], [], {}
    position = {}
    for n, r in enumerate(rows):
        position[r["_file"]] = position.get(r["_file"], 0) + 1
        q = str(get(r, args.col_question, "") or "").strip()
        if "," in args.col_choices:
            choices = [get(r, c, "") for c in args.col_choices.split(",")]
        else:
            choices = to_list(get(r, args.col_choices, []))
        choices = [strip_label(c) for c in choices]
        letter = answer_letter(get(r, args.col_answer, ""), choices)
        if not q or len(choices) != 4 or not all(choices) or letter is None:
            problems.append({"row": n, "file": r["_file"], "why": "missing question, not 4 choices, or answer not found"})
            continue
        year = str(get(r, args.col_year, "") or "unknown")
        level_raw = str(get(r, args.col_level, "") or "")
        level = next((v for k, v in LEVELS.items() if k in level_raw), level_raw or "unknown")
        group_raw = str(get(r, args.col_group, "") or "")
        who = re.sub(r"[^a-z0-9]+", "-", group_raw.lower()).strip("-") or "all"
        paper = f"nak-tham-{year}-{who}-{level}"
        papers.setdefault(paper, {"year": year, "level": level, "who": who, "raw_level": level_raw, "raw_group": group_raw})
        number = str(get(r, args.col_number, "") or position[r["_file"]])
        converted.append((year, level, who, number.zfill(4), q, choices, letter, paper, number))

    converted.sort(key=lambda x: x[:4])
    out = TRACK / "data" / "th"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "dev.jsonl").open("w", encoding="utf-8") as f:
        for i, (year, level, who, _, q, choices, letter, paper, number) in enumerate(converted, 1):
            item = {
                "id": f"nak-tham-th-{i:04d}", "track": "nak-tham", "language": "th", "origin": "native",
                "type": "factual", "format": "mcq",
                "difficulty": {"elementary": "basic", "intermediate": "intermediate", "advanced": "advanced"}.get(level, "intermediate"),
                "traditions": ["theravada.thailand"], "topics": ["doctrine"],
                "question": q, "choices": [{"id": "ABCD"[k], "text": c} for k, c in enumerate(choices)],
                "positions": [{"traditions": ["theravada.thailand"], "answer": letter,
                               "sources": [{"ref": f"Nak Tham exam {year}, {who}, {level}, question {number}"}]}],
                "exam": {"paper": paper, "question": number, "marking": "official-key"},
                "status": "active", "since": version, "changed": version,
                "authors": ["Thai Sangha exam office (via biodatlab)"], "reviewers": [],
                "sources_license": f"biodatlab/thai_buddhist_studies_exam@{args.revision}, Apache-2.0",
                "notes": "Imported. Topic tags not yet assigned; 'type' defaults to factual.",
            }
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    meta = {"_comment": "Generated by scripts/import_nak_tham.py. One paper per year, candidate group (the source's education_level, kept as given) and level.",
            "papers": [{
                "id": pid, "institution": "Thai national Dhamma exams (Sanam Luang Dhamma Studies)",
                "institution_type": "national exam system", "tradition": "theravada.thailand",
                "level": p["level"], "language": "th", "year": int(p["year"]) if p["year"].isdigit() else p["year"],
                "subject": "Dhamma", "candidates": p["who"],
                "source": f"https://huggingface.co/datasets/biodatlab/thai_buddhist_studies_exam (revision {args.revision})",
                "published_online": True,
                "permission": {"status": "published-open", "license": "Apache-2.0", "granted_by": None,
                               "date": str(date.today()), "held_out": False},
                "raw": {"level": p["raw_level"], "group": p["raw_group"]}}
                for pid, p in sorted(papers.items())]}
    (TRACK / "papers.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not converted:
        print(json.dumps({"imported": 0, "problems": problems[:5]}, ensure_ascii=False, indent=2))
        sys.exit("nothing imported: check the column names with --inspect")
    print(json.dumps({"imported": len(converted), "skipped": len(problems), "papers": len(papers),
                      "problems": problems[:20]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
