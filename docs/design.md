# Design

Why BuddhistBench is shaped the way it is. Based on a survey of existing religion and knowledge benchmarks (Gloo's Flourishing AI, the TGC Christian benchmark, BibleBench, FMG-Bench, IslamicMMLU, QIAS, SectEval, BudHistBenchmark, the Thai Nak Tham exam set, DharmaBench, TLUE, GPQA, HealthBench, SimpleQA, MMLU-Redux, Humanity's Last Exam).

## Scope

Version 1 measures **knowledge and correct attribution**: does a model know what each tradition teaches, practises and remembers as its history, and can it keep the traditions apart? Whether a model gives good guidance "through a Buddhist lens" (as Gloo's FAI-C does for Christianity) is a different question with riskier scoring; it can become its own track later.

## Core plus tradition tracks

- No single answer key can speak for every tradition, so each tradition owns the items about itself and decides its own keys.
- The core track holds what the traditions share, and tests attribution across them.
- Tracks report separately. A model can be strong on Gelug and weak on Jōdo Shinshū, and the results should show it.

A tradition track covers one node of the tradition tree and everything below it. Items inside a track are still tagged with the most specific tradition, so the Tibetan track can report Sakya and Kagyu separately.

## Attributed and unattributed questions

Other benchmarks disagree about hedging. The TGC benchmark and BibleBench penalise "all sides" answers; FMG-Bench penalises "tradition-flattening". BuddhistBench uses the question to decide:

- **Attributed** (the question names a tradition): the key is that tradition's answer. Answering from another school is wrong, and needless hedging is not rewarded.
- **Contested** (traditions differ, none named): the rubric rewards naming each position with its tradition and penalises presenting one as "Buddhism".

## Positions, not one answer

Every item stores its key as a list of **positions**, each tied to tradition IDs and sources. A factual item has one position marked `consensus`. A contested item has several. This lets the scorer report which tradition's answer a model gave, and lets a tradition add its position later without rewriting the item.

## Default-school probe

Models tend to default to the most-written-about view (Gelug for Tibetan Buddhism, Zen for East Asian, Western modernist framings in general). Following IslamicMMLU's madhhab-bias task, a `default-probe` item offers each tradition's answer as a choice without labels. It has no right answer; the scorer reports the distribution, and a strong lean is a finding.

## Three outcomes

Following SimpleQA, every answer is correct, incorrect or not attempted. Declining is better than fabricating, and false-premise items reward declining. Reports show the incorrect rate separately so a model cannot hide confident errors behind a high attempt rate.

## Review

Following GPQA, every item has a same-tradition reviewer and a cross-tradition reviewer. Disagreements caused by real differences between traditions become extra positions or contested items, not deletions. IslamicMMLU's single-reviewer validation is the weakness to avoid.

## Judges

Open answers are graded against expert-written, weighted rubrics (HealthBench style), by human experts or a panel of at least three judge models from different vendors. Judges are calibrated against human grades on a sample (report agreement), and every leaderboard row records exact judge versions, because judge models drift (Gloo reports this for its GPT-4o judges).

## Public and private splits

- `example`: format examples, never scored.
- `dev`: public items, for development and transparency.
- `test`: private, held by maintainers, refreshed with each major release, never committed or mirrored. Leaderboards will use it once it exists; until then rows use `dev` and say so.

Public files carry a canary string in the Hugging Face card so contamination can be detected.

## Versioning

Semver at two levels: the release (`VERSION`, git tag) and each track (`track.json`). A gold-answer fix in the Tibetan track bumps the release patch version and the Tibetan track's patch version; other tracks keep their version, so their results stay comparable. Items carry `since` and `changed`, and are retired rather than deleted.

## Saturation

BudHistBenchmark reached 95% within a year of multiple-choice questions, and models score about 99% on a seminary Bible exam. Multiple choice is kept as a floor; most effort should go into attributed, comparative, contested, citation and false-premise items.

## Languages

Each language is its own data set, written or reviewed by native experts, not machine-translated (TLUE shows translated benchmarks lose cultural content). `translation_of` links an item to its source item when one is adapted from another language.
