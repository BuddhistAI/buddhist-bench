# Fixes

A fix is something we add to a model, without retraining it, to make its answers about Buddhism more reliable. BuddhistBench measures each fix by running the same items with and without it (`scripts/compare_runs.py`).

| Kind | What it adds | Example |
| --- | --- | --- |
| `system-prompt` | Extra instructions appended to the standard system prompt (`system.md`) | "Name the tradition you are answering from" |
| `reference` | Reference material placed before the question (`context.md`), like retrieval would | A commentary's explanation of a verse |
| `skill` | A skill from BuddhistAI/buddhist-skills, copied into `system.md` and/or `context.md` at a pinned commit | `toc-extraction-tibetan@abc123` |

Fine-tuned models are not fixes here: run them as ordinary models.

Each fix is a folder `fixes/<id>/` with `fix.json`, and `system.md` and/or `context.md`:

```json
{"id": "attribution-prompt", "kind": "system-prompt", "version": "1.0.0",
 "targets": ["misattribution", "flattening"], "authors": ["@handle"],
 "source": null, "description": "One sentence on what it changes."}
```

`targets` names the failure tags (docs/fixes.md) the fix is meant to reduce, so results can show whether it did. Change a fix only by bumping its version; runs record its version and a hash of its text.

Folders starting with `example-` are format examples.
