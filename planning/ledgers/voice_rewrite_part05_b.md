# Voice rewrite, Part 5 chapters 5.4 to 5.6 (batch b)

Scope: docs/part-05-kubernetes/04, 05, 06. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.4 kubeadm lab | 10809 | 13813 | +27.8% | 0 | 1 (`5.6`, cross-reference to the controllers chapter) | 0 | 0.1 per 1000 |
| 5.5 API server and etcd | 10315 | 12999 | +26.0% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.6 controllers and reconcile loop | 8139 | 10229 | +25.7% | 0 | 0 | 0 | 0.0 per 1000 |

Word counts are the guard's count (code fences are not removed from the count). Gate results: all three pass
(`chain_gate` exit 0, guard 0 hard failures).

## Method

- Whole-file rewrite per chapter (Write), not per-section Edit. Front matter, headings and heading order,
  every fenced code block (including Mermaid and the etcd output samples), every data table, the checkpoint
  block (20 `<details>` entries, verbatim) and the Sources section are carried over unchanged.
- Growth comes from situations at the start of sections, analogies, worked walkthroughs (5.5: a
  `kubectl scale` request traced through the pipeline; 5.5: a 409 conflict between two engineers; 5.6: a
  pod death traced through the informer and work queue; 5.6: GPU remediation walk-through), and "why" sentences.
- Inline code spans were checked against HEAD. Restored the typed spans lost in exercises (5.4: `podSubnet`,
  `serviceSubnet`, the phase arrow chain, `cp1..cp3`, `kubectl logs/exec`). Remaining new spans are the
  commands and flags added in prose (`kubectl scale`, `--replicas=<n>`, `kubectl proxy`, `curl`, `EP`).
- Exercises (5.4 end, 5.5 end, 5.6 end) rewritten: one situation and one question per item, nested
  (a)(b)(c) removed from 5.4 exercise 6 and 5.6 exercise 6, commands and numbers unchanged.
- Exclamation marks: none in prose (the one `#!/bin/bash` in 5.5 is code).
- Honest status: status row plus one sentence in the body per chapter. 5.4 section 2
  ("not verified on live hardware"), 5.5 section 10 ("were not run on live hardware"), 5.6 section 8
  ("not run as part of this chapter"). Inline "(`untested here`)" removed from body prose in 5.6 (the
  exercise intro). The Sources sections still contain "untested here" lists, which stay per the rules.
- Gem book titles kept in full (Kubernetes: Up and Running, Production Kubernetes, Programming Kubernetes,
  Kubernetes Programming with Go). No abbreviations.
- Chapter-number cross references in body prose kept (5.3, 5.5, 5.16 and so on). Only one new one added
  (5.4 section 10 "Chapter 5.6 explains ...").

## Not changed (kept verbatim as facts or code)

- Checkpoint questions and answers, all three chapters, verbatim (form and count unchanged). Checkpoint answers
  NOT voice-rewritten, same as batch a. Rule 9 (one question per sentence) was applied to exercises only.
- Lab step lists in 5.5 section 10 (13 items) and 5.6 section 8 (13 items) kept as written; only the honest
  sentence above each list was adjusted.

## Needs source / fact checks (flagged, not changed)

5.4 kubeadm lab
- Checkpoint 9 and exercise 5 use `kubectl apply -f myobj.yaml view-last-applied` (argument order). Verify
  the CLI form: the subcommand may need to come before `-f`. Same in the "Everyday kubectl" block, which is code and kept.
- "kubectl get --raw", "kind get kubeconfig-path" (in the Start-on-a-laptop block, code, kept): the `kind`
  subcommand may be removed in current releases. Needs source check.
- Section 1: "The skew policy allows kubelet to be up to 3 minor versions older" (and kubectl ±1). Check
  against the current version skew policy.
- Section 7 / checkpoint 20: the `etcdctl member remove` then re-add order is correct for quorum, but the
  older `ClusterStatus` cleanup note in checkpoint 20 is version-specific. Needs source.
- kube-vip note "on kubeadm 1.29+ needs the super-admin.conf workaround" (section 7): Needs source.
- Pod CIDR "A /16 gives 256 nodes of /24" is arithmetic, correct.
- Section 2 bridge note: "By default, the kernel does not send bridged traffic through the iptables rules" is
  the usual `bridge-nf-call-iptables` default, not checked against the kernel version used in the lab.

5.5 API server and etcd
- Checkpoint 9: "fails on objects over 256 KiB" for client-side apply. Needs source (last-applied annotation
  size limit).
- Checkpoint 17: "`--etcd-servers-overrides=/events#https://etcd-events:2379`" is the form in the
  chapter text; the events override takes the form `/events#<servers>` as written. Needs a live check.
- Section 5 / checkpoint 16: `k8s:enc:kms:v2:` prefix and the `etcdctl get` path. Verify against a live cluster.
- Section 7 restore block: the `etcdutl snapshot restore` flags are a sketch from the chapter. Needs a
  live test before use.

5.6 controllers and reconcile loop
- Checkpoint 17: `workqueue_retries_total` is labelled as `controller_runtime_reconcile_errors_total`, and
  `workqueue_work_duration_seconds_bucket` as `controller_runtime_reconcile_time_seconds`. These are not the
  same metrics. Needs a fact fix (checkpoint kept verbatim).
- Checkpoint 7: the order listed for ReplicaSet scale-down puts `pod-deletion-cost` second. The upstream
  ranking order differs (pod phase, readiness, deletion cost, co-location, ready time). Needs source before any
  reader relies on it.
- Section 3 and checkpoint 9: "`node.kubernetes.io/out-of-service=nodeshutdown:NoExecute`" as the fencing taint
  is version-specific. Needs source.
- Section 5 leader election defaults (15 s / 10 s / 2 s) match client-go defaults. Verify against the
  controller-manager version used in the lab.

## Unresolved

- Owner-approval step: none of the three chapters is committed (rule: do not commit without go-ahead).
- Parts 5.1 to 5.3 are batch a (`voice_rewrite_part05_a.md`). Not touched here.
- Checkpoint answers and the Sources sections were not voice-rewritten (verbatim by rule).
