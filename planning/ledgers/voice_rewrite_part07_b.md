# Voice rewrite, Part 7 chapters 7.4, 7.5, 7.6 (batch b)

Scope: docs/part-07-redfish-bmc/04-redfish-authentication-sessions-and-security.md, 05-redfish-actions-tasks-events-and-subscriptions.md, 06-the-redfish-schema-reading-csdl-json-schema-and-the-resource-guide.md. Uncommitted. planning/EXTERNAL_EDITS.md was not edited (per owner instruction). Other Part 7 files (01, 02) were modified by another session and were not touched.

Note: 05 and 06 were reported as changed on disk during the run (outside this session). The current on-disk state was kept, and all gates were re-run after that change.

## Gates

| Chapter | Words (wc) before to after | Guard (`rewrite_guard.py HEAD WORKTREE`) | Chain gate |
|---|---|---|---|
| 04 authentication | 6328 to 7928 (+25.3%) | 0 hard failures; guard count 6008 to 7608; new numbers 0; lost numbers 0; residue 3 to 0 | 0.0 per 1000 words |
| 05 actions/tasks/events | 6099 to 7694 (+26.1%) | 0 hard failures; guard count 5712 to 7307; new numbers 0; lost numbers 0; residue 5 to 1 (heading "In my lab", locked) | 0.0 per 1000 words |
| 06 schema | 6235 to 7838 (+25.7%) | 0 hard failures; guard count 5752 to 7355; new numbers 0; lost numbers 0; residue 3 to 0 | 0.0 per 1000 words |

Code spans: checked by set comparison (Counter of inline backtick spans, HEAD vs WORKTREE). Lost spans: none in 04 or 06; none in 05 after restoring the `200`, `202`, `204` spans from the old prerequisites list. The guard still prints "lost 1" or "lost 2" for 04 and 05 because of its pairing artifact.

Code blocks, the Mermaid diagrams, front matter, headings, tables and the Sources sections were compared against HEAD and are unchanged. Checkpoint count is 20 in each chapter, with the original `<details><summary>` form.

Not run: `node tools/check_mermaid.mjs` and `npm run build` (owner asked to skip them).

## What changed (all three)
- Every section keeps its heading. Each opens with a situation (a stalled training job, a BMC that will not boot, a fleet of 1,000 BMCs, a dashboard that stops updating, a PATCH that fails on a busy afternoon).
- The "Prerequisites and outcomes" outcome bullets were rewritten as a plain paragraph of what the chapter walks through. No "you will be able to" lines remain.
- Interview angles and exercises kept their count. Exercises were split so each sentence asks one question. Chapter 06 went from 7 items back to the original 6, and no nested (a)(b) remains.
- First-person residue ("I used it for the lab", "my mock", "I tried PATCH", "I did not run", "correction to my notes") rewritten in teacher voice. "volume 10" removed from reader text and kept in Sources.
- Honest status: status row keeps **untested**. One plain sentence sits above the lab in each chapter. 04: "These steps were not run on a live cluster or a live BMC" (section 5). 05: "None of these steps were run on a live BMC" (section 5). 06: "These steps were run against the mock and DMTF's files, not against a live BMC" (section 8).
- "Mathematical certainty" in 05 section 5.3 was changed to "a strong guarantee that no state change was missed". The original claim was an overstatement.
- Exclamation marks, raw `<` or `{` in prose: none added. Semicolon chains: chain gate 0.0.

## Needs source (general explanations added, not from the original text)
- 04: TLS handshake and OCSP descriptions; X.509 v3 "carries the extra fields modern tools check"; what a CA is; what a cipher suite is; a hotel key card analogy for the session token; the "one-way hash" explanation; TOTP described as a six-digit code that changes over time; "Anything typed on a command line can end up in shell history or the process list".
- 05: ACPI description ("standard power-management message from firmware to the OS"); SPI flash and satellite controller explanation; UEFI POST explanation; "a blocked GET would tie up one of the BMC's few connection slots" (general claim, no number); claim-ticket analogy for 202; the "single most useful idea" paragraph is an explanation of the original point.
- 06: CXL described as "an interconnect standard for memory and accelerators"; PSU expansion in 8.4; `@odata.etag` described as a version label used to skip re-downloads; a hypothetical alert pipeline walkthrough (illustrative, not a real system); the sticky-note analogy for annotations; the "fleet team" story is marked as hypothetical ("Picture a fleet team...").

## Unresolved / for the owner
- Locked text that still carries first-person or residue wording (not changed, per the rules): the heading "### In my lab" (05); the front-matter description "a lab that found real mistakes in my own mock" (06); Sources and review notes lines written as "I read these clauses", "I did not read it page by page", and "Run here" (04, 05, 06).
- The chain gate and guard both pass, but 05 section 2 and 06 section 8.1 are long single paragraphs. A later pass could split them further if the owner wants shorter paragraphs.
- Checkpoint answers were not voice-rewritten (form and count kept, as the rules require).
- The NVIDIA OEM extensions claim in 06 section 7 still needs checking against NVIDIA documents (it was already marked unchecked in the original).
- The 05 chapter's section 4 BCM commands were not run on a BCM cluster (original statement kept in Sources).
