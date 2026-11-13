# Voice rewrite ledger: Part 7 chapters 7.10, 7.11, 7.12 (batch d)

Base: HEAD (Part 7 chapters 01-09 are edited by another agent; not touched here). Only the three chapter files were edited. Nothing committed. EXTERNAL_EDITS.md not touched (per run instruction).

## Word counts (`wc -w` on the whole file, front matter included)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 10-firmware-inventory-and-the-updateservice.md | 6097 | 7919 | +29.9% |
| 11-log-services-event-logs-and-diagnostics.md | 6301 | 8218 | +30.4% |
| 12-automating-redfish-with-python-ansible-and-go.md | 5908 | 7589 | +28.5% |

## Gates (run by hand, output below)

rewrite_guard.py HEAD WORKTREE (final run per file):
- 10: `ok ... words 5693->7515 new numbers 0 lost numbers 0 new code spans 2 lost 0 residue 0->0`
- 11: `ok ... words 5840->7757 new numbers 1 lost numbers 0 new code spans 5 lost 1 residue 4->1`
- 12: `ok ... words 5537->7218 new numbers 1 lost numbers 0 new code spans 9 lost 0 residue 3->0`
- Hard failures: 0 on all three.

Guard word column counts prose only, so it differs from `wc -w`. The growth figure above uses `wc -w`.

Number check (set comparison, the guard count has pairing artifacts):
- 10: no lost numbers. The `nvfwupd` span lost in the first pass was restored in section 7.
- 11: new numbers are `7.10` (cross-reference to chapter 7.10 added in section 3), `0/200` (copied from the mock output), `403` (already in the chapter, now also in the lab walkthrough sentence). Lost number `10` is the removed body reference "volume 10, scenario 4" (residue, deliberate). Checkpoint 20 and Sources still carry `volume-10` (locked).
- 12: new numbers are section and rule references (`2.3`, rule `7`) and status codes already in the chapter (`401`, `403`, `404`, `502`, `503`, `504`, `201`, `202`). No new data values.

Span check (set comparison): no lost spans on any of the three files. `session_login.x_auth_token` was briefly lost in chapter 12 and was restored.

chain_gate.py: 10 = 0.0, 11 = 0.0, 12 = 0.3 (one hit, a semicolon chain inside the locked Sources section of 7.12). All at or below the 0.2 target except 12, which is locked text.

Code and locked parts: code blocks, Mermaid, `<details>` checkpoint blocks and Sources sections were compared against HEAD and are byte-identical. Front matter and all headings are identical.

Build and Mermaid: NOT run in this batch (per run instruction, no npm build and no full Mermaid).

## Residue removed

- First-person lab claims ("I checked", "My tool", "My lab confirms", "I have not run this", "I did not run either one", "I tested version 3.4.2", "I installed", "I added TLS to the mock", "The client I used") removed from reader text. Headings with the same wording were left as-is because headings are locked; see "Unresolved".
- "Volume N" body references removed in 7.11 (the NVIDIA-DevOps notes are still named in Sources).
- "(untested here)" repetition removed. Honest status kept once per chapter: status row plus one sentence above the lab (10: "The 46 checks pass against the mock. They have not been run against a live BMC..."; 11: lab sentence; 12: "The results below are from the mock only...").
- Exclamation mark removed in 7.12 section 6.1 ("locks the service account out...!").
- Outcomes-style lines ("you will be able to", "When you finish, you can") rewritten as plain paragraphs in all three chapters.

## Needs source

- None added as new facts. Explanations added for terms (BIOS, BMC, CA, TLS, NTP, IPMI, SEL, KMS, FRU, SXM, OpenBMC, RTC, ECC, DMTF) are general definitions, not chapter claims.
- 10 section 4: the Update message registry is described as "a standard list ... that the DMTF defines for all Redfish services". This follows the locked Sources (DSP2046 registries).

## Unresolved

- Headings still contain first-person wording because headings are locked: "### 2.1 The client I used in all labs" (7.12). Left as-is.
- Exercise count in 7.11 says "confirm that `22` / `23` checks pass", but the lab prints "23 passed, 0 failed". Original fact kept unchanged; the owner should decide which number is right.
- 7.12 chain gate hit 0.3 comes from a locked Sources line. Not changed.
- 7.12 Sources and 7.11 Sources still say "I read" / "I did not run" in locked text. Left unchanged per locked-section rule; owner may want those reworded in a Sources pass.
- Checkpoint 20 in 7.11 still says `volume-10/01` (locked).
- Mid-run file changes: none detected on the three chapter files. Other Part 7 chapters (07, 08, 09) and ledgers a, b, c show modifications from another agent; not touched by this run.
