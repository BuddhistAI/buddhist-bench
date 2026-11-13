# Answer prompt (prompt version 0.2.0)

Use this exact system prompt and user template for leaderboard runs. Record the prompt version and variant in the run. `scripts/openrouter_run.py` builds these prompts; if you change this file, change the runner and bump the version.

Version 0.2.0 adds the `sourced` variant and the search-mode notes; the `plain` prompts are unchanged from 0.1.0.

## System

You are answering questions about Buddhism. Answer accurately and concisely. If a question names a tradition, answer from that tradition's point of view. If traditions disagree and the question does not name one, say which traditions hold which views. If you do not know, or the question rests on something that does not exist, say so instead of guessing.

## User: multiple choice (mcq)

{question}

{choices, one per line as "A. text"}

Reply with only the letter of your answer, or DECLINE if you cannot answer.

## User: short answer (short)

{question}

Reply with only the answer, in as few words as possible, or DECLINE if you cannot answer.

## User: open answer (open)

{question}

Answer in at most 200 words.

## Sourced variant

Same system prompt. The user template ends with a different reply instruction, because asking for sources is what we expect to make models search:

- mcq: `Reply with the letter of your answer on the first line, or DECLINE. Then list the reliable sources that support it.`
- short: `Reply with the answer on the first line, in as few words as possible, or DECLINE. Then list the reliable sources that support it.`
- open: `Answer in at most 200 words, and cite reliable sources for your answer.`

The answer is the first line for mcq and short items, and the whole reply for open items.

## Search modes

The prompts are identical in every mode (`closed-book`, `native-search`, `logged-search`, `forced-search`). Only the tools offered differ, so differences between modes measure the effect of search. In `logged-search` the model gets two function tools:

- `web_search(query)`: "Search the web. Returns up to 8 results with title, URL and snippet."
- `fetch_url(url)`: "Fetch a web page and return its text (first 8,000 characters)."

## Converting replies to responses.jsonl

- mcq: `{"id": ..., "answer": "B"}`; a reply of DECLINE becomes `{"id": ..., "declined": true}`.
- short: `{"id": ..., "answer": "<reply>"}`; DECLINE as above.
- open: `{"id": ..., "answer": "<reply>"}`. Whether an open answer declined is decided by its rubric.
