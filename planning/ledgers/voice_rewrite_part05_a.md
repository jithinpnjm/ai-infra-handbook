# Voice rewrite, Part 5 chapters 5.1 to 5.3 (batch a)

Scope: docs/part-05-kubernetes/01, 02, 03. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.1 containers-from-first-principles | 11746 | 14951 | +27.3% | 0 | 0 | 0 | 0.1 per 1000 |
| 5.2 container-runtimes | 9570 | 12105 | +26.5% | 0 | 1 (`5.21`, cross-reference to Pod Security Standards chapter) | 0 | 0.0 per 1000 |
| 5.3 kubernetes-architecture | 10240 | 12901 | +26.0% | 0 | 0 | 0 | 0.1 per 1000 |

Residue after rewrite: 0 in all three (guard). Exclamation marks in prose: removed (one in a 5.1 table cell, "CUDA!").
Honest-status: status row ("labs **untested**") plus one sentence above each lab ("not run against live hardware").
Sources sections unchanged; they still contain "untested here" / "not verified" lists, which the rule keeps.

## Structure kept
- Front matter, title, status tables, heading text and order, Mermaid blocks, every code block, every data table, checkpoint block (count 20, `<details>` form and questions), Sources section.
- Checkpoint and exercise text kept verbatim in all three chapters (form and count). Rule 9 (exercise sentence length) NOT applied; checkpoint answers NOT voice-rewritten.

## Fact fixes made during rewrite (review these)
- 5.2 "Kubernetes supports Docker, but its use is discouraged" replaced with "Kubernetes once supported Docker directly, and that support is gone from the project itself" (dockershim removed in 1.24, matches section 2 of the same chapter).
- 5.2 "Most GPU training clusters use runc or crun with strong pod security policy" replaced with "Pod Security Standards enforced (5.21)" (Pod Security Policies removed in K8s 1.25; ledger fix 2026-11-11).
- 5.3 kubelet example "such as Docker" changed to "such as containerd or CRI-O"; "Docker still runs in many clusters" changed to "Today most clusters run containerd or CRI-O" (consistent with 5.2).
- 5.3 `$\pm 1$`, `$2$–$3$`, `$1$` math in body converted to plain words (same numbers). Checkpoint 4 keeps its `$\lfloor N/2 \rfloor + 1$` math because checkpoints stay verbatim. Decide whether to convert it.
- 5.1 CFS wording changed from "the kernel's default CPU scheduler" to "the kernel's CPU scheduler that enforces the quota" (default scheduler has changed across kernel versions; not checked here).

## Unresolved / Needs source
- 5.1 section 6 walkthrough: "The toolkit's hook runs before the container's main process starts." Needs source (prestart hook timing; check NVIDIA Container Toolkit docs).
- 5.1 section 1: "`--cpu-shares` default 1024 corresponds to Kubernetes `resources.requests.cpu`" is original text, not re-verified.
- 5.2 added sentence "Newer releases use the newer API version, but the order of calls is the same." Needs source (check CRI v1 call order).
- 5.2 walkthrough still pinned to Kubernetes v1.18.2 and containerd v1.3.4 (original; stale versions, not updated, no new facts added).
- 5.2 checkpoints 6 (cgroupfs path `/sys/fs/cgroup/k8s.io/...`) and 17 (PLEG 3-minute threshold) are verbatim and unverified.
- 5.3 added claim: "By default, most pods get that toleration added for them" (default `node.kubernetes.io/*` toleration admission). Needs a quick source check.
- 5.3 added claim: conntrack table full "drops new connections" (general behavior, not sourced).
- 5.3 illustrative example (7 of 8 workers waiting under gang scheduling) is an explanation, not a measured fact.
- 5.3 headings "Why Kubernetes Exists ... (Chapter 1)" and "Inspecting Nodes ... (Chapter 3)" kept verbatim because headings must not change. Consider a heading-level decision later.
- Exercises (all three chapters) and checkpoints kept verbatim; a separate pass is needed for rule 9 (one question per sentence, max two numbers per sentence) and for checkpoint answer voice.

## Attribution handling
- Inline chapter-number parentheticals removed from body prose in 5.1 (OCI paragraph, lab paragraph), 5.2 (Production Kubernetes author names removed from body prose) and 5.3 (book intro paragraphs). Full gem-book titles kept in prose. Chapter parentheticals remain in headings, checkpoints, exercises and Sources, as intended.
- Gem-book titles were never abbreviated.
