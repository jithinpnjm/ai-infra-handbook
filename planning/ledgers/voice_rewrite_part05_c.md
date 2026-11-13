# Voice rewrite, Part 5 chapters 5.7 to 5.9 (batch c)

Scope: docs/part-05-kubernetes/07, 08, 09. Uncommitted. Gates run with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.7 pods-and-workloads | 16497 | 20700 | +25.5% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.8 life-of-a-pod | 7914 | 10015 | +26.5% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.9 kubelet-and-the-node | 9020 | 11343 | +25.8% | 0 | 0 | 0 | 0.0 per 1000 |

Guard word counts are the tool's measure (body text, code excluded from the prose count), not `wc -w`.
Residue after rewrite: 0 in all three (guard). Exclamation marks in prose: none added (the `!` hits are `!=`, `!key`, `!canary` in code).
Honest status: status row ("labs **untested**") kept, plus one sentence above each lab ("not run on live hardware" wording).

## How the rewrite was done
- Code blocks, tables, Mermaid, front matter, H1, every heading (H2 and H3 text), checkpoint block, Exercises and Sources: kept byte-for-byte from HEAD.
- Prose: the terse drafting paragraphs were rewritten in place where they were voice-poor (5.7 "Why this matters", "Prerequisites", section 1 opening, controller and rollout prose, section 5 contracts, section 7). Elsewhere, explanation paragraphs were inserted after the existing paragraph (situation, analogy, worked walkthrough, the why). No original sentence was deleted except the ones replaced by a rewrite.
- Attribution: inline chapter-number parentheticals in body prose were turned into titles (e.g. "*Kubernetes: Up and Running* introduces ReplicaSets in its chapter on replicated pods"). Headings keep their original text.
- Gem books written in full in all body prose.

## Fixes and wording changes to review
- 5.7 "The book's printed command" became "The printed command in that book" (no "the book" residue wording changed otherwise).
- 5.7 "Let's look at the Deployment history again" kept from original; voice not changed (checkpoint-adjacent prose, review).
- 5.7 benchmark paragraph (new) uses the words "ten percent" as an illustrative example, not a measured fact. Review or remove.
- 5.8 new analogies (relay race, front desk, shift supervisor, dinner party) explain the chapter's existing hand-offs. No new facts.
- 5.9 new analogies (hotel front desk, superintendent, lifeboats, fridge, receptionist probes) explain existing rules. No new facts. One claim to check: "Dynamic kubelet config was removed" (kept from original, see below).

## Needs source (claims present in the original, not re-verified here)
- 5.7 "Kubernetes 1.6 gave DaemonSets a rollout mechanism"; "JDK 8u131 and earlier read the host's memory"; native sidecars "stable in recent releases"; in-place resize "stable in recent releases"; `kubectl run --generator` removal.
- 5.8 "serializeImagePulls is true by default"; the Section 8 metric table keeps the original "`kubelet_start_container_duration_seconds`? (varies)" row, which still has a question mark in the table (garbled original, left verbatim because tables are kept).
- 5.8 Checkpoint 1 (Pending phase wording), Checkpoint 19 (veth interface names), Checkpoint 20 (optimization list tools such as Spegel, Dragonfly, SOCI, eStargz): unverified.
- 5.8 blockquote after Checkpoint 8 about dcgm-exporter 4.9.0 "(2026-11-06)" and metric renames: kept verbatim inside the checkpoint block; needs a source check against 17.4.
- 5.9 "Dynamic kubelet config was removed, so you roll changes out with restarts."; DRA "stable in recent releases"; MemoryQoS status.
- 5.9 Section 7 "older than `minimumContainerTTL`-like behaviour" is garbled in the original and was kept, because the sentence is not a clean fact. Needs rewrite with a source.
- 5.9 Section 8 "40 s in older releases and ... 50 s" (already marked version-dependent in the original's Sources).
- 5.9 Checkpoint 14 "more than 95%" etcd write reduction and the 5,000-node scenario: unsourced.
- 5.9 Checkpoint 2 sysctl list (`kernel.keys.root_maxkeys` etc.), Checkpoint 15 graceful shutdown timing split (90 s / 30 s): unverified here.

## Kept verbatim on purpose (not rewritten)
- Exercises (all three chapters) and Checkpoint questions. Part 5 batch a also kept them. Rule 9 (one question per sentence) and checkpoint answer voice NOT applied; needs a separate pass.
- Sources and review notes (all three) keep "untested here", "not verified", "not run" wording as the rule requires.
- 5.7 Lab steps (list items 1 to 13) kept verbatim; the lab intro paragraphs were rewritten.

## Unresolved
- Exercises and checkpoints voice pass (rule 9, checkpoint answers) not done.
- Claims above marked "Needs source" not checked against sources.
- Not run: npm build, Mermaid check, language_audit, pytest (no code changed).
- No commit made (per rules).
