# Voice rewrite, Part 5 chapters 5.25 to 5.27 (batch j)

Scope: docs/part-05-kubernetes/25, 26, 27. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.25 troubleshooting from the node | 7656 | 10135 | +32.4% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.26 how Kubernetes uses the Linux kernel | 9926 | 12520 | +26.1% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.27 software supply chain security | 10807 | 13898 | +28.6% | 0 | 0 | 0 | 0.0 per 1000 |

Word counts are the guard's prose count (code blocks removed). Code spans: 5.25 and 5.27 lost none. 5.26 lost only
`untested here` in the lab intro, which is intended (replaced by "were not run on a live node").

## Structure kept

- Front matter, title, status tables, heading text and order, all Mermaid blocks, all code blocks (including the
  sysctl `text` block in 5.26 and the Tekton and Kyverno YAML in 5.27), all data tables (5.25 4.10 GPU table, 5.26
  master map, controller table, observability and failure-mode tables, 5.27 maturity table).
- Checkpoint block: 20 entries, appended verbatim from HEAD (not voice-rewritten). Sources sections verbatim.
- Lab item count: 13 in each chapter (5.25, 5.26, 5.27). Exercise count: 6 in each chapter.
  Counts were checked against HEAD after a first draft had split items; the split was reverted.
- Status row unchanged ("labs **untested**"). One honest sentence above each lab: "were not run on live hardware"
  (5.25 section 7, 5.27 section 12) or "were not run on a live node" (5.26 section 12).

## Rule 9 (exercises and lab)

- Lab items and exercises rewritten: one action or one situation per sentence, at most two numbers per sentence.
- 5.26 exercise 2 math `$\ge 5.12$` and `$\ge 5.19$` converted to "kernel 5.12 or later" and "5.19 or later" (same numbers).
- Exercises start with a situation line in each chapter. Lab items for 5.27 item 1 "Scan and SBOM" keep their original asks.

## Residue and attribution

- "(untested here)" removed from reader text in all three. Remaining hits are in Sources sections only (kept by rule).
- Body-prose chapter citations to *Production Kubernetes* ("Chapter 15") removed in 5.27 body text; cross-references
  to 4.x, 5.x chapters kept. Exercises and Sources keep their citations.
- No exclamation marks in prose. No `$...$` math in prose after conversion.
- Chain gate: no "; the/every/each/a/an" chains added.

## Unresolved / Needs source

Facts unchanged, but new explanatory sentences were added that go beyond the original text. Each is general
background, not a chapter-specific number. Check before publication:

5.25
- "A signal ... SIGKILL is the one a process cannot catch or ignore" (definition, standard Linux behaviour).
- Pending-pod example and `ContainerCreating` restaurant analogy: explanation only.

5.26
- "An application that never registers a handler for SIGTERM ... the kubelet then has to wait out the grace period
  before it escalates" (escalation to SIGKILL after grace period: Needs source, kubelet docs).
- "EEVDF ... replaced it in later kernels" (wording only; the original said "EEVDF from 6.6").
- DKMS rebuilds the module on each kernel change; ECN/DCQCN/PFC one-line definitions. Needs source (RoCE docs, Part 12).
- Hard vs soft NFS mount behaviour: "A hard mount keeps retrying until the server answers" (standard NFS, Needs source).
- Discard explanation in 5.26 section 5 ("Discard tells an SSD which blocks are free ...") is an added general definition. Needs source check against the block-layer docs.
- Original facts carried over unchanged and not re-verified (noted in the prior batches): idmapped mount versions
  (5.12, 5.19), `memory.oom.group` 4.19, PSI 4.20, io_uring 5.1, EEVDF 6.6, netkit 6.7, BIG TCP 5.19,
  `vm.max_map_count` 262144, the sysctl values in the `text` block, `kernel.keys.*` values in checkpoint 16.
- Checkpoint 1 keeps the original escaped `\"Container\"` quotes (verbatim by rule). Clean up in a later pass.

5.27
- EPSS and CISA KEV one-line definitions; VEX definition; TUF definition; C2PA one-line definition; LoRA adapter
  definition; honeytoken definition; fail-open and fail-closed definitions. Standard meanings, Needs source only if
  rule 7 is applied strictly.
- "Preferring wheels stops pip from running setup.py" (standard pip behaviour, Needs source: pip docs).
- Notary v2 wording changed from "At the time of the source" to "was then in development" (dates not added).
- Original facts carried over and not re-verified: `docker buildx build --provenance=mode=max --sbom=true`,
  `cosign` command flags, `torch.load` default change "before version 2.6", the Kyverno policy fields,
  `nvidia` bulletin list, the "1 hour" log4shell drill, SLA hours/days wording, `gcr.io/distroless/base` tag.
- Kyverno YAML keeps `\\.` escapes and the `registry.example.com` placeholders as in the original.

## Attribution handling

- Gem books: full titles in reader text (*Production Kubernetes*). No abbreviations.
- Chapter-number cross references (4.1, 4.2, 4.13, 5.1, 5.2, 5.8, 5.9, 5.10, 5.15, 5.16, 5.17, 5.21, 5.24, Part 12,
  Part 17) kept in body text, as in the batch a/f rules.
- Exercises and Sources keep "Chapter 4" and "chapters 2 to 5" style citations.

## Next steps (not done in this batch)

- Checkpoint blocks in all three chapters are verbatim. A scenario-style pass (rule 10) is not applied here, because
  Part 5 is outside the Parts 16-18 scenario rule. Decide with the owner whether Part 5 checkpoints get the same pass.
- `npm run build` and `node tools/check_mermaid.mjs` not run. Mermaid blocks are unchanged, so no diff is expected.
