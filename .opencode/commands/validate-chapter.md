---
description: Run the chapter validator and coverage check, then have Claude adjudicate the result
agent: build
---

Validate chapter $1 of the AI Infrastructure Handbook.

Validator output:

!`python3 tools/validate_chapter.py $1 2>&1`

Coverage check output:

!`python3 tools/check_coverage.py $1 2>&1`

Use the `validate-chapter` skill. For anything the two reports above don't
resolve (an UNRECORDED book, a broad corpus cross-check), launch the
`source-fidelity-reviewer` subagent with chapter `$1` instead of reading the
corpus yourself. Report PASS or a short, file:line-referenced issue list. Do
not rewrite the chapter.
