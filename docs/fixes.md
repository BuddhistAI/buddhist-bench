# Failures and fixes

BuddhistBench exists to find out **what goes wrong when commercial AI answers questions about Buddhism, and what fixes it**. Scores alone don't say which fix to try, so graders also record what kind of mistake each wrong answer makes, and every fix is measured against a baseline run.

## The loop

1. **Run the baseline**: the same items on each model with no fix (`scripts/openrouter_run.py`).
2. **Grade and tag failures**: for each wrong or partly wrong answer, record one or more failure tags in the grades file (`schema/grade.schema.json`). The scorer counts them overall and per tradition.
3. **Pick a fix** that targets the most common failures for a tradition, text or exam (table below).
4. **Run again with the fix** (`--fix fixes/<id>`) on the same items, models, mode and prompt variant.
5. **Compare** with `scripts/compare_runs.py BASELINE_RUN FIXED_RUN`: the change in score with a 95% interval, items repaired and broken, per-tradition change, and change in failure counts.

## Failure tags

| Tag | Meaning | Fixes to try |
| --- | --- | --- |
| `misattribution` | Gives one tradition's or teacher's view as another's | system prompt on attribution; reference material naming sources |
| `flattening` | Presents one school's view as what "Buddhism" teaches | system prompt; contested-question training material |
| `fabricated-source` | Cites a text, verse, page or teacher that does not exist or does not say that | reference material; instruction to cite only known references; search mode |
| `fabricated-content` | Invents teachings, events or details | reference material; published sourced pages (intervention studies) |
| `wrong-fact` | Plain factual error (dates, names, numbers, places) | reference material; search mode |
| `wrong-term` | Wrong or misleading rendering of a technical term | glossary as reference material; translation skills |
| `translation-error` | Misreads or mistranslates source-language text | translation skills; glossary |
| `modernist-framing` | Reframes the tradition through Western modernist assumptions (e.g. "a philosophy, not a religion", rebirth as metaphor) when the question asks what the tradition teaches | system prompt; tradition-authored reference material |
| `needless-refusal` | Declines or deflects a legitimate question | system prompt |
| `over-hedging` | Hedges when the question named a tradition and that tradition's answer is clear | system prompt |
| `unsafe-advice` | Advice that could harm (e.g. medical, crisis, unsupervised intensive practice) | system prompt; escalation guidance |

Add a tag only through a schema change (minor release), with a definition here.

## Kinds of fixes

See [fixes/README.md](../fixes/README.md). `system-prompt` adds instructions; `reference` adds material before the question, the way retrieval would; `skill` brings in a BuddhistAI/buddhist-skills skill at a pinned commit. Fine-tuned models are compared as ordinary models. Fixes that change the outside world, such as publishing accurate pages, are measured as intervention studies ([intervention-study.md](./intervention-study.md)).

## Reading results fairly

- Compare only runs with the same items, release, prompt version, mode and variant. `compare_runs.py` warns when they differ.
- A fix that adds the answer to the context (a `reference` fix written from the gold answers) proves nothing. Reference material must be written from sources independently of the items, and should be reviewed before the run.
- Report items the fix broke as well as those it repaired.
