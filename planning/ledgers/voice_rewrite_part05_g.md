# Voice rewrite, Part 5 chapters 5.19 to 5.21 (batch g)

Scope: docs/part-05-kubernetes/19, 20, 21. Uncommitted. Gates run with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Method: prose sections, lab steps and exercises rewritten. Front matter, headings, tables, code blocks,
Mermaid, checkpoint blocks (verbatim) and Sources sections were copied unchanged.

## Status

| Chapter | Status | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|---|
| 5.19 deployment models and day-2 | done | 10815 | 13299 | +23.0% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.20 upgrades, etcd, DR | done | 11037 | 13566 | +22.9% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.21 certificates, identity, policy | NOT STARTED | 15463 (file) | unchanged | 0% | not run | - | - | not run |

Growth is under the +25 to +40 target for 5.19 and 5.20. Both are close; a further paragraph each would clear it.

## 5.21: not started

The file was read in part (lines 1 to 262) and then left untouched, because the context budget for this run was used up.
Start 5.21 in a fresh run. Read the whole file in chunks first, including the lab and exercises at the end.
Rules that must hold (from the batch notes): OIDC `.well-known` and JWKS served by the API server since 1.21, with AWS needing a
public copy (ledger R9); PodSecurityPolicy removed in 1.25; `amicontained:v0.4.9`; checkpoints verbatim.
No file changes were made to 5.21.

## 5.19 notes

- Reader text: "(untested here)" appears only in the Sources section (kept, as the rule requires for Sources).
  Honest status kept: status row ("labs **untested**") and one sentence above the lab ("were not run on live hardware").
- Lab: 12 steps kept (same commands, same count). Exercises: 6 kept, rewritten to one question per sentence.
- Checkpoints verbatim (count 20). Checkpoint answer voice NOT rewritten, as in batches a to e.
- Bold: several bold terms remain in section 1 and 3 (pre-existing); not reduced.
- Added explanation (general, not sourced; "Needs source" only if the owner wants citations):
  PDB meaning, golden image meaning, quorum loss meaning, checkpoint meaning, stranded-resource meaning, the office-building
  analogy for cluster topology, the "fire crew" dispatcher analogy, and the cashier-versus-experiment contrast for drains.
- Original "Needs source" items still open (not touched): "180 Kubernetes Certified Service Providers" (CNCF count);
  "5k node limit"; checkpoint 19 "3 to 7 days" RMA turnaround and "within 2 minutes" job recovery (no source in the chapter);
  checkpoint 5 and 17 runbook timings; `--grace-period=600 --timeout=30m` as a recommended value.

## 5.20 notes

- Initial read missed exercises 7 to 9 (below line 461). They were found on the guard code-span diff and restored, rewritten.
  Guard result above is after the restore.
- Reader text: "(untested here)" is absent. Honest status kept: status row and "have not been run against live hardware" sentence above the lab.
- Lab: 14 steps kept. Exercises: 9 kept (7 to 9 restored).
- Checkpoints verbatim (count 20). Sources verbatim.
- Worked examples added: the rewind story (replica counts and a ConfigMap, no digits), the restore drill guard list,
  the three-alert triage example, and the rehearsal expectation-versus-result habit.
- Inconsistencies in the ORIGINAL text, left as written (owner to decide, facts not changed):
  - Exercise 8 names the Velero schedule `nightly-platform`, but the code block creates `nightly`.
  - Exercise 9 says "the eight scenarios in Section 8", but the Section 8 table has 11 rows.
  - Section 2 says "Four strategies cover most platform upgrades" and then "Three strategies cover most platform upgrades"
    in section 2 detail. Both kept.
  - Section 3 uses a 1.30 to 1.31 template, with `1.31.x` package pins.
- Added general-explanation claims (not sourced, check if the owner wants citations): etcd learner meaning
  (receives data, does not vote until caught up), MVCC meaning, the cloud-disk snapshot consistency caveat
  (disk-level, may catch etcd mid-write), KEP meaning, informer relist after resource-version reset.
- Original "Needs source" items still open: "10 to 15 minutes" learner replacement window (Production Kubernetes, Chapter 2
  wording), "5 to 10 minutes" per control-plane node, "15 to 60 minutes" snapshot interval, "hundreds of MB to a few GB".
- `bcm11-containerization` Appendix C reference kept (it is a document name, not a gem book).

## Process note

Chapter 5.20 was partly read in the first pass, and a whole exercise block was missed. Check line counts against the
last read line before you rewrite a long chapter.
