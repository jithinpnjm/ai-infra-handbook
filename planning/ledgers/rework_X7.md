# Rework ledger X7

## 16.7 Model serving platforms

Changed: transformer is a separate Deployment (KServe collocation page), with the collocation option; shadow mode no longer described as canary at 100 percent (promotes), mirroring via Istio; NetworkPolicy rewritten (DNS, HTTPS to public addresses, same-namespace, kubernetes.io/metadata.name labels) and checkpoint 6 changed to the init-stage symptom; BentoML example now declares BentoModel at class scope, loads with joblib, uses @bentoml.api (code/part16/multi_model_service.py and network_policy.yaml updated); opening 'background reading' block replaced by prose; new section 4.4 LLMs on KServe (Standard mode, Hugging Face vLLM runtime, modelcar, LLMInferenceService with Gateway API Inference Extension); new section 2.5 project status; canary noted as serverless-mode only; lab install set to Serverless mode (canary, scale to zero need Knative); exercises 1 and 5 changed to checkable tasks.

Watch list verdicts: transformer sidecar - fixed (KServe docs). Shadow mode - fixed (canaryTrafficPercent 100 promotes; Istio mirroring docs). NetworkPolicy - fixed. BentoModel.predict - fixed (BentoML docs: BentoModel is a reference, load with path_of). Seldon Core v1/v2 and licence - fixed in 2.5: v1.19.0 2026-01-23, v2.10.2 2025-12-19, both LICENSE files Business Source License. Yatai - fixed: repo archived, last release v1.1.13 2023-10-09. KServe image registry - softened: storage-initializer image is kserve/storage-initializer on Docker Hub per the docs config sample; gcr.io claim removed.

Unresolved: Seldon YAML kept as one predictor with a child node, as instructed, but it is Core v1 API; not applied to a cluster. LLMInferenceService is v1alpha1, example copied from docs, untested. Section 5.1 SLO table, 5.4 alert thresholds and 6.x figures remain unsourced examples. Exercises 2, 3, 4, 6 still 'Add X' tasks with solution sketches (not reworked, scope was the four errors). Exercise 2 sidecar polling nvidia-smi is not a sidecar-of-transformer issue. Chapter 16.8 and 16.6 not checked for the same shadow wording.

## Part 19 draft-history sweep: removed or rewritten text (file, line, old text, new text or DELETED)

- 02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md line 494
  - old: KAI keeps a hierarchy of Queue objects. Only leaf queues run jobs. The Queue API is `scheduling.run.ai/v2`, and units differ from Kubernetes: GPU in devices, CPU in millicores and memory in megabytes. A draft wrote `1Ti` for memory, which the CRD rejects because the field is a number.
  - new: KAI keeps a hierarchy of Queue objects. Only leaf queues run jobs. The Queue API is `scheduling.run.ai/v2`, and units differ from Kubernetes: GPU in devices, CPU in millicores and memory in megabytes. Write memory as a number, not as `1Ti`, because the CRD rejects a quantity string.

- 02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md line 402
  - old: The nominal quotas now sum to the hardware: 12 for training and 4 for serving, 16 in total. A draft gave training 16 and serving 4. Kueue allows quotas above the hardware, but then the serving reserve is a hope, not a guarantee. Only GPUs are covered. By default Kueue does not account for resources that no ClusterQueue declares. The config key `resources.quotaCheckStrategy: BlockUndeclared` changes that.
  - new: The nominal quotas now sum to the hardware: 12 for training and 4 for serving, 16 in total. Kueue allows quotas above the hardware, but then the serving reserve is a hope, not a guarantee. Only GPUs are covered. By default Kueue does not account for resources that no ClusterQueue declares. The config key `resources.quotaCheckStrategy: BlockUndeclared` changes that.

- 02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md line 327
  - old: An earlier draft used `kueue.x-k8s.io/v1beta1`. In Kueue v0.20.5 that version is no longer served, and `v1beta2` renames the cohort field to `cohortName`. The same draft set `withinClusterQueue: Any`. The CRD allows only `Never`, `LowerPriority` and `LowerOrNewerEqualPriority`, so the schema check rejected it.
  - new: Use `kueue.x-k8s.io/v1beta2`. In Kueue v0.20.5 `v1beta1` is no longer served, and `v1beta2` names the cohort field `cohortName`. For `withinClusterQueue` the CRD allows only `Never`, `LowerPriority` and `LowerOrNewerEqualPriority`, so a value such as `Any` fails the schema check.

- 02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md line 311
  - old: Training is 50 on purpose. An earlier draft used 100, and KAI treats a priority of 100 or more as non-preemptible. Such workloads may use only in-quota resources. A training class at 100 would never borrow idle GPUs and could never be preempted by KAI. KAI also ships `train` at 50 and `inference` at 125. Our class names are ours, so check that the number lands on the right side of 100.
  - new: Training is 50 on purpose. KAI treats a priority of 100 or more as non-preemptible. Such workloads may use only in-quota resources. A training class at 100 would never borrow idle GPUs and could never be preempted by KAI. KAI also ships `train` at 50 and `inference` at 125. Our class names are ours, so check that the number lands on the right side of 100.

- 02-capstone-a-kubernetes-gpu-platform-with-kai-and-kueue.md line 122
  - old: An earlier draft of this chapter used `gpu-driver-version=latest` together with the Operator's device plugin. NVIDIA's page says to disable the GKE device plugin and the automatic driver. It lists these as GKE features the Operator does not support. The script below follows NVIDIA's page.
  - new: NVIDIA's page says to disable the GKE device plugin and the automatic driver. It lists these as GKE features the Operator does not support. The script below follows NVIDIA's page, so it does not use `gpu-driver-version=latest` together with the Operator's device plugin.

- 04-capstone-multi-node-training-with-fault-tolerance.md line 1233
  - old: - The previous draft of this chapter, which cited `code/part19/checkpoint.py`, `checkpoint_recovery.py` and `fsdp_config.py` as files that did not exist. Those names are replaced by the tested `c04_*` files.
  - new: DELETED

- 04-capstone-multi-node-training-with-fault-tolerance.md line 598
  - old: PyTorch's NCCL backend has two layers that do. The watchdog is a background thread in each process that watches the collectives it launched. The monitor thread watches the watchdog. Both come from PyTorch's `ProcessGroupNCCL`, not from NCCL itself, so searching the NCCL documentation for a watchdog variable finds nothing. The earlier draft of this chapter named an `NCCL_TIMEOUT` variable. The NCCL environment variable documentation for version 2.32.3 has no such variable, and that item was removed.
  - new: PyTorch's NCCL backend has two layers that do. The watchdog is a background thread in each process that watches the collectives it launched. The monitor thread watches the watchdog. Both come from PyTorch's `ProcessGroupNCCL`, not from NCCL itself, so searching the NCCL documentation for a watchdog variable finds nothing. The NCCL environment variable documentation for version 2.32.3 has no `NCCL_TIMEOUT` variable.

- 04-capstone-multi-node-training-with-fault-tolerance.md line 579
  - old: - The agent's own default for the monitor interval is 0.1 seconds, not the 30 seconds that appeared in an earlier draft of this chapter.
  - new: DELETED

- 05-capstone-an-nccl-tests-fabric-lab.md line 764
  - old: - Removed from the earlier draft because no source supports them: the H100 busbw range, the "hybrid PCIe 95.18 GB/s" row, the "5,850 microseconds at 361.36 GB/s" cluster row and its per-rail percentage, the ConnectX generation table, NVLink generations before Hopper, the Kubernetes Topology Manager paragraph, the 54 and 81 percent AllReduce project figures, the 100 MB within 5 ms gate, and the 64 percent GPU-fault statistic.
  - new: DELETED

- 05-capstone-an-nccl-tests-fabric-lab.md line 747
  - old: The earlier draft took wording from these volumes. Facts from them that could not be confirmed against a source are removed or labelled below.
  - new: DELETED

- 05-capstone-an-nccl-tests-fabric-lab.md line 169
  - old: The PCIe side is separate. A host-to-device copy leaves the node through PCIe, and a Gen5 x16 slot gives roughly 64 GB/s per direction. If `nvbandwidth` reads about half of what the slot should give, suspect a link that trained at x8, and confirm the negotiated width with `lspci -vv`. The exact `nvbandwidth` thresholds in earlier drafts were from memory and are removed. Compare with the same node's baseline.
  - new: The PCIe side is separate. A host-to-device copy leaves the node through PCIe, and a Gen5 x16 slot gives roughly 64 GB/s per direction. If `nvbandwidth` reads about half of what the slot should give, suspect a link that trained at x8, and confirm the negotiated width with `lspci -vv`. Compare with the same node's baseline.

- 05-capstone-an-nccl-tests-fabric-lab.md line 167
  - old: There is no honest sourced busbw target for a single node in this chapter. Earlier drafts quoted a "750 to 800 GB/s" range for H100 nodes, and that figure is not in any source this chapter uses, so it is removed. NVLS can also change the data path. The single-node gate is therefore your own commissioning baseline, plus two integrity conditions: `#wrong` is zero and the link entries show NVLink.
  - new: There is no sourced busbw target for a single node in this chapter, because no source this chapter uses gives one for an H100 node. NVLS can also change the data path. The single-node gate is therefore your own commissioning baseline, plus two integrity conditions: `#wrong` is zero and the link entries show NVLink.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 1045
  - old: - `docs/nvidia-zero-to-hero/volume-24/chapter-05-troubleshooting-incident-response.md`: the incident-response project and its success criteria, which I checked and found different from the targets the earlier draft attributed to it.
  - new: - `docs/nvidia-zero-to-hero/volume-24/chapter-05-troubleshooting-incident-response.md`: the incident-response project and its success criteria, which are different from this chapter's game-day targets.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 1016
  - old: One percent of 730 hours is 7.3 hours, which is 438 minutes. The 43.8 minute figure belongs to 99.9 percent. The earlier draft mixed them up.
  - new: One percent of 730 hours is 7.3 hours, which is 438 minutes. The 43.8 minute figure belongs to 99.9 percent.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 1006
  - old: The documentation gives under 35 minutes for 8 GPUs and under 10 minutes for 4. The earlier draft's 15 minutes was not supported.
  - new: The documentation gives under 35 minutes for 8 GPUs and under 10 minutes for 4.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 951
  - old: The catalog lists Xid 61 as unused. The earlier draft's description of it had no support in the catalog.
  - new: The catalog lists Xid 61 as unused, so there is nothing to alert on.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 783
  - old: The earlier draft asked for a cordon within 2 minutes of the condition. That cannot be met when `unhealthyFor` is 2 minutes, so I changed the target to 3.
  - new: The target is a cordon within 3 minutes of the condition. A 2-minute target cannot be met when `unhealthyFor` is 2 minutes.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 773
  - old: A game day is a hypothesis with a clock. The earlier draft said its targets came from the incident-response project in nvidia-devops volume 24. I checked. That project's success criteria are about finding an NVLink fault within 15 minutes, and they say nothing about 5 minutes to detect or 48 hours to a post-mortem. The targets here are my own, and I derive them from the loop's settings so each one is checkable.
  - new: A game day is a hypothesis with a clock. The targets here are my own, and I derive them from the loop's settings so each one is checkable. The incident-response project in nvidia-devops volume 24 has success criteria about finding an NVLink fault within 15 minutes, and they say nothing about 5 minutes to detect or 48 hours to a post-mortem.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 757
  - old: The earlier draft included a worked example of a very large CRC count on one GPU against zero on its neighbour, and a claim about MIG mode disabling NVLink peer-to-peer. I found no source for either, so I removed both.
  - new: DELETED

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 751
  - old: For application codes such as 13, 31 and 32, restart the process and watch the count. One restart followed by stability points at the application. Repeats on one GPU across unrelated applications point at hardware, and that is my escalation rule, not catalog text. For self-healing codes such as 63 and 92, take no action in real time. Review the rate weekly. The earlier draft said to escalate at a 3x week-over-week rise. I have no source for that number, so I treat it as a starting idea and not as a rule.
  - new: For application codes such as 13, 31 and 32, restart the process and watch the count. One restart followed by stability points at the application. Repeats on one GPU across unrelated applications point at hardware, and that is my escalation rule, not catalog text. For self-healing codes such as 63 and 92, take no action in real time. Review the rate weekly. A threshold such as a 3x week-over-week rise is a starting idea, not a sourced rule.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 747
  - old: Add `-j` for JSON output. An exit code of 0 means success, and 226 means the diagnostic ran and reported an error. The documentation also warns that these are online diagnostics. They run in the current environment, and full offline diagnostics from a different NVIDIA tool are required for an RMA. So a passed level 3 run is my gate for returning a node to the pool. It is not proof that the part is good enough to skip the vendor's own process. This distinction is easy to miss, and the earlier draft did.
  - new: Add `-j` for JSON output. An exit code of 0 means success, and 226 means the diagnostic ran and reported an error. The documentation also warns that these are online diagnostics. They run in the current environment, and full offline diagnostics from a different NVIDIA tool are required for an RMA. So a passed level 3 run is my gate for returning a node to the pool. It is not proof that the part is good enough to skip the vendor's own process.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 738
  - old: The DCGM diagnostic has four run levels. The table gives the durations from the DCGM documentation. A level 3 run on an 8-GPU system is documented as under 35 minutes. The earlier draft said about 15 minutes, which the table does not support.
  - new: The DCGM diagnostic has four run levels. The table gives the durations from the DCGM documentation. A level 3 run on an 8-GPU system is documented as under 35 minutes.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 703
  - old: The earlier draft described a PCIe rescan for Xid 79, with steps to remove the device from the bus and reload the driver. The catalog does not give that procedure, and the nvidia-devops DCGM chapter says to collect a bug report and hand it to the hardware owner. I removed the rescan procedure and kept the catalog's action.
  - new: The catalog does not give a PCIe rescan procedure for Xid 79, and the nvidia-devops DCGM chapter says to collect a bug report and hand it to the hardware owner. So this chapter keeps only the catalog's action.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 528
  - old: The budget needs an example. On this chapter's pool of four nodes, 10 percent rounds up to 1 node. On a pool of 32 nodes it is 4. The earlier draft said 10 percent of the 32-GPU pool was 3 nodes. The pool has four nodes, and the rounding gives 1, so I corrected it. I checked both numbers by running the operator's own `Budget` function.
  - new: The budget needs an example. On this chapter's pool of four nodes, 10 percent rounds up to 1 node. On a pool of 32 nodes it is 4. I checked both numbers by running the operator's own `Budget` function.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 440
  - old: An alert needs an objective behind it. The arithmetic below is computed by a tested script. Three results matter. A 99 percent availability target allows 438 minutes, which is 7.3 hours a month. A 99.9 percent target allows 43.8 minutes. And a 98 percent GPU-health target allows 2 failing GPUs out of 100, but allows none out of 32. The earlier draft said 99 percent was about 43 minutes. That figure belongs to 99.9 percent, so I corrected it.
  - new: An alert needs an objective behind it. The arithmetic below is computed by a tested script. Three results matter. A 99 percent availability target allows 438 minutes, which is 7.3 hours a month. A 99.9 percent target allows 43.8 minutes. And a 98 percent GPU-health target allows 2 failing GPUs out of 100, but allows none out of 32.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 401
  - old: Third, the memory-pressure alert from the earlier draft is gone. A training process that reserves nearly all GPU memory is normal, so the alert would fire constantly and say nothing about the node's health. That is a workload signal and belongs on a workload dashboard.
  - new: Third, there is no memory-pressure alert. A training process that reserves nearly all GPU memory is normal, so the alert would fire constantly and say nothing about the node's health. That is a workload signal and belongs on a workload dashboard.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 175
  - old: Three corrections come from this table. Xid 61 is listed as unused, so the earlier draft's "micro-controller breakpoint" has no support. Xid 62 is the micro-controller halt. And Xid 92 has an immediate action of IGNORE, which is why it is a trend to review and never a real-time page. The investigatory column for 92 says to contact support, so a rising rate still deserves a ticket.
  - new: Three points come from this table. Xid 61 is listed as unused, so it has no alert rule. Xid 62 is the micro-controller halt. And Xid 92 has an immediate action of IGNORE, which is why it is a trend to review and never a real-time page. The investigatory column for 92 says to contact support, so a rising rate still deserves a ticket.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 153
  - old: The NVIDIA Xid catalog gives each code an immediate action. This chapter groups codes by that action. The grouping is the chapter's policy, not NVIDIA's. The earlier draft called the groups "tiers" and implied that the catalog defines them. It does not. The table shows the rows this chapter handles. I fetched the catalog on 2026-11-10, and its footer says it was last updated on 2026-11-04.
  - new: The NVIDIA Xid catalog gives each code an immediate action. This chapter groups codes by that action. The grouping is the chapter's policy, not NVIDIA's, and the catalog does not define the groups. The table shows the rows this chapter handles. I fetched the catalog on 2026-11-10, and its footer says it was last updated on 2026-11-04.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 139
  - old: The earlier draft also promised a freshness alert for series that stop updating while the target still answers. I removed it. Prometheus stamps each sample with the scrape time, so the timestamp cannot show that the exporter served a cached value. I have no tested rule that detects that failure, and I will not ship one I cannot test.
  - new: There is no freshness alert for series that stop updating while the target still answers. Prometheus stamps each sample with the scrape time, so the timestamp cannot show that the exporter served a cached value. I have no tested rule that detects that failure, and I will not ship one I cannot test.

- 06-capstone-node-health-automation-with-dcgm-and-an-operator.md line 69
  - old: This matters because the names changed. Older material, including some of this handbook, uses names such as `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_XID_ERRORS` and `DCGM_FI_DEV_FB_USED`. None of them appear in the 4.9.0 default file. The same file uses `DCGM_FI_DEV_GPU_UTIL_RATIO`, `DCGM_FI_DEV_XID_ERROR` and `DCGM_FI_DEV_FB_USED_BYTES`. The earlier draft of this chapter used eight names that the 4.9.0 file does not contain. This version uses only names that the file contains, and a test checks that.
  - new: This matters because the names changed. Older material, including some of this handbook, uses names such as `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_XID_ERRORS` and `DCGM_FI_DEV_FB_USED`. None of them appear in the 4.9.0 default file. The same file uses `DCGM_FI_DEV_GPU_UTIL_RATIO`, `DCGM_FI_DEV_XID_ERROR` and `DCGM_FI_DEV_FB_USED_BYTES`. This chapter uses only names that the file contains, and a test checks that.

- 08-capstone-mig-multi-tenancy.md line 998
  - old: The corrections were these. The draft's Kueue YAML used a field that does not exist and an old cohort field, and the CRD checker found both. It cited 11.25 and 11.17 for MIG and time-slicing, where the chapters are 11.24 and 11.25. It listed a 5g.40gb profile that NVIDIA does not publish, and `nvidia.com/mig-1g.5gb` on an H100, where the name is 1g.10gb. It passed profile IDs `0,1,2,3,4,5,6` to `-cgi`, and IDs are GPU-specific. It claimed layouts change while serving continues, which contradicts the drain in section 4. It claimed a hardware root of trust and a 2 to 4 times cost drop with no source. The removed groups are in the ledger.
  - new: The corrections were these. The Kueue YAML uses `cohortName` and only fields the CRD defines, and the CRD checker confirms that. MIG and time-slicing are in chapters 11.24 and 11.25. NVIDIA publishes no 5g.40gb profile, and the H100 resource name is `nvidia.com/mig-1g.10gb`. Profile IDs passed to `-cgi` are GPU-specific. A layout change needs the drain in section 4, so serving does not continue through it. The chapter makes no claim about a hardware root of trust or a cost drop with no source. The removed groups are in the ledger.

- 08-capstone-mig-multi-tenancy.md line 995
  - old: | Removed from the earlier draft as unsourced | 9 groups |
  - new: DELETED

- 08-capstone-mig-multi-tenancy.md line 994
  - old: | Corrected from the earlier draft | 8 |
  - new: DELETED

- 08-capstone-mig-multi-tenancy.md line 969
  - old: - The earlier draft cited files `finops_mig_dashboard.json`, `kueue_mig_queue.yaml` and `mig_workload.yaml` that never existed. They are replaced by the `c08_` files in `code/part19/`.
  - new: DELETED

- 09-capstone-capacity-planning.md line 1196
  - old: Claims checked: 22. Confirmed: 20, of which 14 were re-read in the book chapters named above and 6 were checked by tests against the chapter 20.12 and 20.16 code. Corrected: 2 errors from the earlier draft. It divided a daily GPU-hours figure by utilisation and called the result a GPU count, and it ran `capacity_plan.py` with flags that the script does not accept. Removed: 7 items that could not be sourced or run here, namely the multi-region failover section, the discount table, the reservation command, the Kubecost and Prometheus queries, the 80 percent accuracy alert, the `quarterly_review.py` command that does not exist, and the 300 thousand dollar waste figure. Still unverified: 6, listed under the inferences above. The code was run: 20 tests passed, and the worked example and both tables were regenerated from the files shown in the chapter.
  - new: Claims checked: 22. Confirmed: 20, of which 14 were re-read in the book chapters named above and 6 were checked by tests against the chapter 20.12 and 20.16 code. Corrected: 2 errors. A daily GPU-hours figure must not be divided by utilisation and called a GPU count, and `capacity_plan.py` must be run only with flags it accepts. Removed: 7 items that could not be sourced or run here, namely the multi-region failover section, the discount table, the reservation command, the Kubecost and Prometheus queries, the 80 percent accuracy alert, the `quarterly_review.py` command that does not exist, and the 300 thousand dollar waste figure. Still unverified: 6, listed under the inferences above. The code was run: 20 tests passed, and the worked example and both tables were regenerated from the files shown in the chapter.

- 09-capstone-capacity-planning.md line 1175
  - old: The earlier draft cited NVIDIA Zero-to-Hero Volume 24 (capacity planning capstone). I did not re-read that corpus for this rewrite, and no passage from it survives in the text. The earlier draft named Volume 24 without a file path, so I cannot give an exact `nvidia-devops` path and I claim none.
  - new: This chapter takes no passage from NVIDIA Zero-to-Hero Volume 24 (capacity planning capstone), and I claim no exact `nvidia-devops` path.

- 10-customer-workshops-and-the-consulting-method.md line 683
  - old: Claims checked: 41. Confirmed in the book chapters named above: 24. Corrected: 3 from the earlier draft, which invented a half-day agenda as fact, a 1 to 5 maturity score as standard and a "three perspectives" story. Removed: 9 earlier statements with no source, including the claims that a field engineering team runs this method as its playbook and the unsupported statements about sales and customer engineer roles. Still unverified and labelled: 5, listed under inferences above. Code: 37 tests pass in `test_c10_consulting.py`.
  - new: Claims checked: 41. Confirmed in the book chapters named above: 24. Corrected: 3, namely the half-day agenda is an example and not a fact, the 1 to 5 maturity score is an example and not a standard, and the "three perspectives" story is removed. Removed: 9 statements with no source, including the claims that a field engineering team runs this method as its playbook and the unsupported statements about sales and customer engineer roles. Still unverified and labelled: 5, listed under inferences above. Code: 37 tests pass in `test_c10_consulting.py`.

- 10-customer-workshops-and-the-consulting-method.md line 663
  - old: The earlier draft cited NVIDIA Zero-to-Hero Volumes 8, 10 and 22 with placeholder file names such as `chapter-XX-customer-workshops.md`. Those files were never given real paths in the draft. I did not re-read that corpus for this rewrite, and no passage from it survives. I claim no exact `nvidia-devops` path.
  - new: This chapter takes no passage from NVIDIA Zero-to-Hero Volumes 8, 10 and 22, and I claim no exact `nvidia-devops` path.

- 12-system-design-inference-serving.md line 674
  - old: - Removed: the old draft's multi-region failover and unsourced cost statements.
  - new: - Removed: multi-region failover and unsourced cost statements.

- 12-system-design-inference-serving.md line 673
  - old: - Corrected: 2. The old draft's KV-cache size and its GPU counts and throughput figure were replaced by estimator output.
  - new: - Corrected: 2. KV-cache size, GPU counts and the throughput figure come from estimator output.

- 12-system-design-inference-serving.md line 649
  - old: Migrated from `nvidia-devops`: the earlier draft cited Volume 23 `chapter-11-system-design-inference-serving.md` and Volume 8 `chapter-XX-system-design.md`. I did not re-read those files this session. The earlier draft's sizing figures (a 70B model at 5,000 tokens per second per GPU, 320 KB of KV cache per token) were removed because they were unsourced, and the KV figure was inconsistent with the estimator.
  - new: Migrated from `nvidia-devops`: no passage from Volume 23 or Volume 8 is used. I did not re-read those files this session. Sizing figures such as a 70B model at 5,000 tokens per second per GPU, and 320 KB of KV cache per token, are not used because they are unsourced and the KV figure is inconsistent with the estimator.

- 14-interview-question-bank-by-topic.md line 806
  - old: | Still unverified | answers linked to unremediated draft chapters, listed above |
  - new: | Still unverified | answers linked to chapters that have not been source-checked, listed above |

- 14-interview-question-bank-by-topic.md line 793
  - old: - Answers linked to Parts 16, 17, 18 and the 19.x drafts rely on chapters that have not yet been through the source check. Thresholds in them, such as the drift index values, are chapter examples and not universal.
  - new: - Answers linked to Parts 16, 17, 18 and some chapters of Part 19 rely on chapters that have not yet been through the source check. Thresholds in them, such as the drift index values, are chapter examples and not universal.

- 14-interview-question-bank-by-topic.md line 781
  - old: - The previous draft of this chapter cited `nvidia-zero-to-hero` volumes 26, 23, 9 and 8. Those files were not found in this repository, and no claim from them was kept.
  - new: DELETED

- 14-interview-question-bank-by-topic.md line 132
  - old: **In one minute:** There are 176 questions linked to 90 chapters. Topics map to parts of the handbook, and the weight you give each topic should follow the role. Volume 20 holds the Nebius drills, and entries linked to draft chapters are marked.
  - new: **In one minute:** There are 176 questions linked to 90 chapters. Topics map to parts of the handbook, and the weight you give each topic should follow the role. Volume 20 holds the Nebius drills.

- 14-interview-question-bank-by-topic.md line 128
  - old: Some topic chapters are still drafts. Parts 16, 17, 18 and the earlier drafts of Part 19 have not yet been through the same source check as the other parts. Entries linked to them carry a note in the `basis` field, and their thresholds should be read as chapter examples.
  - new: Some topic chapters have not yet been through the same source check as the other parts. Parts 16, 17 and 18 and some chapters of Part 19 are in that group. Entries linked to them carry a note in the `basis` field, and their thresholds should be read as chapter examples.

- 05-distributed-compute-for-ml-ray-kuberay-training-operator-and-katib.md line 388
  - old: # (An earlier draft called torch.distributed.elastic.agent.run(...), which is not how a training script is launched.)
  - new: # (Do not call torch.distributed.elastic.agent.run(...). That is not how a training script is launched.)

- 12-nvidia-enterprise-stack-ai-enterprise-ngc-and-licensing.md line 291
  - old: An earlier draft of this chapter used the API group `serving.nvidia.com` and invented fields such as `resources.gpu.type`. Neither is correct. The NIM Operator's group is `apps.nvidia.com`, and the model weights come from a separate NIMCache resource that the NIMService names. The Operator reads both resources and builds a Deployment with the right GPU binding, pull secret, model storage, and service.
  - new: The NIM Operator's API group is `apps.nvidia.com`, not `serving.nvidia.com`, and the manifest has no `resources.gpu.type` field. The model weights come from a separate NIMCache resource that the NIMService names. The Operator reads both resources and builds a Deployment with the right GPU binding, pull secret, model storage, and service.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 693
  - old: A single double-bit error is critical, and the draft calls for replacing the GPU. Single-bit errors are warnings, and the GPU is scheduled for replacement once the rate stays high. The 100 per hour figure is an example. The strict rule pulls a GPU out of service early, which costs capacity.
  - new: A single double-bit error is critical, and the example calls for replacing the GPU. Single-bit errors are warnings, and the GPU is scheduled for replacement once the rate stays high. The 100 per hour figure is an example. The strict rule pulls a GPU out of service early, which costs capacity.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 689
  - old: The chapter's draft alerts on every Xid error and gives severity critical. Before doing that, the runbook must say what to do for each code, because each code points to a class of problem. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement.
  - new: The chapter's example alerts on every Xid error and gives severity critical. Before doing that, the runbook must say what to do for each code, because each code points to a class of problem. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 633
  - old: 1. **Add a GPU temperature dashboard.** Build a Grafana dashboard that shows temperature for each GPU. Alert when temperature passes a limit you choose. The draft's example is 85 degrees. *Solution sketch:* start from `DCGM_FI_DEV_GPU_TEMP_CELSIUS`, add a Grafana panel, and write the alert rule.
  - new: 1. **Add a GPU temperature dashboard.** Build a Grafana dashboard that shows temperature for each GPU. Alert when temperature passes a limit you choose. The chapter's example is 85 degrees. *Solution sketch:* start from `DCGM_FI_DEV_GPU_TEMP_CELSIUS`, add a Grafana panel, and write the alert rule.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 433
  - old: Four pieces make up this stack, and each one can fail on its own. The table shows where each piece runs and the service target the draft uses for it.
  - new: Four pieces make up this stack, and each one can fail on its own. The table shows where each piece runs and the example service target for it.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 331
  - old: The 1400 threshold in the example is a base-clock value for one model. Confirm your model's base clock before you use it. The draft alerts when the clock stays below base for 10 minutes, and that duration is an example too.
  - new: The 1400 threshold in the example is a base-clock value for one model. Confirm your model's base clock before you use it. The example alerts when the clock stays below base for 10 minutes, and that duration is an example too.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 314
  - old: The draft's example lines are 85 degrees for a warning, 90 for throttling and 95 for critical. They are example values, not manufacturer limits, so check your GPU's documented thresholds first. The draft also says power draw above the rated TDP for your GPU model points to power supply problems.
  - new: The example lines are 85 degrees for a warning, 90 for throttling and 95 for critical. They are example values, not manufacturer limits, so check your GPU's documented thresholds first. The example also says power draw above the rated TDP for your GPU model points to power supply problems.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 297
  - old: The draft alerts on every Xid error. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement. Whatever you alert on, the runbook should say what to do for each code.
  - new: The example alerts on every Xid error. Its common codes are 31 for a GPU memory page fault, 43 for a GPU that stopped responding, 48 for a double-bit ECC error and 63 for ECC page retirement. Whatever you alert on, the runbook should say what to do for each code.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 283
  - old: The draft treats a single double-bit error as critical and calls for replacing the GPU. It warns on single-bit errors and says the GPU should be scheduled for replacement once that rate stays high. The example rate in the draft is 100 per hour, so treat it as a starting value.
  - new: The example treats a single double-bit error as critical and calls for replacing the GPU. It warns on single-bit errors and says the GPU should be scheduled for replacement once that rate stays high. The example rate is 100 per hour, so treat it as a starting value.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 244
  - old: The draft's example values are 30 percent for under-use, 90 percent for over-use, and an alert when utilisation stays above 95 percent for 10 minutes. These are examples. Choose your own numbers for your workload.
  - new: The example values are 30 percent for under-use, 90 percent for over-use, and an alert when utilisation stays above 95 percent for 10 minutes. These are examples. Choose your own numbers for your workload.

- 04-dcgm-exporter-and-interpreting-gpu-metrics.md line 139
  - old: The field names were checked against the dcgm-exporter source, and that check turned up three points. `DCGM_FI_PROF_SM_UTIL_RATIO` (called `DCGM_FI_PROF_SM_ACTIVE` before 4.9.0, a naming link that is inferred, see 1.4) reports a ratio from 0 to 1, not a percentage, and is commented out in the default counters file. The retired-page family is `DCGM_FI_DEV_PAGE_RETIRED_PENDING`, `DCGM_FI_DEV_PAGE_RETIRED_DBE_TOTAL` and `DCGM_FI_DEV_PAGE_RETIRED_SBE_TOTAL`, also inferred and commented out by default. ECC counters end in `_TOTAL`, because an earlier draft used `_DEDUP` names that the exporter does not define.
  - new: The field names were checked against the dcgm-exporter source, and that check turned up three points. `DCGM_FI_PROF_SM_UTIL_RATIO` (called `DCGM_FI_PROF_SM_ACTIVE` before 4.9.0, a naming link that is inferred, see 1.4) reports a ratio from 0 to 1, not a percentage, and is commented out in the default counters file. The retired-page family is `DCGM_FI_DEV_PAGE_RETIRED_PENDING`, `DCGM_FI_DEV_PAGE_RETIRED_DBE_TOTAL` and `DCGM_FI_DEV_PAGE_RETIRED_SBE_TOTAL`, also inferred and commented out by default. ECC counters end in `_TOTAL`. The exporter does not define `_DEDUP` names.

- 07-capstone-an-observability-platform.md line 823
  - old: None. The earlier draft of this chapter cited `nvidia-devops` Volume 24 Project 4 and Volume 8 Chapter 4. Nothing was carried over from them. They were not re-read for this rewrite, and the chapter was rebuilt from the books, the upstream documents and the code. The corpus name `nvidia-devops` appears here for the lab checker only.
  - new: None. This chapter was built from the books, the upstream documents and the code, and no passage from `nvidia-devops` Volume 24 or Volume 8 is used. The corpus name `nvidia-devops` appears here for the lab checker only.

- 11-system-design-a-training-cluster.md line 606
  - old: The old draft's H100 16-GPU sizing, 250 samples per GPU, dragonfly+ and RAID-6 claims were removed. Its cited files `choose_scheduler.py`, `design_review.py`, `design_storage.py`, `select_topology.py` and `size_gpu_pool.py` did not exist and now exist with the `c11_` prefix.
  - new: The scripts `choose_scheduler.py`, `design_review.py`, `design_storage.py`, `select_topology.py` and `size_gpu_pool.py` exist with the `c11_` prefix. No H100 16-GPU sizing, per-GPU sample rate, dragonfly+ or RAID-6 claim is made, because none is sourced.

- 11-system-design-a-training-cluster.md line 246
  - old: Tiering follows from the arithmetic. A parallel file system with RDMA serves the training reads and the shared checkpoints. The GB300 document requires file storage with RDMA support, linear scaling and non-disruptive upgrades. A second tier of object storage holds older checkpoints and the raw dataset. Local NVMe on each node, four 3.84 TB drives in the GB300 compute tray, is useful for scratch and a fast first checkpoint copy. The old draft of this chapter, and NVIDIA Zero-to-Hero volume 23, describe a two-step checkpoint to local NVMe and then to remote storage. That is not verified against a vendor source, so it is presented as reasoning and not as a standard.
  - new: Tiering follows from the arithmetic. A parallel file system with RDMA serves the training reads and the shared checkpoints. The GB300 document requires file storage with RDMA support, linear scaling and non-disruptive upgrades. A second tier of object storage holds older checkpoints and the raw dataset. Local NVMe on each node, four 3.84 TB drives in the GB300 compute tray, is useful for scratch and a fast first checkpoint copy. A two-step checkpoint to local NVMe and then to remote storage is a common pattern, but it is not verified against a vendor source, so it is presented as reasoning and not as a standard.

- 13-system-design-research-infrastructure.md line 760
  - old: | Corrected from the old draft | 6 (MLflow env var names, missing DB and S3 drivers in the image, `latest` notebook image, hand-written JupyterHub Deployment, missing values for the helm install, files that did not exist) |
  - new: DELETED

- 13-system-design-research-infrastructure.md line 735
  - old: The old draft cited NVIDIA Zero-to-Hero Volume 23 `chapter-12-system-design-research-infrastructure.md` and Volume 8. I did not open those files in this rewrite, and no text was migrated from `nvidia-devops`. The structure and every claim here come from the books and upstream sources above.
  - new: No text was migrated from `nvidia-devops` Volume 23 `chapter-12-system-design-research-infrastructure.md` or Volume 8, and I did not open those files in this chapter. The structure and every claim here come from the books and upstream sources above.

- 13-system-design-research-infrastructure.md line 351
  - old: MLflow needs two stores. The backend store holds run metadata and should be PostgreSQL for a shared team. The artifact store holds files and should be object storage. The recommended shape is the tracking server as a proxy: with `--serve-artifacts` the server forwards uploads to the bucket named by `--artifacts-destination`. Researchers then need no bucket credentials. I read the `mlflow server` options in `mlflow/cli/__init__.py` at v3.18.0. The old draft used environment variables named `BACKEND_STORE_URI` and `DEFAULT_ARTIFACT_ROOT`, which do not match the CLI. The real names are `MLFLOW_BACKEND_STORE_URI` and `MLFLOW_DEFAULT_ARTIFACT_ROOT`.
  - new: MLflow needs two stores. The backend store holds run metadata and should be PostgreSQL for a shared team. The artifact store holds files and should be object storage. The recommended shape is the tracking server as a proxy: with `--serve-artifacts` the server forwards uploads to the bucket named by `--artifacts-destination`. Researchers then need no bucket credentials. I read the `mlflow server` options in `mlflow/cli/__init__.py` at v3.18.0. The environment variable names are `MLFLOW_BACKEND_STORE_URI` and `MLFLOW_DEFAULT_ARTIFACT_ROOT`, not `BACKEND_STORE_URI` and `DEFAULT_ARTIFACT_ROOT`.

- 13-system-design-research-infrastructure.md line 136
  - old: Zero to JupyterHub for Kubernetes, the Helm chart `jupyterhub`, is the standard way to run JupyterHub on Kubernetes. This chapter uses chart 4.4.5, which packages JupyterHub 5.5.5, fetched 2026-11-10. The chart already wires the hub, proxy and user scheduler together, so I did not write a Deployment by hand as the old draft did.
  - new: Zero to JupyterHub for Kubernetes, the Helm chart `jupyterhub`, is the standard way to run JupyterHub on Kubernetes. This chapter uses chart 4.4.5, which packages JupyterHub 5.5.5, fetched 2026-11-10. The chart already wires the hub, proxy and user scheduler together, so there is no hand-written Deployment.

- 15-interview-cheat-sheet.md line 618
  - old: | Rows resting only on a drafted chapter from Parts 5 to 15 | 19 |
  - new: | Rows resting only on a chapter from Parts 5 to 15 | 19 |

- 15-interview-cheat-sheet.md line 606
  - old: - The anchors prove presence in a chapter, not truth. Part 5 to 15 chapters were drafted earlier and not re-audited here, and 19 rows rest on them. I checked the PCIe, HBM and NVLink 5 figures against *AI Systems Performance Engineering* ch. 2. The Hopper NVLink figure of 900 GB/s, the DGX memory totals and the 989 TFLOPS figure rest on chapters 9.1 and 9.2 alone.
  - new: - The anchors prove presence in a chapter, not truth. Part 5 to 15 chapters were not re-audited here, and 19 rows rest on them. I checked the PCIe, HBM and NVLink 5 figures against *AI Systems Performance Engineering* ch. 2. The Hopper NVLink figure of 900 GB/s, the DGX memory totals and the 989 TFLOPS figure rest on chapters 9.1 and 9.2 alone.

- 15-interview-cheat-sheet.md line 594
  - old: The earlier draft cited Volume 26, `chapter-XX-interview-cheat-sheet.md`. No such file was found, and none of its wording is kept. The material used from the corpus is the gem-book chapter `nvidia-devops-core-interview` (Chapter 01, "Consolidated Core Interview Questions") in `~/Desktop/books-toon-rag`, used as a cross-check as described above.
  - new: No text is taken from `nvidia-devops` Volume 26. The material used from the corpus is the gem-book chapter `nvidia-devops-core-interview` (Chapter 01, "Consolidated Core Interview Questions") in `~/Desktop/books-toon-rag`, used as a cross-check as described above.


Notes: 'validator' mentions kept where they name a real tool (19.4 jobset validation step, 19.8 mig-parted validator). 17.14 and 17.16 'draft' refers to a generated runbook or post-mortem, not drafting history, and was kept. Part 17.4 'the draft' sentences were rewritten to 'the example'; check that rewrite worker for 17.4 has not reverted them.
