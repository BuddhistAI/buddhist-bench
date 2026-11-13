# Judge prompt (judge prompt version 0.1.0)

For grading open answers against an item's rubric, and short answers that did not match automatically. Use a panel of at least three models from different vendors, record exact versions, and take the majority per criterion. Calibrate on a sample graded by human experts of the relevant tradition before trusting a panel.

## Open answers

You are grading an answer to a question about Buddhism against a rubric written by experts. Judge each criterion independently and literally. Do not reward length or style. A criterion about a tradition's position is met only if the answer states that position and attributes it to that tradition (or a clearly equivalent name).

Question:
{question}

Answer to grade:
{answer}

Criteria:
{for each rubric item: "<id>: <criterion>"}

Reply with JSON only: {"<id>": true or false, ...}

## Short answers

You are checking whether an answer to a question about Buddhism matches an accepted answer. Spelling, transliteration and translation differences are fine; a different referent is not. If the answer hedges between a correct and an incorrect answer, it is incorrect.

Question: {question}
Accepted answers (with tradition): {positions}
Answer to grade: {answer}

Reply with JSON only: {"grade": "correct" | "incorrect" | "not_attempted", "matched_tradition": "<id or empty>"}
