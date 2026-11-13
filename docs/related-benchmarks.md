# Related benchmarks

Existing benchmarks on Buddhism, other religions, and methods BuddhistBench borrows from. Compiled November 2026 from each project's own pages; corrections welcome by pull request.

**Status** says what BuddhistBench does with each set:

- **imported**: converted into a BuddhistBench track, with credit, pinned source version and license (`tracks/<id>/SOURCE.md`). Counts in aggregate scores, shown per source, and can be left out with `score.py --exclude-public`.
- **import ready**: importer written, waiting to run.
- **ask first**: worth importing, but the license is missing or unclear; ask the makers.
- **link only**: not importable (license does not allow it), or a different task (better suited to [buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks)), or not about Buddhism.

Only sets under MIT-compatible licenses can be imported (MIT, Apache-2.0, BSD, CC0, CC-BY-4.0, public domain); `scripts/check.py` enforces this.

## Buddhist

| Benchmark | Maker | Traditions | Languages | Format and size | License | Status |
| --- | --- | --- | --- | --- | --- | --- |
| [Thai Buddhist Studies Exam (Nak Tham)](https://huggingface.co/datasets/biodatlab/thai_buddhist_studies_exam) | Mahidol University biodatlab | Thai Theravāda | th | ~4,100 four-option MCQs from the 2020, 2022, 2023 national Dhamma exams, 3 levels | Apache-2.0 | import ready (`nak-tham`) |
| [BudHistBenchmark](https://mbingenheimer.net/budhistbenchmark/) | Marcus Bingenheimer | Chinese, Japanese, some Theravāda (Burma, Thailand) | en | 260 four-option MCQs on Buddhist history; top models ~95% (saturated) | not stated | ask first |
| [DharmaBench](https://aclanthology.org/2025.ijcnlp-long.114.pdf) | Reichman University, Univ. of Hamburg | Indian and Tibetan canonical texts | sa, bo | 13 classification and span-detection tasks, ~4,900 test items | CC-BY-4.0 (data), Apache-2.0 (code) | link only (text-processing tasks, fits buddhist-benchmarks) |
| [MITRA-zh-eval](https://aclanthology.org/2025.nlp4dh-1.12) | Dharmamitra (Berkeley, Temple, Düsseldorf) | Chinese canon (CBETA) | lzh → en | 2,662 sentence pairs for translation evaluation | CC BY 4.0 (paper); data on GitHub | link only (translation, fits buddhist-benchmarks) |
| [TLUE](https://arxiv.org/abs/2503.12051) | UESTC, Tibet University and others | general Tibetan knowledge (no Buddhism category) | bo | 22,963 MCQs translated from Chinese benchmarks | CC-BY-NC-SA 4.0 | link only (non-commercial license) |
| [SinhalaMMLU](https://arxiv.org/abs/2509.03162) | NAIST | Sri Lankan school exams, incl. a Buddhism subject | si | 7,044 MCQs, Buddhism count not given | not found | ask first (Buddhism subset) |
| [ThaiCLI](https://arxiv.org/abs/2410.04795) | Upstage AI, Chulalongkorn | Thai cultural alignment, 245 religion items | th | chosen/rejected pairs, judge-scored | not found | link only |
| [canoncite](https://huggingface.co/datasets/pralia-labs/canoncite) | pralia-labs | ten public-domain corpora incl. Dhammapada | en | 622 citation and abstention items | CC-BY-4.0 | link only for now (citation task; Dhammapada subset could be imported) |
| [BuddhismEval](https://huggingface.co/datasets/Nethmi14/BuddhismEval) | not verified | not verified | not verified | not verified | not verified | to check |
| [Bo-bench](https://huggingface.co/datasets/MonlamAI/Bo-bench-v1.0.0) | MonlamAI | Tibetan grammar, literature, history | bo | not verified | not verified | to check |
| [BRAND](https://arxiv.org/abs/2512.03943) | BRAC University | religious norms in Buddhism, Christianity, Hinduism, Islam | bn, en | 2,417 norms, ~70% AI-generated | not found | link only |

## Other religions

| Benchmark | Maker | What it measures | Scoring | License | Notes |
| --- | --- | --- | --- | --- | --- |
| [Flourishing AI (FAI, FAI-C)](https://arxiv.org/abs/2507.07787) | Gloo with Valkyrie, Barna, Biblica | support for well-being in 7 dimensions; FAI-C through a Christian lens | LLM judges as expert personas | question set not published | values-alignment, not knowledge; no repo yet |
| [TGC AI Christian Benchmark](https://www.christianbenchmark.ai/) | The Gospel Coalition, Keller Center | theology, ethics, attachment, Bible knowledge | scholars plus an AI grader, 1–5 | partly private | anchored to Nicene and TGC documents |
| [BibleBench](https://biblebench.vercel.app/) | Rhema (pre-launch) | biblical literacy to contested interpretation | blind LLM judges plus scholars | unknown | "tradition fairness" and "boldness" criteria |
| [FMG-Bench](https://arxiv.org/pdf/2608.12324) | Fide AI | pastoral guidance, "theological triage" | 3-judge LLM panel | unknown | names "tradition-flattening" as a failure |
| [IslamicMMLU](https://arxiv.org/abs/2603.23750) | University of Edinburgh | Quran, Hadith, Fiqh | accuracy; separate madhhab-bias task | questions not released | closest model for attribution and school bias |
| [QIAS 2025](https://sites.google.com/view/qias2025) | HBKU and partners | Islamic inheritance and assessment | MCQ accuracy | registration | shared task at ArabicNLP 2025 |
| [SectEval](https://arxiv.org/abs/2603.12768) | IIM Indore | Sunni vs Shia preference | choice distribution | CC BY-NC-ND (paper) | preference shifts with language |
| [AllFaith](https://www.alphaxiv.org/abs/2605.22975) | BYU, B.H. Roberts Foundation | asymmetry in conversion advice across 14 religions | LLM judge, human-checked | unknown | favouritism, not correctness |
| [VedantaNY-10M](https://aclanthology.org/2024.ml4al-1.23.pdf) | UT Austin | RAG on Advaita Vedanta talks | expert ratings | unknown | 25 QA triplets |

No Jewish-text benchmark was found: the Hebrew LLM leaderboard and Dicta-LM have no religious-text task.

## Methods BuddhistBench borrows

| Benchmark | What we take |
| --- | --- |
| [GPQA](https://arxiv.org/abs/2311.12022) | expert writers plus validators from outside the writer's field |
| [SimpleQA](https://openai.com/index/introducing-simpleqa/) | correct / incorrect / not attempted; rewarding honest declines |
| [HealthBench](https://openai.com/index/healthbench/) | expert-written weighted rubrics, consensus subset, judge calibrated against experts |
| [MMLU-Redux](https://arxiv.org/abs/2406.04127) | auditing answer keys; versioned corrections |
| [Humanity's Last Exam](https://arxiv.org/abs/2501.14249) | questions tested against current models; private held-out split |
| [BLEnD](https://arxiv.org/abs/2406.09948) | culture-specific questions written by people from each culture |

## Adding a set

Open an issue or a pull request adding a row. To import a set, add a track with `source.kind: "imported"` in its `track.json` (name, maker, url, revision, license, imported_on, contamination), a `SOURCE.md` saying what changed on import, and an importer script, as `nak-tham` does.
