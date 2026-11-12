# Rework ledger X3 (chapters 17.4, 17.6, 17.7, 17.10, 17.13, 17.16)

Gates run 2026-11-12: pytest code/part17 (40 passed, 1 skipped), check_code_files code/part17 (0 problems), promtool check rules and test rules on gpu_alerts.yaml / gpu_alerts_test.yml (13 rules, tests pass), amtool check-config alertmanager.yaml (ok). All six chapters: chain_gate under 0.1, 20 summaries each, no language_audit row.

## 17.4 DCGM exporter
- Rebuilt the body around fault signals; opener now states "page on fault signals, not load signals". Replaced code/part17/gpu_alerts.yaml (13 rules: row remap failed/uncorrectable, DBE, SBE week-over-week growth, Xid tier 3 and tier 2 with changes(), thermal and power throttle counters, NVLink CRC, PCIe replay, exporter absent fleet-wide, exporter missing on GPU node, GPU count mismatch). Removed GPUHighUtilization, GPUMemoryPressure, GPUClockThrottle, GPUThermalThrottle(temp). 4.9.0 and 4.8.x legs kept with `or`.
- Rewrote code/part17/gpu_alerts_test.yml (promtool tests, both name generations, stale-Xid not alerting). Updated inhibit_rules.yaml (GPUXidTier[23]) and README line. Rename mapping/JSON untouched; fixed two table rows that disagreed with the JSON (PCIE_REPLAY_COUNTER and XID_ERRORS were shown as unchanged old names).
- Lab now PrometheusRule + `dcgmi test --inject --gpuid 0 -f 202 -v 99999` (syntax confirmed from NVIDIA DCGM Error Injection page, fetched 2026-11-12; page does not say which host engine receives the injection, so the lab states the same-host-engine condition).
- Watch list: alert rules wrong in judgement: fixed. "H100 base clock 1.4 GHz": removed, no rule depends on it. Xid gauge never clears: fixed with changes() (limit stated: same code twice in a row unseen; DCGM_EXP_XID_ERRORS_COUNT suggested, name from default-counters.csv). Cardinality row (12 x 8 x 1000): removed, replaced by "count it yourself". 4.9.0 release itself: dates already sourced by FA/JSON, unchanged. "the draft" x8: removed. FA fixes in this file were preserved (re-read from disk before saving; "I could confirm" had already been rewritten).
- Unresolved: the 10 percent thermal, 50 PCIe replays per hour, 100 NVLink CRC per hour thresholds are starting values, labelled as such. SBE growth rule is syntax-checked only.

## 17.6 Alerting, SLOs
- Added 1.4 multi-window burn-rate alerting with worked numbers for a token API (100 req/s, 259,200,000 requests, 259,200 failures budget, 14.4/6/1 table, firing times), consistent with 20.19 and code/part20 slo_burn_alerts_availability.yaml; links 20.19 as owner. Replaced memory-pressure runbook and alert example with GPUXidTier3; fixed inhibit snippet to match code/part17/inhibit_rules.yaml; removed stale 4.9.0 note and fake "50-200 alerts per day" block.
- Verified: 14.4*1/720 = 2%, 6*6/720 = 5%, 1*72/720 = 10%; 5,184 failed requests = 2% of 259,200.

## 17.7 Failure modes
- Removed "Read the diagram" paragraph and fake 30-50 failure mode block. All six tables converted to symptom / detect / first action with real signals (DCGM 4.9.0 names, kube-state-metrics, CoreDNS, PyTorch watchdog message). Object store and serving metric names that do not exist as standards are labelled illustrative.
- Error fixed: OOMKilled was described as GPU OOM; it is host memory (cgroup). New 4.2 separates it from CUDA out of memory. 1.2 storm policy now matches 17.4 (week-over-week SBE growth, not 100 per hour). Meta figures now "of 419 unexpected interruptions" with 148/419 = 35.3 percent.
- Lab step 4 uses dcgmi test --inject.

## 17.10 Lifecycle and upgrades
- Rebuilt around a GPU driver upgrade with the GPU Operator. Removed the software-engineering textbook sections (software needs more than code, Lehman laws, maintenance types, ant colony scheduling, re-engineering, component reuse, system software), about 2,500 words. Added what a GPU upgrade touches, drain policy (ClusterPolicy upgradePolicy fields), canary pool and stage table with pass conditions, window arithmetic, rollback triggers/procedure/evidence.
- Sourced from NVIDIA GPU Operator "GPU driver upgrades" page (fetched 2026-11-12): fields, state label and states, skip label, autoUpgrade, kubectl patch of spec.driver.version. Unresolved: rollback is not documented there; section 6.2 labelled as inference to test in staging. Invented bug ID NV 4123456 and driver versions 550.54.x removed; 580.95.05 is NVIDIA's example version. `apt-get` rollback via kubectl exec removed (wrong for Operator-managed drivers).
- Not verified: GKE surge-upgrade behaviour for GPU pools (hedged in text).

## 17.13 Reliability
- Added 1.4 GPU fleet numbers from the Llama 3 405B table, corrected 148/419 = 35.3 percent (book prints 30.1; only that row mismatches its 419 base; other rows verified: 72=17.2, 54=12.9, 35=8.4, 32=7.6, 19=4.5, 17=4.1, 7=1.7; counts sum to 419). Derived: one interruption per 3.1 h, GPU rows 268/419 = 64 percent, about 11 percent per GPU per year (lower bound, GPU count in snapshot not stated; paper says up to 16K H100), more than 90 percent effective training time (paper). Spare pool sizing with Poisson arrivals (0.5 nodes/day for 1,024 GPUs; 2 and 3 spares for 98 and 99.5 percent at 1-day repair; 3 and 4 at 2-day), pool availability 99.6 vs 99.2 percent. GPU-fleet error-budget policy rules. N+1 corrected to node-level spares. Burn-rate lines now point to 17.6.
- Unresolved: scaling Meta's rate to other fleets assumes comparable hardware; stated in text.

## 17.16 AI-assisted ops
- Rewrote around concrete patterns: DCGM anomaly detection with peer comparison and a false-positive budget (20,160,000 checks/week; 5 FPs/week = about 2.5e-7 rate; three-sigma gives about 54,000), alert summarisation with guardrails, runbook assistant failure modes, Prometheus cardinality (metric names prometheus_tsdb_head_series and prometheus_tsdb_head_series_created_total), fleet automation with a common-cause breaker. Code blocks equal to code files untouched.
- REMOVED sections 5.5 to 5.14 (scheduling agents, compilers, AlphaTensor, DeepSeek-R1 kernel, Triton RL, 100T hardware, precision, memory tiers, self-improving agents, perf per watt), about 4,000 words, off topic. Full text saved to planning/ledgers/removed_17-16_ai_for_performance_outlook.md; restore or relocate if the owner wants it. Checkpoint Qs 11, 15, 18 replaced to match.
- Unresolved: the PromQL peer-median expression is promtool-parsed only; the 2 percent / 10 minute breaker numbers are examples.

## Neighbouring chapters noticed
- 17.15 and 17.7 lab commands reference `configs/gpu_alerts.yaml`; 17.6 lab (7.4) still creates a ConfigMap from that path. Not edited.
- 19.7 still says 17.4 uses pre-4.9.0 names; 17.4 now carries both name legs.
- code/part19/c07_stack_rules.yaml has its own GPUXidError rule (`> 0` never clears); outside my scope.
