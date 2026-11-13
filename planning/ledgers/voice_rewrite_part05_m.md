# Voice rewrite, Part 5 chapters 5.34 and 5.35 (batch m)

Scope: docs/part-05-kubernetes/34, 35. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.34 GKE for GPU workloads | 7469 | 10365 | +38.8% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.35 Multicluster and fleet management | 11041 | 14339 | +29.9% | 0 | 0 | 0 | 0.1 per 1000 |

Word counts are the guard's prose count (code blocks removed).

Code spans: 5.34 +3 / -0 (`40 GB`, `37.25 GiB` and similar vendor memory values, kept as spans from the original).
5.35 +9 / -4. The four lost spans are `untested here` (removed on purpose, rule 8), the plain-number spans `10` and `14`
(now written as words in prose, same values), and one `$...$` math artifact. New spans are typed field names
(`generators`, `selector`, `template`, `templates`, `{{name}}`, `{{server}}`) and the `{{...}}` placeholders in the
ApplicationSet explanation.

## Structure kept

- Front matter, title, status tables, every heading (text and order, including "Terraform sketch (untested)"),
  all Mermaid blocks, all code blocks, all data tables (5.34 section 1, 5, 7, 12 tables; 5.35 section 1 driver table,
  section 5 tool comparison, section 10 failure table), checkpoint block (20 entries) and Sources sections. These were
  copied byte-for-byte from HEAD by a splice step, not retyped.
- Lab item count: 9 in each chapter. Exercise count: 6 in each chapter. Interview bullets: 9 in 5.34, 10 in 5.35.
- Honest status once per chapter: status row, plus one sentence above the lab ("were not run on live hardware" in 5.34;
  "were not run on live clusters" in 5.35).

## Rule 9 (exercises and lab)

- Exercises start with a situation line (a teammate asks, a lead asks, a stalled upgrade). One question per sentence
  where possible. Nested (a)(b)(c) in 5.34 exercise 3 and 5.35 exercise 6 rewritten as "the first case / the second case".
- Lab items rewritten as one action per sentence. Item 4 in 5.34 uses "First / Second / Third", not (a)(b)(c).
- `$\approx$` in 5.34 section 7 became "is about". `$N$` and `$8 \times 3 = \mathbf{24}$` in 5.35 became words with the
  same numbers. No `$...$` math left in prose.

## Residue and attribution

- "(untested here)" removed from reader text in 5.35 lab intro. Remaining hits are in the 5.35 Sources section only (kept by rule).
- "The book ..." phrasing replaced by book names in 5.34 (two places) and 5.35 (two places).
- "as I recall it" in 5.35 section 4 replaced with "written from memory of the ApplicationSet syntax". Other "from memory"
  notes in 5.34 (machine and accelerator names) are original and kept, because they are honest verify notes.
- No exclamation marks in prose. No semicolon chains added.
- Gem books in full in reader text: *Kubernetes: Up and Running*, *Generative AI on Kubernetes*. The exercise
  citation "NVIDIA Base Command Manager 11 Containerization Manual" keeps its full title (original text).
  *Production Kubernetes* appears only in the Sources sections (unchanged).

## Unresolved / Needs source

Facts unchanged. New explanatory sentences were added. Each is general background unless noted.

5.34
- Definitions: regional vs zonal cluster; what the system pool runs (DNS, monitoring agents); Workload Identity;
  RDMA; DCGM as NVIDIA's data center GPU manager; Xid and ECC; live migration; DaemonSet and taint as used here.
- "Image streaming starts the container before the whole image has arrived" (feature behaviour). Needs source: GKE image streaming docs.
- "Auto-repair can wipe a three-day training run without a checkpoint" is an illustrative example, not a fact.
- "Choose ANY when you care more about getting nodes at all, BALANCED when you care more about spreading risk" is
  reading of the flag names. Needs source check against `--location-policy` help.
- Original facts carried over and not re-verified: the 25 to 30 second Spot notice (marked verify in the chapter),
  `a3-highgpu-8g`, `nvidia-h100-80gb`, GKE 1.30.1 default driver, `--additional-node-network` repeat limit of 7.

5.35
- Definitions: CNI, namespace, RBAC, node pool, TTL, anycast, BGP, VIP, PoP, PVC, flavor, managedBy, sync wave,
  Flux as a separate controller, OpenID Connect, Cluster Autoscaler behaviour when the management cluster is down
  ("scaling stops") and the Namespace controller example. Needs source check against the Cluster API docs for the
  autoscaling claim.
- Argo CD: "removing the label stops generation; whether resources are removed depends on sync settings." Needs source:
  ApplicationSet docs.
- MultiKueue: "reservations sit idle until losing copies are deleted" and the plain-step walkthrough. Needs source:
  Kueue MultiKueue docs.
- Admission policy audit mode explanation (Kyverno, ValidatingAdmissionPolicy). Standard behaviour; optional source check.
- "The source material returns to this topic in its Chapter 9" (Federating metrics). Needs source: the original text did
  not name the book. Confirm which book and chapter, then name it in full.
- Identity and RBAC paragraphs (Azure AD, Azure Arc, central identity) had the attribution "The authors" in the original.
  Changed to "The guidance here". Needs source: confirm which book they come from, then name it in full.
- Original facts carried over and not re-verified: Kueue v0.9, v0.13, v0.19; batches of up to 3 clusters and 5 minutes;
  commit `1ec0d28`; `/etc/multikueue/kubeconfigs/`; "10 times harder with 10 clusters"; "three active versions";
  "two to three times the mean time to smoke"; replica floor example (8 clusters, 3 replicas, 24 and 10 and 14).
- Walkthroughs added (no new numbers): new-cluster label example, one MultiKueue job in plain steps, a ring rollout
  over a first day, and the network partition case.

## Next steps (not done in this batch)

- Checkpoint blocks in both chapters are verbatim (20 each). A scenario pass (rule 10) is not applied here, because
  Part 5 is outside the Parts 16-18 scenario rule. Decide with the owner whether Part 5 checkpoints get the same pass.
- `npm run build` and `node tools/check_mermaid.mjs` not run. Mermaid blocks are unchanged, so no diff is expected.
- Nothing committed. Owner go-ahead needed.
