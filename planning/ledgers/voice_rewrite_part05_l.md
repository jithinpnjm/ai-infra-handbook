# Voice rewrite, Part 5 chapters 5.31 to 5.33 (batch l)

Scope: docs/part-05-kubernetes/31, 32, 33. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.31 Operators in Go: controller-runtime and kubebuilder | 9672 | 14803 | +53.0% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.32 Project A: GPU node health operator | 6239 | 8666 | +38.9% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.33 Reading the GPU Operator and Network Operator source | 7601 | 9816 | +29.1% | 0 | 0 | 0 | 0.0 per 1000 |

Code spans: 5.31 +32 / -0, 5.32 +11 / -0 (after restoring `>=`, `<` and `time.Sleep`, which first-pass
exercise text had dropped), 5.33 +3 / -0. Word counts are the guard's prose count (code removed).

5.31 is above the 25 to 40 percent band. Nothing was trimmed (rule: never trim). Owner may decide whether the
exercise and checkpoint-adjacent explanations need a second look.

## Structure kept

- Front matter, titles, status rows, heading text and order (5.32 heading "Where this operator fits" kept at H3
  under "The reconciler"; first pass had made it H2 and was fixed).
- All Mermaid blocks, all code blocks, all tables (5.32 decision table, return-value table, budget and failure
  tables; 5.31 hardening table; 5.33 GPU and Network comparison table, debugging table).
- Checkpoint blocks: 20 in each file, appended verbatim from HEAD (not voice-rewritten, as in batches a to k).
  Sources sections verbatim.
- Lab item count: 5 in 5.31 (section 14), 4 in 5.32, 7 in 5.33. Exercise count: 6, 6, 8. Checked against HEAD.
- Requirements in 5.32 and the Prometheus items unchanged in meaning.

## Rule 9 (lab and exercises)

- Lab items and exercises rewritten as short situation-first sentences, one action or question per sentence.
- Each exercise opens with a situation a teammate or reviewer might raise. No nested (a)(b).
- Two-number sentences checked; 5.32 "2–3" and "15 * time.Sleep" kept as typed values.

## Residue and attribution

- "The book's ..." / "The book shows" / "The book notes" removed from reader text. Replaced by the named book.
  Remaining body citations: *Kubernetes Programming with Go* (chapters 9, 10, 11, 12, 13), *Production Kubernetes*
  (chapter 8, 5.31 section 10 and exercise 5 of 5.32 and 5.31 exercise 5). Chapter numbers kept as before.
- "(untested here)" removed from reader text. Remaining hits are in Sources sections only (kept by rule).
- Honest status once per chapter: status row ("**untested**" in 5.31 and 5.33; "**not** tested" in 5.32) plus one
  sentence above the lab ("were not run on a live cluster" / "has not been run").
- Bold reduced to one idea per section (list labels unbolded). The only remaining bold is the "Tip" label in 5.31.
- No exclamation marks in prose. Lab and exercise wording uses no `$...$` math.

## Unresolved / Needs source

5.31
- SIGTERM as the kubelet's stop signal before a kill, and drain-as-graceful-stop wording in section 3 (Kubernetes
  termination docs).
- Lease renewal and takeover explanation in section 3 (leader election docs).
- Infoblox example and companion-controller sentence: the original said "The book's example" and "The book also
  notes". Attributed to *Production Kubernetes* chapter 8 because the chapter already cites that book for the
  same webhook. Confirm the book for the companion-controller sentence.
- AWS IAM Roles for Service Accounts webhook: the original said "The book shows"; the source book is not named.
  Needs source before naming a book.
- "Drift" and "back-dated timestamp" definitions (plain-language explanations).
- Original facts carried over and not re-verified: controller-gen v0.16.5, setup-envtest release-0.19 and 1.31.0,
  `:8080` and `:8081` ports, `unhealthyFor: 2m`, `5,000`-node cache sizing, `Result{RequeueAfter}` table rows,
  `kubectl patch ... finalizers=null`, `IntOrString` example values.

5.32
- "Xid is the error code the NVIDIA driver writes to the kernel log" and ECC definition (NVIDIA XID docs).
- "every GPU waits for the slowest one at each step" in the Why section: general claim, Needs source
  (distributed training docs) if applied strictly.
- Taint behaviour in extension idea 2 (`NoExecute` evicts non-tolerating Pods): Kubernetes taints docs.
- Circuit breaker and smoke-detector analogy: explanation only.
- Original facts carried over and not re-verified: the decision table, `2m` and `5m` defaults, the 3-scenario
  table, the envtest counts ("2 unit-test groups plus 5 envtest scenarios"), `go vet` clean, the
  `platform.example.com/...` annotation keys, `setMin(15 * time.Second)`, the 25 percent and 3 minute
  circuit-breaker example in exercise 6.
- Lab step text "install both operators" and "10-line summary" kept from original.

5.33
- Definitions added at first use (GFD, MIG, RDMA, OFED, hostPath, RHCOS, DCGM, Multus, IPoIB, CNI, NFD PCI
  vendor). Standard meanings; Needs source only if rule 7 is applied strictly.
- "A precompiled driver ... so the node does not compile it on boot" (explanation). Needs source (GPU Operator
  precompiled driver docs).
- "pci-15b3 is the PCI vendor ID for Mellanox" (NFD label meaning). Needs source (NFD docs or PCI ID list).
- "The message 'waiting for nvidia container stack to be setup' ... means the plugin is still in its init loop":
  Needs source check against the init script text.
- Orphan propagation, OnDelete and init-container descriptions: standard Kubernetes behaviour.
- Original facts carried over and not re-verified: commit hashes `0fbefd5` and `041bd87`, clone date 2026-10-24,
  the 45 second and 5 second requeues, `MaxConcurrentReconciles: 1`, `maxParallelUpgrades`, `waitForCompletion`,
  the validator constant names, the `state-*` asset and manifest names, the `pci-10de` and `pci-15b3` label keys.
- Cluster exercises (5.33 lab step 6, 5.32 cluster steps, 5.31 deployment step) not run on live hardware.

## Attribution handling

- Gem book titles in full in reader text. No abbreviations.
- Chapter-number cross references (5.5 to 5.8, 5.14, 5.19, 5.21, 5.22, 5.27, 5.29, 5.30, 5.31, 5.32, Parts 7, 10, 11,
  12, 14, 17) kept.

## Next steps (not done in this batch)

- Checkpoint blocks in all three chapters are verbatim. A scenario-style pass (rule 10) is not applied here, because
  Part 5 is outside the Parts 16-18 scenario rule. Decide with the owner whether Part 5 checkpoints get the same pass.
- `npm run build` and `node tools/check_mermaid.mjs` not run. Mermaid blocks are unchanged, so no diff is expected.
- Not committed. Waiting for the owner's go-ahead.
