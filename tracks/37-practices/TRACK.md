# The Thirty-Seven Practices of Bodhisattvas

A **text track**: questions about one work, Gyalsé Tokmé Zangpo's *Thirty-Seven Practices of Bodhisattvas* (rgyal sras lag len so bdun ma), whose answers come from its commentaries. Design: [docs/intervention-study.md](../../docs/intervention-study.md).

- `commentaries.json` lists the commentaries answers can be keyed to, each with its tradition.
- Items tag the verse they are about (`passage`) and, when the question names a commentary, which one (`commentaries`). Each position says which commentaries give it and cites the page.
- Questions that name a commentary are scored against that commentary. Questions that name none, where commentaries read a verse differently, are `contested` and reward attributing each reading.
- Every answer cites its source: commentary, edition and page.

**Status:** example items only (`data/en/example.jsonl`). Their commentary answers are placeholders marked `SAMPLE`; they show the format and are not gold answers. Real items need an author and two reviewers, one from the commentary's tradition.

Sources to draw on: the root text in Tibetan and its translations, and commentaries from each school (add each one to `commentaries.json` before writing items keyed to it).

Languages to aim for: `en`, `bo`, `zh`, plus the languages of planned interventions.

Example study using this track: [studies/example-37-practices](../../studies/example-37-practices/).
