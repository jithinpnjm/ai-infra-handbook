# Checkpoint rewrite: Parts 16 and 17 (rule 10)

Scope: the 12 flagged checkpoints in 9 chapters listed in planning/ledgers/checkpoint_audit_parts_16_18.md (4 in Part 16, 8 in Part 17). Each rewrite keeps its number, its position and the count per chapter. Only the summary line and the answer line of each flagged block changed. Every fact in a new question or answer was checked against the chapter body, with line numbers below. Old answers that were not in the body were dropped, not kept.

Line numbers refer to the worktree file, which has the same body lines as HEAD outside the checkpoint blocks.

## Part 16

### 16.3 Data pipelines and feature stores (`03-data-pipelines-and-feature-stores.md`, checkpoint 16, UNSUPPORTED)

Old question: A CSV file with 17,654 rows and 10 columns takes 14 MB, and the same data as Parquet takes 6 MB. How much smaller is Parquet, and what is the downside?
Old answer (in brief): 14 divided by 6 is about 2.3 times smaller. The saving is 8 MB, which is about 57 percent of the CSV size. The downside is slower point writes. The chapter's table says roughly 6 times less storage, which this example does not show.

New question: A training input is a 14 MB CSV file, and the same data as Parquet is 6 MB. A colleague plans storage on the claim that Parquet is always 6 times smaller. How much smaller is it in this example, and what does Parquet cost you?
New answer: The example file is about 2.3 times smaller, so the colleague should not plan on 6 times. The 6 times figure is AWS's claim that Parquet can be up to 6 times smaller in Amazon S3 than text formats, and the chapter says to treat it as a best case, not a typical result. The saving depends on the data, which is why the table says Parquet is often much smaller. The cost is that point writes are slower, because each new row rewrites a column file.

Support in the chapter:
- Line 173: the format table says Parquet is "often much smaller and faster to read than CSV, with the saving depending on the data", and lists slower point writes as the cost.
- Line 177: "14 MB as CSV ... 6 MB, which is about 2.3 times smaller"; "AWS describes Parquet as up to 2 times faster to unload and up to 6 times smaller in Amazon S3 than text formats. Treat 6 times as a best case, not a typical result"; "Point writes get slower, because each new row rewrites a column file."
- The unsupported claim is removed. The old answer's "57 percent" and "8 MB" were not in the body, so they are gone. The 57 accounts for the one "lost number" in the rewrite guard.

### 16.9 LLM evaluation and guardrails (`09-llm-evaluation-and-guardrails.md`, checkpoint 11, RECALL)

Old question: Why does the chapter recommend a dead man's switch for monitoring?
Old answer (in brief): If the monitoring fails, no alerts arrive and everything looks calm. A dead man's switch is an alert that fires on a schedule. When those alerts stop, a critical alert tells on-call. Set it up before the first production run.

New question: After a deploy, the guardrail monitor stops sending alerts, and the on-call sees no alerts at all and assumes the night was quiet. Why does the chapter recommend a dead man's switch for monitoring, and when should you set it up?
New answer: A monitor that fails silently looks exactly like a quiet night, so an empty alert feed proves nothing. A dead man's switch is an alert that fires on a schedule during normal operation. When those alerts stop arriving, a critical alert tells on-call that the monitoring has failed. Set it up before the first production run.

Support: Line 530 (the Production Kubernetes chapter 9 paragraph): "a monitor that fails silently looks exactly like a quiet night", the dead man's switch definition, and "Set up that switch before the first production run."

### 16.13 Governance, privacy and compliance (`13-governance-privacy-and-compliance-for-ml-platforms.md`, checkpoint 15, RECALL)

Old question: Why would you publish the differential privacy budget on the model card, and which numbers make it up?
Old answer (in brief): The budget records the trade-off between accuracy and privacy, and a regulator will ask about it. It is the pair epsilon and delta, computed from the noise settings, the batch size and the number of training steps.

New question: A team trains a model on medical data with differential privacy, and the model card needs a privacy section. The run has noise settings, a batch size and a fixed number of training steps, but nobody has worked out the budget. Which numbers make up the budget, and why does it belong on the card?
New answer: The budget is the pair epsilon and delta. The training library computes them from the noise settings, the batch size and the number of training steps, so you do not calculate them by hand. You publish them on the model card because they record the trade-off between accuracy and privacy, and a regulator will ask about it. A smaller budget means stronger privacy and usually lower accuracy, so the card should show which side of that trade you chose.

Support:
- Line 316 and line 644: "Differential privacy fits medical data."
- Line 350: the library computes epsilon and delta "from those settings, the batch size and the number of training steps"; publish on the model card because it "records the trade-off between accuracy and privacy that a regulator will ask about"; "A smaller budget means stronger privacy and usually lower accuracy".

### 16.15 Lab: end-to-end MLOps on GKE (`15-lab-end-to-end-mlops-on-gke.md`, checkpoint 9, RECALL)

Old question: Why does `dvc add` plus a Git commit make the dataset part of your code history?
Old answer (in brief): DVC adds a small pointer file to Git and pushes the data to a GCS bucket. The commit holds the pointer, which contains the content hash, and the pipeline records it with every run.

New question: A teammate runs `dvc add` on the churn dataset and commits the pointer file. Later the bucket object shows a different hash from the one in the pointer. What does the mismatch tell you, and why does the dataset become part of your code history?
New answer: DVC adds a small pointer file to Git and pushes the data itself to a GCS bucket, so the commit holds the content hash and the hash travels with the code. A mismatch between the pointer file, the commit and the bucket object means the push and the commit are out of step. Check that all three show the same hash, and record that hash with every run.

Support:
- Line 225: DVC "adds a small pointer file to Git and pushes the data itself to a GCS bucket. ... The commit holds the pointer, so the dataset's content hash becomes part of your code history."
- Line 245: "Check that the pointer file, the commit, and the bucket object all show the same hash, because a mismatch means the push and the commit are out of step." Also "record it with every run."

## Part 17

### 17.1 Observability foundations (`01-observability-foundations-metrics-logs-and-traces.md`, checkpoint 14, RECALL)

Old question: Should you rely on a service mesh to give you complete traces?
Old answer (in brief): No. A service mesh does not remove the instrumentation work. The application must inject and read the `traceparent` header.

New question: A team adds a service mesh, and the trace still breaks at the first hop between the HTTP handler and the inference service. Can the team stop adding instrumentation to the application now, and what must each hop pass along?
New answer: No. The chapter says a service mesh does not remove the instrumentation work, because the request headers must still pass from one service to the next. The application has to inject and read the `traceparent` header on every hop. Without that header, the trace breaks at the first hop that drops it.

Support: Line 303 ("A trace stays whole only when every hop passes the trace ID along"; `traceparent`); line 326 (service mesh does not remove the work; request headers must pass from one service to the next; inference service child spans).

### 17.2 Prometheus and Grafana (`02-prometheus-and-grafana.md`, checkpoint 7, RECALL)

Old question: Why do applications never need to know anything about the metrics system behind Prometheus?
Old answer (in brief): Prometheus is pull-based. Applications only expose a `/metrics` endpoint in the exposition format, and the server scrapes it.

New question: A team ships a new inference service and wants it on the Grafana dashboards. Does the team need to change anything in Prometheus itself, and what must the service expose?
New answer: Not for the metrics path. Prometheus is pull-based, so the arrows point one way, and the service only has to expose a `/metrics` endpoint in the Prometheus exposition format. The server scrapes that endpoint every N seconds. Once the service exposes metrics, add it to the scrape configuration, usually with a ServiceMonitor resource, and the Operator updates the scrape configuration of the matching Prometheus server.

Support:
- Line 71: "Prometheus is pull-based. The server scrapes metrics from a set of targets".
- Line 96: "Every workload exposes a `/metrics` endpoint in the Prometheus exposition format. Prometheus scrapes that endpoint every N seconds".
- Line 205: "Once an application exposes metrics, add it to the scrape configuration. The usual way is a ServiceMonitor resource".
- Line 264: "When you create one, the Operator updates the scrape configuration of the matching Prometheus server."
- The old answer's claim that an application "needs to know the format and nothing more" is replaced, because the body requires adding the service to the scrape configuration.

Checkpoint 8 (RECALL)

Old question: Why does a dead man's switch alert exist, and how does it work?
Old answer (in brief): You cannot get an alert from a system that is itself down. The switch is an alert that fires on a regular schedule. If it stops arriving, a critical alert reaches on-call.

New question: The Prometheus server dies overnight, the dashboard stops updating, and no alert fires. Why can an ordinary alert not report this, and how does a dead man's switch report it?
New answer: You cannot get an alert from a system that is itself down. A dead man's switch is an alert that fires on a regular schedule under normal operation. If that alert stops arriving, a critical alert reaches on-call and tells them the metrics or alerting system is down. The switch works because silence becomes the signal.

Support: Section 1.11 "The dead man's switch", lines 384-388 (the same sentences; "You will not get an alert from a system that is itself down"; "The switch works because silence becomes the signal").

### 17.8 Performance engineering methodology (`08-performance-engineering-methodology-and-decision-trees.md`, checkpoint 7, RECALL)

Old question: Why does the ridge point decide whether a kernel is memory-bound or compute-bound?
Old answer (in brief): The ridge point is the compute peak divided by the memory bandwidth. A kernel left of it waits on memory, and a kernel right of it waits on arithmetic. The fix differs on each side.

New question: An attention kernel on an H100 works out to 2048 FLOP per byte, and the ridge point is about 295 FLOP per byte. Why does the ridge decide the fix, and which side is the kernel on?
New answer: The ridge is the compute peak divided by the memory bandwidth, so a kernel left of it waits on memory and a kernel right of it waits on arithmetic. At 2048 FLOP per byte, the attention kernel is far right of 295, so it is compute-bound, and the chapter suggests lower precision or fuller use of Tensor Cores. A memory-bound kernel needs better access patterns instead, so a wrong guess sends the team to the wrong part of the code.

Support:
- Line 178: "I_ridge: 295 FLOP/byte"; line 181: ridge is compute peak divided by bandwidth; "a wrong guess sends the team to the wrong part of the code" (also line 181); "A memory-bound kernel needs better access patterns".
- Line 195: "Arithmetic intensity: 6.87e10 / 3.36e7 = 2048 FLOP/byte"; line 199: "The kernel is compute-bound".
- Line 203: "the chapter suggests lower precision or fuller use of Tensor Cores".
- Line 734 (checkpoint 18): "about 2,048 FLOP per byte".
- Number note for the rewrite guard: "2048" is new in the checkpoint, but it is the value at line 195 of the body.

### 17.10 Cluster lifecycle, upgrades and change management (`10-cluster-lifecycle-upgrades-and-change-management.md`, checkpoints 9, 14 and 20, RECALL)

Checkpoint 9

Old question: Which pass conditions must a canary meet before the next stage?
Old answer (in brief): `dcgmi diag -r 3` passes, nccl-tests bus bandwidth is within 5 percent of the baseline, no tier 3 Xid, failed row remap, GPU count mismatch or missing exporter, no fast SLO burn, no node in the `upgrade-failed` state, and the soak time passes.

New question: A canary's nccl-tests bus bandwidth falls below the pre-upgrade baseline by more than the allowed margin, but the hardware diagnostic passed. Does the canary clear the gate for the next stage, and which other conditions must hold?
New answer: No, the bus bandwidth must be within 5 percent of the pre-upgrade baseline, so a larger shortfall fails the gate even when the hardware check passes. The hardware check is `dcgmi diag -r 3`, and the others are no tier 3 Xid, no failed row remap, no GPU count mismatch, no missing exporter, no fast SLO burn, and no node in the `upgrade-failed` state. The soak time must also pass before the next stage.

Support: Lines 202-208 (the pass conditions list: `dcgmi diag -r 3` passes; bus bandwidth "within 5 percent of the pre-upgrade baseline"; tier 3 Xid, failed row remap, GPU count mismatch, missing exporter; "No fast burn on the SLOs"; "No node in the `upgrade-failed` state"); line 196 (soak of 24 hours); line 192 (the soak "for the soak time").

Checkpoint 14

Old question: How do you pause the driver upgrade, and what happens to nodes already done?
Old answer (in brief): Set `autoUpgrade` to false in the ClusterPolicy. The Operator removes the upgrade-state labels and stops moving more nodes. Nodes already upgraded stay on the new driver.

New question: The driver upgrade is partway through the fleet and the canary has started to fail, so the team must stop the controller before more nodes move. What do you change, and what happens to nodes that are already done?
New answer: Set `autoUpgrade` to false in the ClusterPolicy. The Operator then removes the upgrade-state labels and stops moving more nodes, and nodes already upgraded stay on the new driver. A pause does not undo the finished work, so it is not a rollback, and a rollback needs its own change to the driver version.

Support: Line 209 ("To stop the whole upgrade, set `autoUpgrade` to false, which makes the Operator remove the upgrade-state labels. Nodes already upgraded stay upgraded. Stopping does not undo the work that is finished, so a pause is not a rollback."); lines 386-388 (pause step: stop the controller from moving more nodes); line 237 onward (Rollback plan: patch the driver version back); line 513 (a canary that fails its checks goes back).

Checkpoint 20

Old question: Why can a peer review not be replaced by automated tests, and in what order does a change move?
Old answer (in brief): A human reviewer catches gaps tests cannot see, such as a rollback plan that says too little. The order is change request, peer review, automated tests including the rollback test, staging, canary, early stage, wide stage, then verification.

New question: A change has a rollback step that says only one line, and the author says the automated tests are green. Why can a peer review not be replaced by those tests, and where does the reviewer read the change in the order?
New answer: A peer reads the change before anything runs, because the author is the person least likely to notice what is missing. A human reviewer catches gaps tests cannot see, such as a rollback plan that says too little. The order is change request, peer review, automated tests including the rollback test, staging, canary, early stage, wide stage, then verification, so the review comes before any test runs.

Support: Line 252 ("whose rollback step is one vague line. A peer reads the change before anything runs, because the author is the person least likely to notice what is missing"); line 621 (the order; human reviewer catches gaps); line 487 (a reviewer who finds the rollback plan vague should request changes).

### 17.15 On-call runbooks (`15-on-call-runbooks.md`, checkpoint 11, RECALL)

Old question: Why does the chapter recommend a dead man's switch alert?
Old answer (in brief): It is an alert that fires on a schedule. When it stops firing, the on-call hears that metrics or alerting have failed. Without it, a broken alerting system looks like a quiet, healthy one.

New question: A week goes by with no pages at all, and the on-call assumes the platform is healthy. Is that silence good news, and what alert would tell you whether the alerting path still works?
New answer: Not necessarily, because a broken alerting system looks the same as a quiet, healthy one. A dead man's switch is an alert that fires on a schedule, and when it stops firing, the on-call hears that metrics or alerting have failed. PagerDuty offers an integration for this, called Dead Man's Snitch.

Support: Line 421 ("Picture a pager that is silent for a week. It might mean calm, or it might mean the pager is broken."). Line 431 ("adds one alert that every team needs: a dead man's switch. It is an alert that fires on a schedule, and when it stops firing, the on-call hears that metrics or alerting have failed. PagerDuty offers an integration for this, called Dead Man's Snitch.").

## Guard and span results

- `python3 tools/rewrite_guard.py HEAD WORKTREE` on the nine chapters: 0 hard failures.
- Numbers, guard notes:
  - 16.3: 1 lost number, "57" (the old answer's computed 57 percent, not in the body, now removed). The "8 MB" was dropped too, but "8" appears elsewhere in the chapter, so the guard did not flag it.
  - 17.8: 1 new number, "2048", supported at line 195 and line 734 of the chapter.
- Backticked spans: no span added or dropped. The span Counter (outside code fences) is identical HEAD vs worktree for all nine chapters.
- Dropped spans: none.
- Checkpoint count per chapter: unchanged (20 each).
- Changed lines: only the summary and answer lines of the flagged blocks (2 lines each, 4 in 17.2, 6 in 17.10).
