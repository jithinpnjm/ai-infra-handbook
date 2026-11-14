# Voice rewrite ledger: 11.32 NVKE in depth, part 1

File: `docs/part-11-gpu-kubernetes/32-nvke-nvidia-kubernetes-engine-in-depth.md`
Nothing committed. Other chapters untouched.

## Words

| Measure | Before | After | Change |
|---|---|---|---|
| rewrite_guard word count | 6629 | 8879 | +33.9 percent |
| Non-fence words (plain split) | 6726 | 8976 | +33.5 percent |

## Gates

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. Residue 3 to 3.
- Literal backticked-span Counter check, HEAD vs worktree outside fences: lost {} and new {}.
- Code fences: 20 before, 20 after, byte-identical. An early draft had one changed regex line in the error-model block; it was restored before the final gate run.
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words (target 0.2 or lower).
- `node tools/check_mermaid.mjs` over all docs: 776 diagrams, 0 failed (includes this chapter's flowchart).
- Checkpoints: 20 before, 20 after, text verbatim.
- Not run: `npm run build` (excluded by the task).

## What changed

- Front matter, title, heading text and heading order unchanged. Step 6 still precedes Step 5 in section 7, as in the original.
- Outcomes list converted to a plain paragraph. The "After this chapter you can" wording is gone.
- Every section and subsection now opens with a situation or a question from one.
- Added explanation: definitions at first use (neocloud, management system, bare metal, Go workspace, CRD, CNI, CNCF, TPM, SPIFFE and SPIRE, etcd role, outbox, finalizer, leader election, DaemonSet, PodDisruptionBudget, grace period, logical dump, blackbox exporter), walkthroughs of the outbox, the trade-off in each design, and reading guides for tables.
- Kept verbatim: all code, Mermaid, tables, the Sources and review notes section, the Verification log, the checkpoint questions and answers.
- Checkpoint answers were not rewritten. The locked-text rule covers them and rule 10 applies only to Parts 16-18.

## Needs source

These explanations are general Kubernetes or networking knowledge or my reading of the sources. Check before publishing.

- Section 2: "CNCF is the Cloud Native Computing Foundation, the body that hosts Kubernetes" and the sentence on what conformance results show (general background, not from the NVKE sources).
- Section 3.1: the reason an outbox avoids a call to Temporal from the handler (design reasoning, not stated in the source).
- Section 6.1: the statement that desiredCount must be odd so etcd keeps a majority (general etcd background).
- Section 6.1: headroom described as spare room for a node that joins during an upgrade (reading of `max(1, surge)`).
- Section 6.3: the description of what the systemReservedMemory and kubeReservedMemory reservations protect (general kubelet background).
- Section 6.5: DaemonSet example (log collector) is illustrative only.

## Unresolved

- Pre-existing content, not changed: in section 7 the "Step 6" heading appears before "Step 5".
- Pre-existing Exercise 2 answer phrasing kept as in the original.
- EXTERNAL_EDITS.md was not edited, per the task instruction. The HAIKU instructions ask for a line there; that step was skipped on purpose.
- No real build or lab run was performed in this pass; the rewrite did not add any new facts or commands.
