# Languages

The same model can answer a question about Buddhism well in English and badly in Tibetan, Thai or Vietnamese. BuddhistBench treats the **language of the question** as an axis, alongside tradition and topic, so these gaps are measured rather than hidden in one average.

## Three kinds of items

Each item says how it came to be in its language (`origin`):

| `origin` | Meaning | Rules |
| --- | --- | --- |
| `native` (default) | Written in this language by someone from a community that uses it | Normal review |
| `translated` | A faithful translation of another item (`translation_of`) | Same format, positions and choice ids as the source; a native-speaker `language` reviewer checks it against the source |
| `adapted` | Translated and changed to suit the readers (terms, examples, cultural references) | `translation_of` plus a `language` reviewer; not a strict parallel |

An original item and its translations form a **parallel group**. Translations always point at the original, never at another translation.

Native items matter as much as translations: a question first written in Thai for Thai Buddhists tests things an English question translated into Thai never will. Exam tracks are usually native in the exam's language ([exams.md](./exams.md)).

## Results by language

- Every scorer report has `by_language`, and each item row carries its `language` and `parallel` group.
- Leaderboards are per track and language (`results/<lang>/LEADERBOARD.md`), so the site can filter by language.
- `scripts/crosslingual.py RUN_en RUN_bo RUN_zh ...` compares one model's runs across languages **on the questions answered in every language**, and reports the score per language, the gap against a reference language (English by default), the largest gap, and the questions answered correctly in one language but not another. The **cross-lingual gap** is a headline number for each model.

## Prompts

`prompts/answer.md` is written in English, and the runner currently uses it for every language. For non-English tracks this mixes languages in one request. Translated answer prompts (`prompts/answer.<lang>.md`, reviewed by native speakers) are planned; until then, report the prompt language with results.

## What BuddhistBench does not test

BuddhistBench tests **knowledge about Buddhism, asked in many languages**. It does not test reading or translating Buddhist source languages (Classical Tibetan, Pali, Sanskrit, Classical Chinese), term extraction or text alignment. Those are tasks in [BuddhistAI/buddhist-benchmarks](https://github.com/BuddhistAI/buddhist-benchmarks), where skills are scored on real texts. A question asked in Tibetan here is a knowledge question that happens to be in Tibetan, not a test of reading a canonical text.
