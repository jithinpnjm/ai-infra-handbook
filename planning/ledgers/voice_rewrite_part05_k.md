# Voice rewrite, Part 5 chapters 5.28, 5.29, 5.30 (batch k)

Scope: docs/part-05-kubernetes/28-service-mesh.md, 29-extending-kubernetes-crds-and-operators.md, 30-go-for-kubernetes-engineers.md. Uncommitted.
Gates: `python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before (wc) | Words after (wc) | Growth (wc) | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.28 service mesh | 10745 | 13570 | +26.3% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.29 extending Kubernetes: CRDs and operators | 12685 | 16017 | +26.3% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.30 Go for Kubernetes engineers | 9449 | 13703 | +45.0% | 0 | 0 | 0 | 0.0 per 1000 |

Guard prose-only counts: 5.28 10107 to 12932 (+28%), 5.29 11840 to 15172 (+28%), 5.30 7588 to 11842 (+56%).
5.30 is above the +25 to +40 aim. The growth is explanation of Go concepts for a learner (what a struct, an interface, a channel, a context, a Lease and a work queue are, with a walkthrough per example). Nothing was trimmed. Owner may want to trim the Go section, but that is the owner's call.

Code spans: 5.28 +7 / -0 (typed field names, `version: v2`, `stat`, `top`, `edge`, `metrics`, `resource`); 5.29 +6 / -0; 5.30 +31 / -0. Lost spans restored (see Method). Guard reports 5.28 "lost 1" as a parsing artefact of an unbalanced backtick in the original Linkerd sentence; the same span text is present in the new file.

## Structure (checked)

- Front matter, title, status table, every heading (same text, same order), 6 numbered headings in 5.30 kept as in HEAD.
- Every code block and Mermaid block copied byte for byte from HEAD (via `@@COPY` line ranges, see Method). Guard reports 0 code-block failures.
- Data tables (5.28 data-plane table; 5.29 extension-points, capability-level, operator-choice, verb and AI-operator tables; 5.30 quantity, RESTMapper and idioms tables) copied from HEAD.
- Checkpoint block: 20 `<details>` blocks in each file, copied verbatim from HEAD. Checkpoint answers not voice-rewritten (as in batches a to j).
- Sources and review notes copied verbatim from HEAD.
- Honest status: status row ("labs **untested**") plus one sentence above the lab in each chapter. 5.30 also keeps the compile-and-test status sentence in section 6, reworded to show the tests that passed (the "not run" sentence is kept only above the lab).
- Exclamation marks in prose: none. "!" only in `!=` in code.
- "(untested here)" and "the book" residue: none in reader text. 5.28 "The book" residue (one sentence) rewritten as the chapter title, which the guard counted as residue 1 to 0.
- Gem book titles kept in full. Author names removed from body prose in all three chapters (they remain in Sources). 5.30 "Network Programmability and Automation, Chapter 7, by ... et al." changed to title and chapter only.

## Method

- Each chapter was rewritten section by section into scratchpad parts. Code, tables, checkpoints and Sources were pulled from the HEAD copy by line range, so they cannot drift.
- Each section opens with a situation (a model server with a canary, a pod that will not stop, a GPU health policy, a node cordon, a probe over a cluster) and then the mechanism.
- Added: analogies (postal service, hospital corridor, apartment and building guards, kitchen bell vs cook walking to the pass, airport checkpoints, crate for packaging, locked room key, filing-system migration, subscription, private drawer for `internal/`, notebook for informers, inbox for work queues), worked walkthroughs (5.28 Istio route and sidecar memory arithmetic; 5.29 a rejected `deploymentTier: qa` and a defaulted replica count, the finalizer for three cordoned nodes, one WebApp reconcile pass, the four-step CRD upgrade; 5.30 cordon CLI flags, the classifier and fake-clientset tests, the two Dockerfile stages).
- Lab steps and exercises rewritten per rule 9. Same counts: 5.28 13 lab steps and 9 exercises; 5.29 13 lab steps and 6 exercises; 5.30 12 lab steps and 10 exercises. Commands and file names unchanged. Dense sentences split (5.28 lab step 4 had three numbers in one sentence; fixed).
- Inline code spans: a few exercise and prose names had been unwrapped on the first pass and were restored (`go build/test/vet/fmt/mod`, `errors.Is/As`, `panic/recover`, `reflect.Type`, `Filter/Map/GroupBy`, `go test`, `Sidecar`, `python3 code/part05/service_mesh_policy_sim_lab.py`).
- A checkpoint heading was duplicated twice during assembly (once in the rewritten part, once in the copied block). Both were fixed. Checked with grep: one heading per file.

## Kept on purpose

- 5.28 fact-fixes from the earlier pass kept: `istiod` merged in 1.5, Pilot/Citadel/Galley named as the older components, the three-question adoption list, the `DestinationRule`-before-route ordering note, and the Sources wording.
- 5.28 original statements kept, not re-verified: Envoy default route timeout 15 s, stream idle timeout 5 minutes, Linkerd proxy 10 to 20 MiB, Envoy sidecar 50 to 100+ MiB, 0.2 to 1 ms per hop, `holdApplicationUntilProxyStarts` and `EXIT_ON_ZERO_ACTIVE_CONNECTIONS` behaviour.
- 5.29 "about 1.5 MiB" etcd object limit, the five capability levels, the operator-term date (November 2016) and the Brandon Phillips attribution. All original.
- 5.30 checkpoint 20 numbers (about 30% binary shrink, about 2 MB distroless) kept as checkpoint text, not checked.

## Needs source (explanation added; not checked against docs)

5.28
- "A revision is a second control plane that runs next to the first" (Istio revisions). General explanation. Check the Istio revision docs.
- "The kubelet sits outside the mesh, so it cannot present an identity" (health-check explanation). Judgement, check against Istio probe-rewrite docs.
- Locality-aware routing "saves time and cross-zone cost" and long-lived connections "stay pinned to one replica". General reasoning; no number.
- Protocol-sniffing explanation (server-first protocols wait for the client). General reasoning.
- SPIFFE described as "a standard format for naming a workload". Definition; check the SPIFFE spec wording.
- The "p99 of 13 minutes ... one call in a hundred" reading of the SMI example. Definition of p99; the example value is from the original text.

5.29
- "`kubectl scale webapp ... --replicas=4` writes to the field named by `specReplicasPath`" (illustration, needs the scale subresource on the WebApp type, which the chapter's WebApp CRD does not declare). Hypothetical; no claim about the real CRD.
- Deprecation: clients "see a warning" when a version has `deprecated: true`. Check the CRD deprecation docs for the exact header behaviour.
- `resourceNames` "limits a rule to named objects". General RBAC; no number.
- Kitchen and bell analogy for informers and polling. Analogy only.

5.30
- Protobuf described as "faster to parse than JSON, which is why it suits busy core types". General knowledge; check the apimachinery serializer docs if quoted.
- `ptr.Deref(p, default)` returns the default for a nil pointer. Check `k8s.io/utils/ptr` docs for the exact signature.
- "Floating-point numbers store values in binary, which cannot represent many decimal fractions exactly." General fact; no number.
- "Go 1.22 loop-variable change" and "Go 1.23 timer change" are the original statements; kept.

## Unresolved

- 5.30 length: +45% wc is above the +25 to +40 aim. Not trimmed (rule: never trim). Flag for owner review of the Go-concept explanations.
- 5.28, 5.29, 5.30: original fact questions in the Sources or body were not changed by this pass. Examples: 5.28 Envoy 15 s default route timeout (flagged in the Sources as not verified); 5.29 "Kubernetes Programming with Go, Chapter 8" and "Chapter 6" citations; 5.30 the Protobuf and `intstr` details. Keep them unless a source check says otherwise.
- 5.29 example string `webAppReplcas` in the schema-validation paragraph is a deliberate typo to show pruning. It is a new code span; check the owner accepts it.
- No commit made. Files are in the worktree only.

## Attribution

- Gem book titles in full: *Kubernetes: Up and Running*, *Production Kubernetes*, *Kubernetes Programming with Go*, *Network Programmability and Automation*.
- Chapter cross references kept (5.5, 5.6, 5.9, 5.12, 5.13, 5.15, 5.16, 5.18, 5.19, 5.20, 5.21, 5.22, 5.24, 5.27, 5.31, 5.32, 5.33, 5.35, 4.8, 4.26, 3.8).
