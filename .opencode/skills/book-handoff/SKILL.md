---
name: Book handoff
description: Resume work on the AI Infrastructure Handbook without re-scanning the repo or re-reading finished chapters. Use at the start of any session that drafts, edits, or plans handbook chapters.
---

## Read these files, in order, once per session

1. `planning/MASTER_REWRITE_PLAN.md` — if a re-processing pass is active, find
   the next unchecked `[ ]` item there and execute it directly. Do not re-scan
   the repository or re-read other chapters to "catch up" — this file and
   `planning/STATUS.md` are the authoritative state.
2. `planning/PROJECT_MAP.md`, `planning/STATUS.md`, `planning/CURRICULUM_MAP.md`.
3. `planning/INTERVIEW_TOPICS.md` and `planning/JD_MAPPING.md` only if scope is
   unclear.

## Rules (full detail lives in the files above — this is the short form)

- Work only the next unfinished item in `STATUS.md` / `MASTER_REWRITE_PLAN.md`
  unless told otherwise.
- Depth over compression: match the source books' depth; split a topic into
  multiple chapters rather than shortening it.
- Every non-obvious claim needs a source. Use `tools/study_rag/query.py` to
  search the corpus before writing, across several books.
- Do not do broad "read every related book/file" research yourself. Launch the
  `source-fidelity-reviewer` subagent with the chapter ID and the terms you
  need sourced, and work from its condensed citation list. Only read a source
  file directly when you need to quote or verify one specific passage the
  subagent flagged.
- Update `planning/STATUS.md` when done (status, word count, open/untested
  items). Keep chat replies short — the depth belongs in the chapter files.
- If instructions conflict or scope is unclear, ask the author; do not widen
  scope or silently change the template.

## When validating a drafted chapter

Use the `validate-chapter` skill (or `/validate-chapter <id>` command) instead
of re-deriving the Step 3 checklist from memory.
