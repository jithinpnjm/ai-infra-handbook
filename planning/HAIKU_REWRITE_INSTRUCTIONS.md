# Instructions for Haiku 5.5 (opencode): warm rewrite of one chapter

Paste this whole file, or point Haiku at it, then name ONE chapter, for example: "Follow planning/HAIKU_REWRITE_INSTRUCTIONS.md and rewrite docs/part-06-hpc-slurm/02-....md". One chapter per run. Work only on that file.

Repo: `/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook`. Never commit. Never touch other chapters.

## 0. Read first (every run)
1. `planning/RULES_AND_WORKFLOW.md` section 1 (the voice). It wins over anything below if they conflict.
2. One finished example for tone: `docs/part-05-kubernetes/01-containers-from-first-principles-images-layers-registries.md` (compare `git show 6412960~1:<that file>` with the current one to see what changed).
3. The chapter's own ledgers in `planning/ledgers/` (search the chapter number) so earlier fixes are kept.

## 1. What you are making
A patient human teacher explaining to a DevOps engineer who is new to AI infrastructure. Plain words, "you", one idea per paragraph, a reason before each detail. The text must teach by itself. The reader should feel guided, never lectured, never quizzed.

## 2. Hard rules (a run that breaks any of these is rejected)
1. ADD explanation. Aim for 25 to 40 percent more words than the original (`wc -w` before and after). Never trim. A rewrite under +20 percent means you only polished; go back and add situations, walkthroughs and the why.
2. Each section opens with a real situation the reader has lived or will live (a job that crawls at night, a pod that will not start). The question comes from the situation, then the mechanism answers it. Then: intuition or picture, mechanism step by step, numbers and commands, failure modes.
3. Never announce learning goals. Delete lines like "In this chapter you will learn", "By the end you will be able to", or an outcomes checklist written as skills. If the original has an outcomes list, rewrite it as a short plain paragraph of what the chapter walks through, without "you will be able to".
4. Define each term once, in plain words, at first use. Spell out acronyms at first use.
5. Facts stay exact. Do NOT change or add: numbers, versions, flags, commands, code blocks, Mermaid, data tables, front matter, heading text and order, the Sources and review notes section, the checkpoint questions and answers (form `<details><summary>N. Question?</summary>`, count unchanged). Explanation may be added, new facts may not. Analogies must not introduce new numbers.
6. Never invent a source. Do not write "the book says", "Volume N", or attribute a claim to a book or chapter unless the original text already did and you can see it supports the claim. If you add an explanation that needs checking, list it in the ledger under "Needs source". Gem books are always named by full title, never abbreviated.
7. No drafting residue in reader text: no "(untested here)" on every line, "my tool", "earlier draft". Honest status appears once: the status row plus one plain sentence above the lab ("these steps were not run on a live cluster"). The chapter must still contain the word "untested" or "not run" or "not verified" once.
8. Style: no exclamation marks; no raw `<` or `{` outside code; backticks only for things typed or seen on screen; keep every inline code span the original had; at most one bold idea per section; bullets hold a question and the idea that answers it; tables are for lookup only; avoid semicolon chains.
9. Lab steps and exercises: one situation, one question per sentence, at most two numbers per sentence, no nested (a)(b). Keep the same count, the same commands and the same facts. Do not leave a long multi-part exercise as it was.
10. Rewrite whole sections in place, section by section, until the LAST section is done. Check the end of the file before you report. A half-rewritten chapter is a failed run.

## 3. Procedure
1. Count words: `wc -w <file>`. Note the number.
2. Rewrite top to bottom, one section at a time. Keep headings and code exactly.
3. Run the gates (all from the repo root):
   - `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: hard failures must be 0. Read every "new numbers" line and either explain it in the ledger or revert it. Compare "lost" code spans and restore them. Ignore the word-count column but do check your own +25 percent.
   - `python3 tools/restore/chain_gate.py <file>`: at most 1.5, aim for 0.2 or lower.
   - `node tools/check_mermaid.mjs` and `npm run build`: run once when the chapter is finished. Report failures; do not guess fixes outside this chapter.
4. Self-check before reporting: no outcomes-style learning-goal lines; every section opens with a situation; exercises follow rule 9; no invented attribution; last section really rewritten; word growth at least +25 percent.
5. Write the ledger `planning/ledgers/voice_rewrite_partNN_<chapter>.md`: words before and after, guard output, chain gate, Needs-source list, unresolved issues. Do not claim a gate passed unless you ran it and saw the output.
6. Add one line to `planning/EXTERNAL_EDITS.md` (see that file) so the owner and Claude know what changed outside the Claude session.

## 4. Final reply format (short)
A single table: file, words before to after, guard result, chain gate, build result, unresolved items. Nothing else.
