# Voice rewrite ledger: Part 16 chapters 16.13, 16.14, 16.15 (run e)

Scope: `docs/part-16-mlops-llmops/13-governance-privacy-and-compliance-for-ml-platforms.md`, `14-platform-design-multi-tenant-ai-factory-quotas-and-chargeback.md`, `15-lab-end-to-end-mlops-on-gke.md`. Warm teacher voice rewrite per `planning/HAIKU_REWRITE_INSTRUCTIONS.md` sections 0-3 and `planning/RULES_AND_WORKFLOW.md` section 1. Step 6 (EXTERNAL_EDITS.md) skipped on instruction. Nothing committed.

## Word counts (`wc -w`, whole file, HEAD vs worktree)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 16.13 Governance, privacy and compliance | 7389 | 10064 | +36.2% |
| 16.14 Platform design, quotas and chargeback | 9402 | 12357 | +31.4% |
| 16.15 Lab: end-to-end MLOps on GKE | 6578 | 8550 | +30.0% |

Prose-only counts from `rewrite_guard.py`: 6650 to 9325; 8209 to 11164; 5206 to 7178.

## Gates (run, output seen)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>` for each chapter: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0, residue 0 to 0 in all three. (One new code span in 16.14 and one in 16.15 were found during the run and unwrapped before the final run.)
- `python3 tools/restore/chain_gate.py <file>`: 16.13 at 0.3, 16.14 at 0.0, 16.15 at 0.1 (limit 1.5).
- Span check (inline code spans in prose, HEAD vs worktree): `{}` for all three.
- Locked content compared with HEAD: checkpoint block and Sources tail identical; all code blocks (14, 23, 16) identical; all table rows identical; all headings identical; 20 `<details>` blocks in each chapter.
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed".
- `npm run build`: NOT run (task said no npm build).
- `python3 tools/language_audit.py`: not run.
- Exclamation marks in prose: none. Raw `<` or `{` added: none.
- Forbidden phrasing ("will be able", "should be able", "you will learn", "by the end"): none in the three files.

## What changed (structure and voice)

- Every H2 and H3 with prose opens with a situation sentence (a regulator's letter, a Monday review, a Friday dashboard, an on-call night, a team lead's form). Where a locked heading sits above, the situation is the first sentence under it.
- "Outcomes" lists rewritten as one plain paragraph in 16.13 (six pieces of work), 16.14 (six pieces of work) and 16.15 (six pieces of work). The "Outcomes" headings stay. "six", "five" and "three" words kept where the original had them.
- Bullet lists kept as bullets; each bullet now carries a question or a plain explanation.
- Exercises: same count (6 in 16.13, 6 in 16.14, 6 in 16.15). Same solution sketches, commands and spans. 16.15 exercise titles lost their bold markers so the section keeps one bold idea. Each exercise opens with a situation.
- Lab: 16.13 keeps steps 1-7 (8.2 to 8.8) with same commands and expected lines; 16.14 keeps steps 1-7 (8.2 to 8.8); 16.15 keeps its thirteen-step structure and headings. "What to record" lists (5 questions each) unchanged. Lab-intro honest status: one sentence in 16.13 (existing "untested" bold word kept), one in 16.14 (existing), one new sentence above the 16.15 steps ("These steps were not run on a live cluster..."). The duplicate "untested" sentence after the 16.13 lab was reworded to drop the status claim, and 16.14 section 8.9 "should be able" lines were reworded.
- Honest status word per chapter: 16.13 "untested" in lab intro (plus the locked tail); 16.14 "untested" in lab intro (plus the locked tail); 16.15 "not run" in the new sentence above the steps (plus the locked "Not verified on live hardware" tail, which says "untested").
- Number hygiene: no digit added to prose. Spelled numbers not in the original were removed (for example "two in the morning", "line four", "one afternoon", "two cluster"). Every number in the original prose survives.
- Attribution: book attributions in prose are exactly the original ones (LLMOps Chapter 8 and 9, Engineering AI Systems Chapters 9 and 10, Designing Machine Learning Systems Chapter 11, AI Factory Chapter 11, Production Kubernetes chapters 9, 10, 12, 15, Machine Learning Platform Engineering chapter 9, AI Engineering chapter 10, NVIDIA Zero-to-Hero volume 21 and 25 where the figure block already named them). No new book, chapter or volume was attributed.
- Chapter 16.15 fixes from earlier runs kept: UCI Adult is stated as an income dataset used as a stand-in for the churn files, not as a churn dataset. Ledger fixes_FA and checkpoint_rewrite_C items for 16.13 (homomorphic encryption 10-100x figure has no source, and the chapter says so) kept.
- 16.14 Kueue wording kept as HEAD states it: Kueue limits GPUs, not money (section 7.2).
- 16.14 Pod Security Policy warning kept (PodSecurityPolicy removed in Kubernetes 1.25; Pod Security Admission replaces it).

## Needs source (general explanations added in the rewrite, not in HEAD)

These are definitions, general practice, analogies or scenarios. None adds a number. Check each before the chapters are marked final.

16.13
- Definitions: EU AI Act as the European Union's law for artificial intelligence; GDPR spelled out at first use; "critical path"; identity and access management (IAM) spelled out; object-lock as a fixed retention period; tamper-evident meaning; Kubernetes Job; DAG as a pipeline with fixed order and no loops; DELETE and row-level update; Helm and release; Keras and optimizer; gradient as the list of adjustments; secure aggregation; "without undue delay" as a legal standard for counsel to interpret; amortisation in exercise 6 as spreading one cost over a day's requests.
- General practice or claims: lineage audited by sampling real runs (section 2.3); a Git pull request as a second record next to lineage (2.3); gradients are not automatically private (5.2); a smaller differential privacy budget means stronger privacy and usually lower accuracy (5.3); federated learning example of a phone keyboard (5.2); a cleaning step shipped without lineage (2.3 scenario); a lineage registration with a gap is "the same failure as a missing lock" (2.3, rhetorical).
- Analogies and scenarios (no facts): the city map without street names (2.1); the building-code vs coat-of-paint comparison (intro); three regulators in one week (1.1); the loan decline letter (intro); the Monday model-card reader (3.1); the Friday fairness dashboard (6.3); the Sunday lineage slowdown (6.1); the compliance analyst who asks for write access (6.2); the hospital and phone-keyboard examples; the relay race for the erasure workflow (4.2).
- Lab: "a slow answer on a practice day is a clue worth chasing, because it can point to a missing edge" (8.9) is an opinion, reworded from an earlier stronger claim.

16.14
- Definitions: tenant; primitive; FinOps; Kubernetes ResourceQuota as namespace-scoped (HEAD); CNI plug-in; admission webhook; RBAC; kubelet; Open Policy Agent and Kyverno as policy engines; Kueue as an admission add-on; hypervisor; eviction; Pending; cgroups and CFS as in HEAD, plus the shares-as-pie analogy; backport; NVAIE expansion (NVIDIA AI Enterprise); CSI driver; ERP expansion; chargeback; Terraform and module; CI; canary, shadow traffic and chaos experiment; burn rate; MIG expansion (Multi-Instance GPU); storage prefix; reconciler; break-glass admin; finalizer; Elasticsearch; Fluentd tag; spot capacity; observability; the GPU driver tool as the example for a privileged workload (1.5, "A GPU driver tool is a common example").
- General practice or mechanism: "a fence built after the neighbours have moved in is harder to put up" (1.4); test the default-deny in a scratch cluster and check DNS (1.4); noisy neighbour analogy (2.4); "the container still has quota left, but the kernel stops it anyway" (2.4 kernel bug, restates HEAD's throttling claim); a dashboard and bill that disagree lose trust (3.1); "a cost spike can be a bug in a job rather than a team that deserves more money" (6.3); "Oversubscribing means promising more memory..." (2.4); "A target nobody can meet teaches the team to ignore the target" (4.2); "a guess can fail a team" (6.1); "a team that complains on Monday when the dashboard showed the problem on Friday" (7 intro, scenario).
- Scenarios (no facts): the product manager and slow platform (5.2); the lunchtime slow web service (2.4); the midnight namespace typed by hand (6.2); the Thursday change that breaks the promotion gate (lab 12 CI); the first Monday of the platform review (14 section intro).
- Lab expected outputs: "in the Argo Workflow stage the first, second and third commands" (15, 5), "the Restart Count tells you how often" (14 2.4 memory), "the kubelet is the agent on each node" (14 1.5).

16.15
- Definitions: DVC as Data Version Control; content hash; binary classification; GCS as Google Cloud Storage; Argo Workflows as a Kubernetes pipeline engine; seed; parameter; AUC expansion and meaning; Staging as a holding area; KServe; canary origin (miners' canaries); READY=True as readiness; Prometheus, Grafana and Evidently roles; port-forward; drift detector; gang scheduling; self-hosted runner; PagerDuty and Opsgenie; escalation policy; cooldown (16.15 13.4); Helm chart.
- General practice or mechanism: the training stage stalls and the cause is one missing piece at setup (2 intro); a version pinned in a shell history is guesswork (3 intro); "later install that points at an earlier one fails" (3); "run one check per piece rather than trusting install messages" (2); "a dashboard with only latency and errors can look healthy while the model goes wrong" (8, after panels); an alert test that fires proves the route (8); a drift trigger that does not fire may mean the injected drift never reached the feature view (9); "skipping the middle check is an easy way for a request to look closed" (10); reporting success early is the trap (13.5); a well-meaning cleanup can delete records (13.6); "Object lock is cheap to turn on at the start and very hard to add after" (13.6); "a failure at the start costs seconds, a failure at the register stage costs a full training run" (13.2); "a Pod that runs fine for days" (not in 15); "an alert with no next step is a question left on the desk at night" (11); "the test of a handoff is to ask someone who did not build it" (11); CI pass criteria comment (12).
- Scenarios (no facts): the on-call night (intro); the Monday support queue (9); the customer waiting for confirmation (10); the Thursday chart change (12); the first on-call night after handoff (11); the platform engineer who opens the lab unread (Prerequisites).

## Changed wording to flag (no fact changed; owner review)

- 16.15 section 13.3: the heading and symptom keep the error text "cluster binding not found". The added sentence says the cause is bucket access and that the cluster name in the error is not the cause. HEAD's own diagnosis says the bucket is unreadable, so the sentence follows HEAD, but the error text and the cause still do not obviously match. Owner should confirm the error string.
- 16.15 section 13.3 fix: added "A quick read test with the same service account tells you whether the fix worked". Practice advice, Needs source.
- 16.15 section 7 (Exercise and step text): "The Kueue ClusterQueue should refuse new Jobs once the limit is reached" (Exercise 2) was kept as HEAD wrote it. It conflicts with 16.14 section 7.2, which says Kueue limits GPUs, not money. Left as is to keep the facts unchanged; a fix is one line (replace with "a controller suspends the LocalQueue when spend crosses the cap").

## Unresolved

1. Build: `npm run build` not run (task said no npm build). Mermaid check passed (776 diagrams, 0 failed).
2. `python3 tools/language_audit.py` and pytest not run (the three chapters have no code tests in this pass).
3. Checkpoint answers and Sources tails are locked by the task and were not edited. The 16.14 checkpoint 16 answer (`$2 per GPU-hour` ... `$0.50`, in the locked answer text) has two dollar signs that a math plugin could read as a `$...$` pair. These are plain prose amounts with no stray backticks. Locked text; flagged only.
4. 16.15 Exercise 2 wording conflict with 16.14 section 7.2 (see above). Owner decision.
5. 16.15 section 13.3 error text (see above). Owner decision.
6. Lab step sentences in 16.13 section 8 and 16.14 section 8 were rewritten with the same commands; rule 9 (one question per sentence, at most two numbers) was applied by eye, not by a script. A reader pass is advisable.
7. The 16.13 lab intro keeps the bold word **untested** (one bold idea in the section). The status sentence in 16.15 is new; the locked "Not verified on live hardware" tail keeps "untested" as before.
8. The 16.14 and 16.15 repeated sentences (checkpoint and tail text repeated in HEAD) were left as they are.
9. Growth: 16.13 is at +36.2% (wc -w), 16.14 at +31.4%, 16.15 at +30.0%. All within the +28 to +40 band.
