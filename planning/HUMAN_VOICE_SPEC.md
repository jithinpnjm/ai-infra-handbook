# Human-teacher voice rewrite: spec for rewrite agents (Kimi or DeepSeek) and for the review that follows

The owner approved the style of the Part 1 (30 chapters) and Part 3 (17 chapters) rewrite done with Kimi K3 and DeepSeek sub-agents (commits 9394a58 to dc13719). This file turns that result into a repeatable brief for the remaining parts (0, 2, 4 to 20) and defines how the rewrite is reviewed. Longer chapters are fine: the Part 1 rewrite grew about 6 percent and Part 3 about 8 percent, with no change to code blocks and almost none to numbers. Quality and clarity beat length.

## What the approved style looks like (read two chapters first: docs/part-01-linux/08-processes-signals-and-job-control.md and docs/part-03-python/06-concurrency-threads-processes-and-asyncio.md)
1. Each section opens with a real situation the reader has been in or will be in (a job that crawls at night, a pod that will not terminate, a fleet script that hangs) and only then explains the mechanism.
2. The author speaks to the reader as "you" and sometimes "we" for working through an example. Plain words, one idea per paragraph, a reason before each detail, short transitions that say where the section is going ("Signals come next, followed by job control").
3. Lists stay short. Bullets hold a question and the idea that answers it, not a pile of terms. Tables are for lookup only.
4. A new term is defined once, in plain words, at first use. Acronyms are spelled out the first time.
5. Numbers, commands, flags, names, versions and code are exactly as they were. Added sentences explain, they do not add facts.
6. The ramp: plain intuition and a picture first, then the mechanism, then numbers and commands, then failure modes and expert detail. A beginner follows the first half, an expert is not bored by the second.
7. Drafting residue never appears in reader text: no "Volume N", no "the book says", no "(untested here)" on every line, no "my tool", no "earlier draft", no borrowed "Table 8-3" labels. Attribution lives in the Sources and review notes section. The honest status appears once per chapter (for example the status row and one sentence above the lab).
8. Exercises: one situation, one question per sentence, at most two numbers per sentence, no nested (a)(b) pile-ups. Checkpoint questions keep their required form (`<details><summary>1. Question?</summary>` newline answer newline `</details>` blank line) and their count.
9. Never abbreviate a gem book (no ASP, HLW, SCL, PK). Use the full title.

## Hard rules for every rewrite (a script checks them)
- Front matter, headings (wording may be improved only if the section order stays), code blocks, Mermaid diagrams, tables of data, the checkpoint question count, and the Sources section structure stay. Code blocks must be byte-identical.
- No new numbers, no new commands, no new claims. If an explanation needs a fact that is not in the chapter, leave it out or put a short "Needs source" line in the ledger.
- Known errors listed in planning/review/OPUS_REPORT_1.md and OPUS_REPORT_2.md (section 6 watch lists, section 5 rework instructions) and in planning/FIX_WORKLIST.md are fixed or flagged, never silently kept and never silently changed: record each as fixed with its source, or unresolved.
- Chapters already reworked by the Claude workers (see git log, messages starting "Rework", "Rebuild" or "Fix") keep their corrections. Do not reintroduce a corrected error: read the chapter's ledger in planning/ledgers/ (rework_*, fixes_*, voice_rewrite_*) first.
- No exclamation marks in prose, no semicolon chains (python3 tools/restore/chain_gate.py FILE must stay at 1.5 or lower), no raw `<` or `{` outside code, no `$...$` math with stray backticks.

## How the review works (what the owner asks Claude to do after a batch)
1. Commit the batch with the parts named in the commit message.
2. python3 tools/rewrite_guard.py BASE_REF HEAD_REF docs/part-NN-... : hard failures (front matter, code blocks, checkpoint count) must be zero. Read every "new numbers" line: each must be explained or reverted. Review lost numbers and lost or new code spans the same way.
3. python3 tools/restore/chain_gate.py, python3 tools/language_audit.py (no new warnings), node tools/check_mermaid.mjs and npm run build.
4. Read-through: Claude reads a sample of about 6 paragraphs per chapter, grades them with planning/VOICE_AUDIT_PROMPT.md, and reads the opening, one deep section and the exercises of the 10 chapters with the lowest guard scores. Findings go back as a list of chapter, line, problem, suggested fix.
5. Factual spot check of the claims the rewrite touched, against the gem books or vendor documents.

## Order of work (suggestion)
Part 2 (networking), Part 4 (automation), Part 5 (Kubernetes), Part 6 (Slurm), Part 7 and 8 (BMC, BCM), Part 9 (systems), Part 10 (CUDA), Part 11 (GPU Kubernetes, except 11.31 to 11.34), Part 12 to 15, Part 16 to 19, then Part 20 (the Nebius interview volume) and Part 0.
Part 20 note: its first-person lines record what was verified. Keep the honest uncertainty in a natural voice, move test-log language to the Verification log.
