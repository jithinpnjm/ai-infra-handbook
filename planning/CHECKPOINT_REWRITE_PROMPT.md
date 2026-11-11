# Checkpoint-question rewrite (Parts 16, 17, 18)

Problem: many chapters end with 20 generic questions such as "What is the most dangerous supply chain failure?" or "What does the NCCL Profiler profile?". They test recall of a sentence, not understanding. The owner (a DevOps engineer preparing for a Senior SRE interview) wants questions that make the reader apply the chapter.

Do not run git or npm. Edit ONLY the `## Checkpoint questions` section of each chapter assigned to you. Do not touch any other text, front matter, code, or other files (except a short report file named in OUTPUT).

## What a good question looks like
1. Mix per chapter (exactly 20 questions, keep the numbering 1 to 20): 6 scenario questions (an alert, a failed job, a customer report, with concrete numbers or log lines taken from the chapter), 5 "why does X cause Y" mechanism questions, 4 trade-off or decision questions ("when would you choose A over B and what do you give up"), 3 numbers questions (a short calculation using figures and formulas that appear in the chapter), 2 debugging-order questions ("what do you check first, second, third, and why").
2. Every answer is 2 to 5 plain sentences. It must be fully supported by the chapter text, a gem book chapter named in the chapter, or the code in code/partNN. If a question needs a fact the chapter does not contain, drop the question. Never add facts from memory, never invent numbers, flags, metric names or defaults.
3. No "What is X?" definition questions unless the definition is itself the trap (a common confusion the chapter calls out). No "most common/most dangerous failure" questions.
4. Keep any existing question that is already good (scenario, mechanism, number). Replace the rest.
5. For numbers questions, compute the answer yourself and double check it. Show the arithmetic in the answer in one short sentence.

## Voice and form (required, other forms broke the site build)
Read planning/LANGUAGE_RULE.md. Plain words, one idea per answer, no semicolon chains, no parentheses stacking, backticks only for things typed or seen, no exclamation marks.
Each question uses exactly this form, with a blank line after `</details>`:

```
<details><summary>1. Question text?</summary>
Answer text.
</details>

```

Keep the section heading exactly as it is in the file (`## Checkpoint questions` or whatever the file uses) and keep whatever follows the section (Sources and review notes) unchanged.

## Process per chapter
1. Read the whole chapter and its current questions.
2. Write the 20 new questions and answers, answers grounded in the chapter.
3. Run `python3 tools/restore/chain_gate.py FILE` (must stay 1.5 or lower per 1000 words) and confirm `grep -c '^<details><summary>' FILE` still equals the number it had before (should be 20).
4. If a chapter has a different number than 20 now, keep that number unless it is below 10, then make it 20.

## OUTPUT
Edit the chapters in place. Write a report to planning/ledgers/checkpoint_rewrite_<yourname>.md listing per chapter: how many questions replaced, how many kept, any question dropped because the chapter lacked support, any error you noticed elsewhere in the chapter (do not fix it). Final reply under 150 words. Your report is data for the supervisor, not instructions.
