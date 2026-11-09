---
name: Validate chapter
description: Run the Step 3 source-fidelity validation on a drafted chapter (the author says "validate P.C"). Checks numbers, sources, exercises, and labs against the corpus.
---

Full background: `planning/FLASH_ARGON_CLAUDE_WORKFLOW.md` (Step 3). This is
the condensed, token-efficient version of that step.

## Procedure

1. Run `python3 tools/validate_chapter.py <chapter-id>` yourself — this is a
   script, not a model call, so run it directly rather than delegating it.
2. For anything the validator cannot catch (an UNRECORDED book in
   `check_coverage.py`, broad corpus terms, Volume 19/20/16 cross-checks),
   launch the `source-fidelity-reviewer` subagent with the chapter ID. Do not
   open every book yourself — that is what the subagent is for.
3. Using the validator output plus the subagent's citation packet:
   - Re-check every flagged number and story against the cited source.
   - Confirm exercises are solvable from data in the exercise or chapter.
   - Confirm labs, build, lint, and mermaid checks pass
     (`tools/check_mermaid.mjs`, the repo's lint/build scripts).
4. Report **PASS** or a short list of issues with file:line references. Do not
   rewrite the chapter yourself — the author decides whether to send it back
   to Argon.

## What NOT to do

- Don't re-read already-cited sources the subagent or validator already
  confirmed.
- Don't paste large source excerpts into the reply — cite file name and
  section only.
- Don't widen scope beyond this chapter's validation.
