# Voice rewrite, Part 5 chapters 5.16 to 5.18 (batch f)

Scope: docs/part-05-kubernetes/16, 17, 18. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.16 configuration, secrets and RBAC | 14643 | 18886 | +29.0% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.17 storage internals | 10543 | 13425 | +27.3% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.18 scheduling in depth | 9454 | 11893 | +25.8% | 0 | 0 | 0 | 0.0 per 1000 |

Guard detail: 5.16 lost 0 code spans, 5.17 lost 0, 5.18 guard reports "lost 3" code spans. A direct count
of backtick spans shows only one removal, `untested here` in the 5.18 lab intro, which is intended (replaced
by the honest sentence). The other two are artifacts of the guard's counting. 5.18 "new numbers" was 1
(63, a derived count I introduced in an analogy) and was removed before the final run.

## Method

- Edits were section-by-section in place (Edit), not whole-file writes. Code blocks, Mermaid, tables,
  front matter, heading text and order, checkpoint block (20 entries, verbatim) and Sources sections
  are unchanged.
- Growth: a real situation opens most sections, followed by analogies (keycards, sticky note, seating
  planner, staff badge, admissions office, film crews, lanes on a highway), worked walkthroughs (5.16 the
  three-door ConfigMap spec and the `kubectl replace` pipeline; 5.17 the StorageClass field by field and the
  node-log sequence; 5.18 the affinity block read from the outside in, and one pod traced through the
  scheduling cycle) and "why" sentences.
- Exercises rewritten per rule 9 in all three chapters (6 exercises each, same count, same asks, same code
  spans). Each item is one situation line followed by one question per sentence. No nested (a)(b).
  Checkpoints were NOT rewritten (verbatim, form and count kept), so rule 10 scenario style is not applied.
- "The book" / "the book's" residue in reader text replaced with the full gem-book title (*Production
  Kubernetes*) or with neutral wording (5.16 sections 2 to 5, Vault, OIDC, CSR, Dex and Gangway lines).
- Inline code spans: typed commands and flags kept. 5.16 exercise 6 keeps `get/list/watch`.
- Exclamation marks: none in prose (5.16 has one inside a code block, `echo Hello Kubernetes!`, kept).
- Honest status: status row plus one sentence above each lab, "were not run on live hardware" (5.16 section 8,
  5.17 section 7, 5.18 section 10). Interactive lab steps no longer say "untested here" in reader text.

## Kept on purpose (not changed)

- "(untested here)" comments inside code blocks (5.16 Vault `vault` CLI snippet, three to four comments).
  Code blocks must not change under the guard. Sources sections also keep their "untested here" lists.
- 5.18 dcgm-exporter 4.9.0 version note (line in the exercises area, links to 17.4). It reads like a dated
  drafting note. Kept verbatim because it is a fact-bearing note. Owner to decide whether it stays in the
  reader text or moves to the Verification log.
- 5.17 "When this material was written" note and the AWS price row ("as recorded when this material was
  written"). Kept verbatim. Needs a dated source check before a future price review.
- 5.18 "At the time of writing" warning on `--policy-config-file` and `--policy-configmap`. Kept.

## Unresolved / Needs source

5.16 Configuration, secrets and RBAC
- Duplicate heading: "## 6. Configuration management patterns for AI workloads" appears twice in a row in the
  source (HEAD). Heading order and text must not change under the rules, so both were kept. Owner decision:
  delete one heading in a later structural pass.
- `optional: true` wording in the three-door walkthrough explains the field as "handled gently instead of
  stopping the start." This is the field's meaning; no new fact. Mark as "check against the ConfigMap key
  reference" if rule 7 is strict.
- Existing facts carried over and not re-verified: "Since 1.22+", "~1 MiB" limit, "1 to 2 minutes" kubelet
  sync, "every 30 days" sealed-secret key renewal, `kubectl create token` durations, `vault:1.3.2`.
- Checkpoint answers carry facts not re-verified in this pass, for example the kubelet rotating the bound
  token at 80% of its lifetime (checkpoint 7). Left verbatim by rule.

5.17 Storage internals
- Explanation added, not a fact: "A driver that runs on the controller but never appears on a node cannot
  mount anything." Consistent with the chapter's own CSINode section; no source check needed beyond that.
- Explanation added: a node missing from `CSINode` is "a node where pods will fail to mount." Judgement,
  consistent with the troubleshooting table. Optional source check.
- Exercises still cite *Production Kubernetes* Chapter 4 (attribution inside exercises is kept).
- Pre-existing claims not re-verified: `maxWaitForUnmountDuration` 6 minutes, XFS inode behaviour, the
  `fsGroupChangePolicy` and `seLinuxChangePolicy` field names, AWS EBS attach caps of 16, 28 or 128.

5.18 Scheduling in depth
- Explanation added: "a judge with weight 5 counts five times as much as a judge with weight 1." This is the
  weighted-sum rule; no new fact.
- Explanation added: a shorter `tolerationSeconds` "can move a pod that would have recovered on its own."
  Judgement. Optional source check against the taint-based eviction docs.
- Exercises 1 to 6 reworded to one situation and one question per sentence. Exercise 6 keeps the
  `FailedScheduling` span.
- Pre-existing claims not re-verified: `podMaxInUnschedulablePodsDuration` 5 min, backoff 10 s, scheduler
  queue names, Kueue `v1beta2` manifests (Sources says checked 2026-11-11).

## Attribution

- Gem books use full titles in reader text: *Production Kubernetes*, *Kubernetes: Up and Running*.
  No abbreviations.
- Chapter-number cross references (5.12, 5.22, 4.26, Part 13, Part 17) kept.
