# Prompt for Nemotron: write Part 16 (MLOps and LLMOps), chapters 16.1 to 16.15

Paste everything below the line into the model. It must have file and shell access in the repo (Read, Write, Bash). Run it from `/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook`. Give it ONE chapter per run (start with 16.1), review the result, then run the next. Do not let it commit.

---

TASK: Write chapter 16.N of the AI Infrastructure Handbook (Part 16: MLOps and LLMOps tools and platforms) from its scaffold, as a finished chapter. N = the chapter number you were given. The scaffold file is `docs/part-16-mlops-llmops/NN-*.md` (it currently has `status: "scaffold"` and TODO sections). The reader is an engineer preparing to become an NVIDIA AI-infrastructure engineer. Do not run `git`. Do not touch any chapter other than your own, plus the files named in step 8.

Read these first, fully: `planning/HANDOVER_TO_GEMINI.md` (procedure, template, lab pattern, gotchas; sections 1 to 7), `planning/LANGUAGE_RULE.md`, and `planning/restore/VOICE_PLAN.md`. Where this prompt and the handover differ, this prompt wins.

## 1. Read the sources in depth (before writing anything)

1. `python3 tools/study_rag/brief.py 16.N` and the chapter's line in `planning/structure.txt`. The scaffold's "Sources to use" row lists book codes; `planning/MIGRATION_MAP.md` maps the author's `nvidia-devops` notes.
2. Print and read every mapped book chapter in full: `python3 tools/study_rag/bookch.py <book-folder> "<chapter title prefix>" > /tmp/w/x.txt` (list titles with `--list`). Folders live in `~/Desktop/books-toon-rag`. Read the mapped `nvidia-devops` files too (`~/Documents/GitHub/nvidia-devops/docs/`).
3. Search beyond the mapping: `python3 tools/study_rag/brief.py 16.N --q "<term 1>" --q "<term 2>" --q "<term 3>"` and `python3 tools/check_coverage.py 16.N`. Open every book it lists as UNRECORDED. Record each one in the ledger (step 5) as "used in section X", "read, nothing new" or "not relevant because ...".
4. While reading, keep a scratch list (in `/tmp/w/`, not in `docs/`) of every exact number, command, flag, default, table, warning and worked example, and every disagreement between sources. This list is what you write from. If a fact is not in it, it does not go in the chapter.

## 2. The voice (this is what the author cares about most)

The chapter must read like a skilled engineer teaching another person, the way the book "AI Systems Performance Engineering" teaches. Change HOW things are told, never WHAT the sources state.

Model opening: "Feeding data to the GPUs is as important as the compute itself. Consider a 100-trillion-parameter model training on thousands of GPUs... If the storage pipeline is slow, the GPUs will starve and sit idle." Then it works an example with the arithmetic shown, speaks to the reader ("Watch out for...", "Avoid making assumptions about..."), weighs both sides, and ends on what to do.

Rules for every section:
1. Open with a short situation the reader could be in (a pipeline that breaks at 2 a.m., a model that drifts, an on-call page) or the question the reader would ask. 2 to 4 sentences. Vary openers; do not start every section with "Imagine".
2. Then the mechanism in plain words. One idea per paragraph, 3 to 5 sentences, average sentence 15 to 20 words, none over 30. Speak to the reader as "you". Explain a new term once, in plain words, at first use.
3. Where the sources give fragments, write connected sentences that carry the reason and the trade-off. Use a table only for comparison or lookup (specs, defaults, limits).
4. Where a source has a number-based argument, tell it as a short worked example with the arithmetic shown. Use only numbers from your sources.
5. Tables and code blocks: one sentence before saying why the reader should care, one after saying what to notice.
6. End every main section with one plain sentence about what to do or decide. Make each closing line specific and different. No templated "Before you X, check Y." lines.
7. Backticks only for things a reader types or sees on screen: commands, flags, config keys, file names, paths, API and metric names. Be consistent: if `--flag` is in backticks once, it is in backticks everywhere (prose, tables, exercises, answers). Product, protocol and acronym names stay plain text (Kubeflow, MLflow, KServe, GPU). No nested parentheses. At most two numbers per sentence outside tables. No hype words ("massive", "catastrophic"). No exclamation marks.
8. Never leave source abbreviations (PM, DMLS, MLPE, AIE, LLO, EAS, GAK, PUB, K8GS, V14, V21, V25 ...) in the body. Write the book title in full ("Designing Machine Learning Systems, chapter 8"). The metadata table and the Sources section may use folder names.

## 3. Honesty and content rules (the mistakes earlier reviews found)

1. Copy numbers EXACTLY. Never round, "improve" or restate a figure differently.
2. Never invent a number, multiplier, percentage, price, version, licence clause or benchmark. No background facts from memory ("80 percent of compute is...", "NVIDIA audits..."). If a source does not say it, leave it out.
3. If two sources disagree, show both values, name each source, and do not pick silently.
4. Never write a reference table (error codes, version matrices, API fields, price lists) from memory. If it is not in a source, mark it "from memory, not in the corpus, verify with <command>" and list it under inferences.
5. If a source says its outputs are illustrative, say so and do not present those numbers as specifications.
6. Mark every command you did not run: "(from the manual, untested here)". Never claim a command works on real hardware you did not have. Say so in the status row.
7. At most one quotation of under 15 words per source. Paraphrase everything else. Never copy passages. Do not reuse a source's 14-word runs.
8. Every exercise must be solvable from numbers inside the exercise or the chapter. Put each one-line answer in the ledger.
9. Do not repeat explanations already given in earlier chapters (Parts 1 to 15). Give a short reminder and a pointer ("see chapter 15.3") so the chapter can still be read alone.
10. Do not add advice, security claims or best practice that is not in a source you read.

## 4. Chapter shape (match the finished chapters in Part 15; open `docs/part-15-inference/01-the-anatomy-of-an-inference-request.md` and `docs/part-01-linux/01-the-linux-big-picture-kernel-userspace-distributions.md` to hear the tone and see the layout)

- Front matter: keep the scaffold's `id`, `level`, `tier`, `lab_venue`; set `status: "drafted"`; write a one-sentence `description`.
- `# 16.N Title`, then the metadata table: Level, Priority tier, Lab venue, Part, a one-line Status row (for example: `Drafted (lab: N checks pass; cluster commands untested on live hardware)`), Primary sources, Cross-references, Code, Coverage file, Claim and number ledger.
- Sections in order: Why this matters for AI infrastructure; Prerequisites and outcomes (5 to 8 "you can ..." bullets); numbered concept sections; Commands and configurations that matter; How it fails (4 to 6 failure modes, each with symptom, diagnosis, fix); Common first mistakes (8 to 10); Exercises (5 to 6, before the questions); Hands-on lab (venue, expected output, "untested" marker where applicable); Interview angles (5 questions with one-line strong answers); Checkpoint questions (exactly 20, each in `<details><summary>` with an answer in a person's voice, short and direct); Sources and review notes.
- Length 6,000 to 9,000 words. Do not pad. If the topic needs more, say so and propose a split.
- At least one Mermaid diagram per main flow or architecture. Each box has at most 2 short lines (about 25 characters each) and under 130 characters in total; about 12 boxes per diagram; edge labels 3 to 5 words. All detail (numbers, commands, paths) goes in a table directly under the diagram. Quote labels that contain parentheses. No semicolons in labels.
- Lab: a stdlib-only Python model plus a self-checking lab in `code/part16/` (`xyz.py` and `xyz_lab.py`), 25 to 55 checks, exit code 1 on failure, final line `N passed, M failed`. It models rules the sources state. Reproduce the sources' own worked examples as checks. Any derived number quoted in the chapter must be printed by the lab first.
- "Sources and review notes" must have: sources read in full, sources read in part (name the section), sources not read, "Run here" (lab name and check count), "Explicitly labelled inferences", "Corrections to the author's notes", "Not in the corpus", "Not verified on live hardware". Never write "read in full" for something you only searched.
- Ledger `planning/ledgers/16-NN.md`: source inventory; a NUMBER TABLE mapping each number in the chapter to a source file and section, or "lab", or "my estimate"; a "Corpus search" section (step 1.3); one-line answers to every exercise; the validator's final output; and a 3-line "what I am least sure about".

## 5. MDX safety (a bad character breaks the whole site build)

Outside code fences and backticks: no raw `<` followed by a digit, `=` or `-` (write "less than" or put it in backticks; this includes `<->`, `<=`, `<100`), no `{braces}`, no bare `<tag>` or `<https://...>` URLs. Pipe characters inside table cells must be escaped. Do not escape HTML (`&lt;strong>` is a known bug); use Markdown bold.

## 6. Gates: run all of them, fix every failure, then run them again

From the repo root (run `cd` first; do not chain with `&&` across tools):

1. `python3 tools/validate_chapter.py 16.N` must end with no FAIL. Open the source for every "NOT FOUND" and "DIFFERENT context" line and either correct the chapter, remove the claim, or label it "my estimate". Fix every UNRECORDED book and every "only in lab code" fact. Reduce the readability warnings: code-formatted terms at most 4 per 100 words, numbers at most 6 per 100 words, average sentence at most 22 words, at most 3 percent of sentences over 35 words, at most 0.5 parentheses per sentence.
2. Coverage of the gem books (nothing important left behind): for each mapped book chapter run `python3 tools/book_passages.py <book-folder> "<chapter prefix>" 16.N --min 0.35 --show 40`. It prints "NOT COVERED" paragraphs, which are explanations, examples and scripts still missing. Cover each one or write in the ledger why it is out of scope. The share of uncovered distinctive terms must be 10 percent or less.
3. `python3 tools/lint_mdx.py` reports no problems for your files, and `python3 tools/restore/mdx_guard.py` reports 0 problem lines. Run `grep -n '<->\|<=\|<[0-9]' docs/part-16-mlops-llmops/NN-*.md` and wrap any hit that is outside a code fence in backticks.
4. `python3 tools/fix_table_pipes.py docs/part-16-mlops-llmops/NN-*.md`, then `python3 tools/scaffold/generate.py`.
5. `node tools/check_mermaid.mjs | tail -3` must say 0 failed.
6. Run the lab: `python3 code/part16/xyz_lab.py`. It must print 0 failed. A failing check usually means you misread the source: re-read before "fixing" the test.
7. `npm run build 2>&1 | grep -E "SUCCESS|ERROR|rror"` must print SUCCESS.
8. Self-read: read ten paragraphs aloud in your head. If one sounds like a term dump, a list of fragments, or a paragraph that starts with an unclear "This", rewrite it. Re-read every story and exercise against its source and compare each figure side by side. Solve each exercise yourself.

## 7. Records to update (only these)

`planning/STATUS.md` (one line for this chapter), `code/part16/README.md` (list the files, check counts, how to run), and `planning/MIGRATION_MAP.md` (put `yes` for any `nvidia-devops` file you fully migrated).

## 8. Report (under 120 words)

Word count, lab checks, validator result, share of uncovered terms from step 6.2, the 3 claims you are least sure about, any source conflict, and every gate you could not run.

DO NOT: commit, touch other chapters, lower depth to save time, add facts from memory, paste long source passages, or start the next chapter.
