# Rework ledger W1 (chapters 0.1, 5.9, 5.32, 3.6)

## 0.1 (docs/part-00-orientation/01-*)
- Rewrote: deleted all manufacturing, lambda, Industry 4.0 and policy sections. Kept opening, layer diagram and table, roles table, common failure, 4 checkpoint questions (form kept). Added: What a GPU server is, A training job end to end, An inference request end to end, What goes wrong at scale. About 1,950 words including tables (target 2,500; kept to what can be sourced).
- Watch list: "IBM AC922 4,608 servers" removed with the section (fixed).
- Unresolved: Llama 3 figures (466 interruptions in 54 days, 419 unexpected, about 78 percent hardware, 16,384 H100) quoted from memory of arXiv 2407.21783, not re-fetched. Please verify.
- Gates: chain_gate pass, no language_audit row, 4 summaries.

## 5.9 (kubelet)
- Replaced the pasted probe subsections with a startup-probe YAML (300 s load) and a compact endpoint-design subsection; removed all book leaks and docker:// event text.
- Eviction sampling: fixed (housekeeping cycle about 10 s; evictionPressureTransitionPeriod default 5m is the wait before clearing pressure). Source: Kubernetes node-pressure eviction docs (from memory, not re-fetched).
- OOMKilled exit code: fixed to 137 with explanation.
- Failure-count sentences: fixed ("more than three" and "last 10 probes" removed).
- node-monitor-grace-period: stated as 40 s older, 50 s recent, version-dependent. UNRESOLVED against a specific release.
- Not added (unsourced): DRA and MemoryQoS status. Inline "untested here" removed. 20 details unchanged. Gates pass.

## 5.32 (GPU node health operator)
- Design contradiction fixed: absent condition is now neither healthy nor unhealthy (like Unknown). Changed consistently in evaluate.go, evaluate_test.go, gpu_health_operator_sim.py, gpu_health_operator_sim_lab.py, chapter block, decision table, prose, failure table, interview answers 3 and the release-condition answer. Sim lab passes 3/3, check_code_files part05 clean, go vet clean. The Go unit test was NOT run (envtest TestMain fails without kubebuilder assets): please run go test for evaluate_test.go.
- Replaced volume-10 subsection with plain "Where this operator fits" paragraph (Parts 10, 11, operations part). Fixed "(5.22)" to "(5.27)", LaTeX removed, six-versus-eight count explained, inline untested tags removed.
- Not done: circuit breaker stays an extension; leader-election RequeueAfter not discussed. Beginner paragraph on node conditions not added.

## 3.6 (Python concurrency)
- Replaced spinner and book narrative with a runnable hash experiment (checked locally: sequential 2.78 s, threads 2.70 s, 4 processes 0.81 s on my run; chapter gives no numbers). Removed laptop timings, Example numbers, book refs in body, checkpoints and lab.
- forkserver: fixed (3.14 Linux default is forkserver; macOS/Windows spawn). Thread-safety paragraph: fixed (boto3 low-level client only; paramiko, DB-API threadsafety, sqlite3). aiohttp: import added and ClientTimeout used (checked from memory, not against pinned version). retry: random import added.
- Exercises cut from 11 to 6 infrastructure fan-out tasks. Checkpoint questions 3, 6, 8, 12, 14, 16 reworded without book/demo names. Sources rewritten.
- Not added: free-threaded dependency status, uvloop/anyio, event-loop tick picture.

## Neighbours noticed
- 5.9 section 8 cross-reference "Part 17" for remediation controllers is unverified; 5.32 now avoids a Part 17 claim.
- Status tables at chapter top left as instructed.
