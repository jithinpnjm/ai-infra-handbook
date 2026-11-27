---
id: "c20-18"
title: "20.18 How LLM serving fails"
sidebar_label: "20.18 How LLM serving fails"
sidebar_position: 18
description: "A failure catalogue for an inference SRE: queue growth, KV-cache exhaustion and preemption, head-of-line blocking, OOM, NCCL hangs and Xid errors, cold start, thundering herd, probe mistakes, retry amplification, quality drift and version skew, each with symptom, confirmation, mitigation and fix, plus a decision tree and a tested failure-signature classifier."
status: "drafted"
tier: "1"
level: "I"
lab_venue: "Laptop / Docker"
---

# 20.18 How LLM serving fails

## What the interviewer is testing

An alert fires at 02:10. Time to first token (TTFT) is five times its normal value, and the pager says nothing else. That silence is typical, because most serving alerts describe a symptom and not a cause. This chapter serves the 30-minute production-incident round, and it also feeds the system design round, where you must say how your design fails. The job posting asks for knowledge of "how distributed back-ends fail" and for debugging "from kernel to application layer". It also lists incident detection, isolation and remediation with automation and runbooks. A runbook is the written list of steps an on-call engineer follows when an alert fires.

One candidate reported that this round asks you to solve a production incident in 30 minutes. Nebius has not published the incidents it uses. So the skill being tested is a method, and the method has three moves in order: name the failure from a few signals, protect users first, and only then dig for root cause. An interviewer who hears you jump to the cause before the protection will mark that down, even if your guess is right.

Imagine the interviewer's question arriving while the dashboard is still open on a second screen. A realistic question in the interviewer's voice: "Your vLLM endpoint's p99 time to first token tripled in ten minutes. GPU utilisation looks fine. Walk me through what you check and what you do before you know the cause."

## The core ideas

### 1. Every failure is a story about three places where a request can wait

![A request waits in the engine's queue, runs in the batch and holds KV cache, and the metrics for each place show which one is full.](./img/p2-2018-three-waits.svg)

*Figure 20.18.1. A request waits in the queue, runs in the batch and holds KV cache, and each place has a vLLM metric that shows whether it is full.*

A request enters the engine and sits in the waiting queue. Think of the queue as the line outside a busy kitchen. The scheduler moves it into the running batch when there is room, which is the set of requests the GPU is cooking together right now. While it runs, its keys and values occupy the KV cache, which is GPU memory reserved for per-token attention state. The attention state is what the model needs to remember about the words it has already seen. Nearly every serving failure is one of these three places filling up, stalling or lying about itself.

vLLM exports all three as Prometheus metrics on `/metrics`. Prometheus is the metrics database most teams use, and it reads these values on a schedule. The waiting queue is `vllm:num_requests_waiting`. The running batch is `vllm:num_requests_running`. The cache is `vllm:kv_cache_usage_perc`, where 1 means 100 percent. Counters such as `vllm:num_preemptions` appear with a `_total` suffix on the wire, so in PromQL you write `vllm:num_preemptions_total`. PromQL is the query language for Prometheus. That detail comes from the metrics design page and it catches people who copy a name from the source code.

The latency metrics split the request's life the same way. `vllm:request_queue_time_seconds` is time spent waiting. `vllm:time_to_first_token_seconds` is TTFT, and `vllm:inter_token_latency_seconds` is the gap between streamed outputs. The gap between streamed outputs is what a user feels as smoothness. If you know which of the three places is full, you already know which family of failure you have, and you can say so in the first minute of the round.

![Every failure is a story about three places where a request can wait](./img/m20-18-1.svg)

*Figure 20.18.2. Every failure is a story about three places where a request can wait, as a diagram.*

Before you touch anything in an incident, read these three numbers and the token rate. Look at them as a set, because one number alone can mislead you. **Name the place that is full before you name a cause.**

### 2. Queue growth and TTFT spikes

![A queue growth pattern where waiting requests rise, the batch sits at its limit and KV usage stays below 90 percent, which means the fix is replicas, not memory.](./img/p2-2018-queue-triage.svg)

*Figure 20.18.3. When waiting requests rise while KV usage stays below about 90 percent, the engine is short of replicas, not memory.*

A user writes that the app hangs before it starts answering, and the chat window shows a spinner. Symptom. TTFT and end-to-end latency climb together, error rate stays low at first, and users say "it hangs before it starts answering". The engine is working at full speed, but new requests wait for a slot. A slot is a place in the running batch, and a full batch has no free slot for the newcomer.

Confirm. `vllm:num_requests_waiting` rises, `vllm:num_requests_running` sits at the batch limit, and `vllm:kv_cache_usage_perc` is below about 90 percent. The p99 of `vllm:request_queue_time_seconds` explains most of the TTFT increase. Token throughput is flat or high, which separates this from a hang. The pattern to remember is simple: the queue is long, the batch is full, and the memory still has room. That combination means you are short of replicas, not short of memory.

Mitigate now. Add replicas if you have spare GPUs, or shed load at the router. Shedding means refusing some requests on purpose, so the rest stay fast. vLLM can do the shedding itself. The setting `max_num_queued_reqs` rejects new requests with HTTP 503 once the in-flight limit is reached, so the client can retry on another instance. HTTP 503 means the service is temporarily unavailable, and it tells the client to try again later. The setting `max_num_queued_tokens` bounds the prefill backlog, and the source comment gives the sizing rule as target TTFT times prefill throughput. Rejections show up as `vllm:admission_rejections_total` with a reason label, so you can count them on a graph.

Fix later. Autoscale on queue depth and queue time instead of GPU utilisation. A saturated batch can show high utilisation both when it is healthy and when it is drowning, so utilisation cannot tell the two apart. The book Distributed AI Systems, chapter 9, recommends a bounded queue that returns 503 immediately rather than letting requests time out after a long wait. A bounded queue is a queue with a maximum length, so the wait itself has a ceiling. Keep 10 to 15 percent spare capacity in steady state, as AI Systems Performance Engineering, chapter 16, recommends, because autoscaling takes minutes to provision a GPU. Spare capacity is the cushion that covers the minutes you cannot buy back.

Decide: if waiting is high and KV usage is low, you are short of replicas, not memory. Say that sentence in the room, because it tells the interviewer you can tell the two apart from the numbers.

### 3. KV-cache exhaustion and preemption

![On a 24 GB GPU with 14 GB of weights, 10 GB remains for cache, enough for about five requests of 4,096 tokens, so a burst of 16 cannot all run.](./img/x18-kv-budget.svg)

*Figure 20.18.4. The KV cache is a fixed pool left after the weights, so a burst of long requests fills it and forces preemption.*

Imagine a long answer that stops in the middle, waits for a moment, and then carries on. The user thinks the app froze. Symptom. Latency becomes uneven. Some requests stall mid-answer, then continue. Throughput drops even though demand is unchanged, because the engine redoes work.

The mechanism. Every running request needs KV space that grows with each token. The cache is a fixed pool, so when space runs out, vLLM preempts a request, which means it pauses that request and gives up its cache space. It frees the cache and recomputes the request later. The vLLM optimisation page says V1 defaults to recompute mode, since recomputation is cheaper than swapping in that architecture. Swapping would move the cache to host memory and back, and recomputation simply redoes the work on the GPU. Recomputation burns GPU time and puts the victim back at the front of the queue, which hurts both its latency and everyone else's.

A worked example uses the book numbers, and the walkthrough is worth doing by hand once. Hands-On LLM Serving and Optimization, chapter 5, gives KV size per token as two times layers times heads times head dimension times bytes. For Llama-2-7B in FP16 that is 2 x 32 x 32 x 128 x 2 bytes, which is 0.5 MB per token. A 24 GB GPU holding 14 GB of weights leaves 10 GB. That is 10 x 1024 / 0.5 = 20,480 tokens of cache, or about five requests that each reach 4,096 tokens. A burst of 16 such requests cannot all run. Notice that the answer comes from memory left after the weights, not from the model's size alone.

Confirm. `vllm:kv_cache_usage_perc` is near 1 and `rate(vllm:num_preemptions_total[5m])` is above zero. Read the second part as a check that preemption is actually happening now, not only that it happened once. The per-request histogram `vllm:request_num_preemptions` shows how many requests are hit. The vLLM docs show a warning line saying a sequence group was preempted by recompute mode because there is not enough KV cache space. That sample comes from an older scheduler file name, so grep your own logs for the word preempted instead of the exact text.

Mitigate now. The vLLM docs list four levers. Raise `gpu_memory_utilization`, lower `max_num_seqs` or `max_num_batched_tokens`, raise tensor parallel size, or raise pipeline parallel size. Tensor parallel size splits one model across GPUs in a layer, and pipeline parallel size splits it across stages. Lowering batch limits is the fastest, because it needs only a restart and trades throughput for stability. In an incident, stability is the goal, so that trade is usually the right first move.

Fix later. Size the cache from expected context length, not from the model size. Context length is how many tokens a request can hold at once, and a short-context model with long requests can still run out. The source for v0.32.0 shows a default `gpu_memory_utilization` of 0.92, while the book still says about 0.85, so check the version you run. Consider KV-cache quantisation, covered in section 11. Quantisation stores numbers with fewer bits, which saves memory at some cost to quality.

Decide: preemptions above zero mean you are over-admitting, so reduce admission before you add anything else.

### 4. Long-context head-of-line blocking

![One tenant's long prefill blocks short requests in the shared batch, so inter-token latency rises even with a short queue and moderate KV usage.](./img/p2-2018-long-prompt-block.svg)

*Figure 20.18.5. A long prefill from one tenant blocks short requests in the shared batch, so the fix is to isolate long prompts rather than add replicas.*

A tenant starts sending very long documents on a Tuesday, and suddenly the short chat prompts from other customers feel sluggish. Symptom. Short prompts suddenly see slow streaming. Inter-token latency p99 rises although the queue is short and KV usage is moderate. One tenant has started sending very long documents.

The mechanism. Prefill of a long prompt is a large compute job, and it runs before the first token appears. Head-of-line blocking is the general name for a line where one slow item blocks everything behind it. In vLLM V1, chunked prefill is on by default, and the scheduler batches all pending decodes first and then fills the remaining token budget with prefill chunks. Decoding is the step that writes one new token at a time for each running request. This protects decodes, but a very large `max_num_batched_tokens` lets one prefill take most of each step. The docs say smaller values give better inter-token latency and larger values give better TTFT. So the setting is a trade between two users' experiences, and the incident is about picking the side that protects the most customers.

Confirm. Compare `vllm:request_prompt_tokens` p99 against p50. The p50 is the median prompt length and the p99 is the long tail. A tail that is eight or more times the median is a warning sign. In the classifier this ratio is a starting value I chose, not a vendor number. Also check that preemption is flat, which rules out section 3. If preemption is flat and the tail is long, the evidence points at one long prompt, not at memory pressure.

Mitigate now. Lower `max_num_batched_tokens`, or route long prompts to a separate pool. A pool is a group of replicas dedicated to one kind of traffic. The scheduler also has `long_prefill_token_threshold`, which the source describes as the length above which a prompt counts as long for chunked prefill, so that long prompts cannot starve others. Its default is 0, which disables the cap. That means the protection is off until you turn it on, so check it in the config before you claim it is active.

Fix later. Separate prefill and decode pools, as the Nebius case study did [vendor], and add per-tenant context-length limits. A split pool lets long prefills happen where they cannot hurt short decodes. AI Systems Performance Engineering, chapter 16, lists "decode-node hotspot or head-of-line blocking" and recommends inspecting router logs and enabling speculative decoding paths. Treat the speculative-decoding suggestion with care, for reasons in section 11.

Decide: if tail latency rises with the prompt-length tail, isolate long prompts rather than adding replicas to the shared pool.

### 5. GPU OOM at startup versus at load

![A GPU out-of-memory failure is split by time: at startup during weight loading, profiling and CUDA graph capture, or at runtime under traffic spikes.](./img/p2-2018-startup-or-runtime.svg)

*Figure 20.18.6. A GPU out-of-memory failure at startup points to sizing settings, while one at runtime under peak traffic points to the traffic and prompt lengths.*

A deploy goes out on a Friday afternoon, and the new pods never become ready. The events list shows restart after restart. Symptom, startup form. The container exits before it ever listens, and Kubernetes restarts it in a loop. Symptom, runtime form. The process dies hours later, under peak traffic, and a pod that was serving disappears.

The two have different causes, so the first question is when it died. At startup vLLM loads weights, runs a profiling pass and may capture CUDA graphs. A CUDA graph is a recorded set of GPU work that can be replayed quickly. The worker code in v0.32.0 prints a message that lists free memory, weights, peak activation and CUDA graph memory, and suggests a `--kv-cache-memory` value. Startup OOM means the sum of those parts does not fit in the requested fraction of the GPU. OOM means out of memory, and the sum is the budget the engine tries to fit. A co-tenant holding GPU memory is a common reason. A co-tenant is another process sharing the same GPU. The vLLM docs also warn that a stored `--kv-cache-memory` value is valid only on the same GPU with the same initial free memory.

Runtime OOM is different. The cache was sized correctly at startup, but a spike in activations, longer prompts or memory fragmentation consumed the headroom. Activations are the temporary tensors the model creates while it works, and fragmentation is memory that is free but split into pieces too small to use. AI Systems Performance Engineering, chapter 16, warns that repeated OOM crashes under peak load take GPUs out of the pool and cause cascading latency. Each crash removes capacity at the worst moment, so the survivors slow down and fail as well.

Confirm. Read the log around the exit, and read `kubectl describe pod` for the last state. The last state tells you the exit code and the reason, which is the first clue to startup or runtime. Check `nvidia-smi` for other processes on the GPU. Compare `vllm:prompt_tokens` rate before the crash, because a sudden rise in prompt length is the usual runtime trigger.

Mitigate now. For startup, lower `gpu_memory_utilization` or `max_model_len`, or free the GPU. The first lowers how much of the GPU the engine claims, and the second caps how long a request may be. For runtime, lower `max_num_batched_tokens` and cap prompt length at the gateway. Fix later by reserving activation headroom, one replica per GPU, and a startup test in CI that loads the exact config. A startup test in CI catches a bad config before it reaches production, which is cheaper than an incident.

Decide: ask "startup or runtime" first, because the first points to sizing and the second to traffic.

### 6. CUDA and NCCL hangs and Xid errors

![A stall with zero token rate behind a green health route, and a mid-stream error that a status code SLI misses.](./img/p3-2018-hang-health-lies.svg)

*Figure 20.18.7. Alert on token rate and finish reason, because health routes and status codes can both stay green.*

Picture a dashboard where the queue keeps growing and no answer ever completes. The process is still running, so nothing looks crashed. Symptom. Requests queue up, nothing finishes, and `rate(vllm:generation_tokens_total[1m])` is zero while waiting plus running is above zero. The process is alive. CPU is idle, and a GPU may sit at 100 percent.

A hang in tensor-parallel serving is often one rank waiting for another in a collective. A rank is one worker process that holds a slice of the model, and a collective is an operation where all the ranks must take part together. If one rank never arrives, the rest wait forever. The book Distributed AI Systems, chapter 9, notes that Docker's default shared memory is only 64 MB. Tensor-parallel workers route NCCL and IPC buffers through it. NCCL is NVIDIA's library for moving data between GPUs, and IPC is inter-process communication. Too little space makes collectives hang with little diagnostic output. The vLLM troubleshooting page gives the debug switches: `NCCL_DEBUG=TRACE`, `CUDA_LAUNCH_BLOCKING=1` and `VLLM_TRACE_FUNCTION=1`. It warns that the last one slows generation by more than 100 times. It also offers `NCCL_P2P_DISABLE=1` as a temporary workaround only. Use the switches to find the stuck rank, then turn them off again.

Here is a trap you must know. In v0.32.0 the `/health` route returns 200 unless the engine is marked dead, and the code behind it checks only an error flag. A hung but not crashed engine keeps answering 200. The route awaits `check_health()` in `async_llm.py`, which raises only if the engine-dead flag is set or the output loop is not running. The output loop is the task that streams tokens back to clients, so a stopped loop is a real failure. Say it as "the health route reports a crash, not a stall". A deep check must send a real one-token request, or watch the token counter.

A failure after the first token has a second trap. By then the server has sent HTTP 200 and cannot change it, because the status line has already left. In the v0.32.0 chat stream generator, a `GenerationError` or any other exception becomes one `data:` error chunk, followed by `data: [DONE]`. The engine side counts the request in `vllm:request_success_total` with `finished_reason="error"`, or `"abort"` if the client left first. So a status-code SLI misses it, and the finish-reason counter sees it. Build the alert on the counter, not on the status code.

Xid errors are kernel-driver messages about GPU faults, visible in `dmesg`. The kernel driver is the software that talks to the GPU hardware, and `dmesg` is the command that prints the kernel's log. The NVIDIA Xid catalog, last updated 2026-11-04 on the page I fetched, gives these examples. Read the table as a first lookup, not as the whole catalog.

| Xid | Name in catalog | What it means | Catalog action |
|---|---|---|---|
| 13 | Graphics Engine Exception | Usually an application fault | Restart the app |
| 31 | GPU memory page fault | Mostly application bugs, sometimes driver or hardware | Restart app, debug with Compute Sanitizer |
| 48 | Double Bit ECC Error | Uncorrectable memory error | Follow the catalog's Xid 48 workflow |
| 74 | NVLink Error | Link problem, may be reported by the healthy peer | Follow the NVLink error workflow, then contact support |
| 79 | GPU has fallen off the bus | PCIe link lost or failing hardware | Restart the bare metal node, then contact support (NVIDIA Xid catalog, fetched 2026-11-09) |
| 94 and 95 | Contained and uncontained memory error | 94 hits one application, 95 needs a GPU reset | Restart app, or reset GPU |

Mitigate now. Capture logs and a stack dump, drain the replica from the pool and restart it. A stack dump records where each thread is waiting, which is the evidence you need after the restart erases the state. Cordon the node for hardware Xid codes, so the scheduler stops placing work on it. Fix later with NCCL timeouts, a watchdog on token rate, and automated cordon on fatal Xid codes. A watchdog is a timer that acts when a signal stops moving. The handbook chapter 15.13 covers the profiling side of NCCL tail latency.

Decide: zero tokens with work present is a hang, and a green `/health` does not change that.

### 7. Slow weight load, cold start and thundering herd on restart

![A 140 GB model pulled from one 14 GB per second source takes 10 seconds for one replica and 320 seconds each when 32 replicas start together.](./img/x18-herd-load.svg)

*Figure 20.18.8. A thundering herd splits one shared source across every replica that starts at once, so load time grows with the number of replicas.*

Picture a deploy that finished, a dashboard that looks fine, and an on-call engineer watching new pods stay not-ready for a long time. Symptom. After a deploy, node failure or autoscale event, replicas stay not-ready for minutes. Latency on the survivors worsens while the new ones load.

The mechanism comes from model size and storage speed. The book gives the size rule as parameters times bytes per parameter. A 70-billion-parameter model in FP16 is 70 x 2 = 140 GB. The book's table puts SSD bandwidth between 0.5 and 14 GB/s. Bandwidth is how many gigabytes per second the disk can deliver. One replica loading at 14 GB/s needs 10 seconds, and at 0.5 GB/s it needs 280 seconds. Distributed AI Systems says typical cold start, with warmup, is 30 to 60 seconds for the models it uses. Large models take longer, and the gap between those numbers is the reason the source matters, so measure your own.

The herd appears when many replicas load at once from one shared source. They split the bandwidth, so every one is slow. A herd is a crowd of identical requests that all arrive together, and a shared source that is already busy becomes slower for everyone. The script `herd_load_calc.py` shows the arithmetic for a 14 GB/s source.

```python
# code/part20/herd_load_calc.py
"""Weight-load time when many replicas pull from one shared source.
Model size = parameters x bytes per parameter (Hands-On LLM Serving, chapter 5).
Source bandwidth range 0.5 to 14 GB/s is the book's SSD row of Table 5-5."""


def weights_gb(params_billion: float, bytes_per_param: float) -> float:
    return params_billion * bytes_per_param


def load_seconds(params_billion, bytes_per_param, replicas, source_gb_per_s):
    """All replicas start together and share the source bandwidth equally."""
    if replicas < 1 or source_gb_per_s <= 0:
        raise ValueError("replicas and bandwidth must be positive")
    return weights_gb(params_billion, bytes_per_param) * replicas / source_gb_per_s


if __name__ == "__main__":
    for n in (1, 2, 8, 32):
        t = load_seconds(70, 2, n, 14)
        print(f"{n:>2} replicas of a 70B FP16 model from a 14 GB/s source: {t:7.0f} s")
```

I ran it. One replica takes 10 s, eight take 80 s each, and 32 take 320 s each. Read the three results as the shape of the problem, not as a forecast. The shape is that load time grows in step with the number of replicas that start together. The equal-share model is a simplification, so treat the numbers as the shape of the problem.

Confirm. Read the model load time in the startup log. The vLLM troubleshooting page says to check whether weights sit on a slow network filesystem and recommends local disk. A network filesystem is storage mounted over the network, and it is often slower than a disk inside the node. Use `--load-format dummy` to separate download and load from everything else. Also check CPU memory, since a large model can cause swapping while it loads.

Mitigate now. Stagger restarts and keep serving replicas in the pool. Staggering means restarting a few at a time, so the rest keep serving traffic. Pre-pull the weights to node-local disk. Fix later. vLLM can cut repeat boots in two ways. Reuse the `torch.compile` cache under `VLLM_CACHE_ROOT`. Pass back the `--kv-cache-memory` value from the previous start to skip memory profiling. Setting `VLLM_FORCE_AOT_LOAD=1` makes a cache miss fail loudly. Add a startup probe so Kubernetes waits for the load. Keep warm spares, which the performance book calls "no substitute" for pre-warmed idle nodes.

Decide: if many replicas load together, fix the rollout order and the weight source, not the engine.

### 8. Probes that hurt: liveness kills and silent pool shrink [vendor]

![A healthy busy pod restarted by liveness fails to re-register, dropping eight replicas to five, with the signals that reveal it.](./img/p3-2018-silent-shrink.svg)

*Figure 20.18.9. Compare ready pods with desired replicas and with the router's backend list.*

![A short liveness timeout restarts healthy busy workers, the survivors take more load, more probes fail, and the pool shrinks silently.](./img/x18-liveness-loop.svg)

*Figure 20.18.10. A liveness probe that restarts healthy workers creates a feedback loop, so liveness must stay local and tolerant.*

A platform team notices that a restart that looked healthy has quietly left the pool a few workers short. Two failures from the Nebius chat-app case study belong together. The case study says aggressive liveness probes were restarting healthy workers. It also says restarted workers sometimes did not rejoin the pool, so capacity shrank silently. Nebius has not published probe settings, so what follows is general method plus my own reasoning.

Liveness kill. The vLLM `/health` route in v0.32.0 does not queue behind generation, because it only reads a flag. So a busy engine alone does not make it slow. It can still time out when the API server process is starved, for example by CPU-heavy tokenisation or a saturated event loop. The default probe timeout is 1 second per the Kubernetes docs. If the liveness probe has a short timeout, or calls a path that waits behind generation work such as a real completion, Kubernetes sees failures and restarts a healthy pod. The restart drops every in-flight request and starts a new weight load. The book Production Kubernetes, chapter 14, says a liveness probe should fail only when a restart is needed, such as a deadlock. Many apps use an endpoint that unconditionally returns 200. It says not to check external dependencies in liveness. It describes readiness as the place for temporary conditions such as warm caches and overload. It also explains the startup probe, which covers slow initialisation and then steps aside.

Silent shrink. A restarted worker has to pass readiness and be re-registered with whatever the router uses for discovery. If registration fails, the pod looks fine to Kubernetes but receives no traffic. Capacity drops from, say, eight replicas to five, and every alert that watches latency stays quiet until load rises. The pain is that nothing is red. A reasonable design, which is my reasoning, alerts on ready versus desired replicas and on per-replica request rate being zero for a ready pod.

Confirm liveness kills with the pod's last state and events. The restart reason names the failed probe. Check generation rate just before the restart. If tokens were flowing, the worker was healthy and busy. Confirm shrink with ready replicas, the router's backend list and a per-backend request rate. Compare the two readings side by side, because a healthy-but-busy worker and a dead one look different in the token rate.

Mitigate now. Relax the liveness timeout and raise `failureThreshold`, which the Distributed AI Systems book suggests setting to 3 or higher. The failure threshold is how many failed probes in a row the kubelet tolerates before it restarts the container. Move load checks to readiness. Restart workers that are ready but unregistered. Fix later with a startup probe, X+1 spare capacity [vendor], and an alert on ready less than desired. Handbook chapter 15.16 has worked probe numbers, and I did not re-verify them here.

Decide: liveness answers "should this process be killed", readiness answers "should it get traffic", and mixing them causes both of these failures.

### 9. Retry amplification during a partial outage

![Bars of 1.11, 1.875 and 2.95 expected attempts at failure rates 0.1, 0.5 and 0.8, beside the loop that raises load.](./img/p3-2018-retry-attempts.svg)

*Figure 20.18.11. The higher the failure rate, the more retries arrive, which raises the failure rate again.*

A small outage becomes a large one, and the on-call channel fills with graphs that all climb together. Symptom. A small outage becomes a large one. Half the replicas fail, and traffic arriving at the survivors doubles, then doubles again. Request rate at the gateway exceeds the user request rate.

The mechanism is arithmetic, and it is worth doing once by hand. If each attempt fails with probability p and a client allows k attempts, the expected attempts per request are the sum 1 + p + p squared, continuing up to p to the power k minus 1. Each term is the chance that the request reaches that attempt. I computed this for k = 4. At p = 0.1 it is 1.11 attempts. At p = 0.5 it is 1.875. At p = 0.8 it is 2.95. As load rises, p rises, so the load rises again. That loop is why the Nebius case study changed retry logic to stop amplification in partial outages [vendor].

Confirm. Compare gateway request rate against unique user requests. If you do not track unique requests, compare against the rate of successful responses. Look for `vllm:admission_rejections_total` rising together with retries from clients. When the two rise together, the clients are answering the rejections with more attempts, and that is the loop you are trying to break.

Mitigate now. Cut client retries, return 503 with a back-off hint, and shed at the edge. A back-off hint tells the client how long to wait before the next attempt. Fix later with a retry budget, jittered exponential back-off, a circuit breaker and idempotency keys. Jitter adds a random delay so that clients do not all retry at the same instant. Chapter 20.21 covers these in depth. The book AI Systems Performance Engineering, chapter 16, adds that failing fast and applying backpressure give a stressed system room to recover.

Decide: during a partial outage, reduce the number of attempts first, because more capacity will not catch up with a growing retry loop.

### 10. Noisy tenants

![An aggregate dashboard shows normal latency and green status, while a per-tenant gateway breakdown reveals that one tenant takes 68 percent of prompt tokens and starves others in the queue.](./img/p4-2018-noisy-tenant.svg)

*Figure 20.18.12. Aggregate dashboards mask noisy tenant starvation, which is confirmed by breaking down prompt tokens and request rates by tenant at the gateway.*

Picture a status page where the average looks healthy, but one customer keeps writing in to say their answers are slow. Symptom. One customer's p99 is fine, another's is awful, and aggregate dashboards look normal. A single tenant is sending large batches or long prompts.

Confirm. Break prompt tokens and request rate down by tenant at the gateway. A tenant holding half or more of the prompt tokens while others queue is the signature. Be careful about putting tenant ID on engine histograms. The vLLM metrics page warns that every histogram bucket adds one series per label combination, so a tenant label multiplies series quickly. A series is one stored time line in the metrics database, and too many series slow the whole system down.

Mitigate now. Apply that tenant's rate limit, or move them to a dedicated endpoint. A dedicated endpoint gives one customer their own replicas, so their load cannot reach the others. Fix later with per-tenant token quotas and fair-share queueing at the router, which chapter 20.13 designs. Fair-share queueing gives each tenant a turn, so one busy tenant cannot take every slot.

Decide: if the damage is uneven across tenants, look at who sent the tokens before you look at the GPUs.

### 11. Quality failures: finish_reason drift, corruption, speculative decoding and quantisation

![Quality failures show green infrastructure while answers are cut off, with causes such as finish reason drift, NaN corruption, speculative decoding, quantisation and sampling defaults.](./img/p2-2018-quality-checks.svg)

*Figure 20.18.13. Quality failures leave infrastructure green, so the design checks finish_reason shares, NaN corruption counts and the last configuration change.*

Symptom. Nothing errors, latency is fine, and users complain that answers are cut off, repetitive or odd. This is the hardest failure to see, because every infrastructure signal is green. A green dashboard can still hide a product that is failing its users. The Nebius case study lists alerts on finish_reason drift for this reason [vendor].

The signal. The counter `vllm:request_success_total` has a `finished_reason` label. A label is a tag that splits one counter into several series. In v0.32.0 the reasons are stop, length, abort, error and repetition. The source says error is a retryable request-level error returned as HTTP 500, and repetition means a repetitive token pattern was detected. A rise in the share of length, which means the model ran to its token limit, or any repetition finishes, is a drift signal. Drift means the mix of outcomes moves away from what it was on a calm day. The classifier computes shares from rates.

KV-cache corruption. vLLM has a counter `vllm:corrupted_requests`, counting requests with NaNs in logits. NaN stands for not a number, a bad value that spreads through later arithmetic, and logits are the raw scores the model gives each possible next token. A request is counted once, when it finishes, if any step produced NaNs. In v0.32.0 the source registers it only when the environment variable `VLLM_COMPUTE_NANS_IN_LOGITS` is set. If you never set it, the metric is simply absent. Absence does not mean zero corruption. Set the variable in a test environment first, so you know the counter works before you rely on it.

Speculative decoding. The vLLM docs say speculative decoding is theoretically lossless up to hardware numerics, and that greedy output matches in their tests. Speculative decoding means a small draft model proposes tokens, and the main model checks them. Lossless here means the answer should match what the main model alone would produce. They also say batch size changes can cause small variations. So a quality regression after enabling speculation is less likely to come from the algorithm than from a configuration change. The real trap is speed. If the draft rarely matches, you pay for drafts and save little. The design page gives the acceptance rate as accepted tokens over draft tokens, using `vllm:spec_decode_num_accepted_tokens_total` and `vllm:spec_decode_num_draft_tokens_total`. A rate below about 50 percent is my starting threshold, not a vLLM number.

Quantisation. Chapter 5 of Hands-On LLM Serving says lowering precision reduces model size and improves serving performance at the cost of some accuracy. Lowering precision means storing each number with fewer bits, which makes the model smaller and faster to move. Nebius markets about 99 percent quality for its quantised models [vendor]. Do not take any such claim on trust for your task. Gate each precision or KV-cache dtype change behind an evaluation set and a canary. A canary is a small share of traffic on the new version, so a problem shows up before it reaches everyone. Watch finish_reason shares during the canary.

A fourth cause is the sampling defaults. Sampling settings control how the model picks each next token, such as how random the choice is. The vLLM troubleshooting page says that since v0.8.0 the default sampling parameters come from the model's `generation_config.json`, and `--generation-config vllm` restores the old defaults. An engine upgrade can change output length and style with no code change at all. That is why the last config change belongs on the checklist for quality complaints.

Mitigate now. Stop the rollout and roll back the change on the affected pool. A pool is the group of replicas that share one configuration, so rolling back one pool limits the damage to that group. Compare outputs on a fixed prompt set. A fixed prompt set is a short list of questions you always send, so you can compare the answers before and after the change. Fix later with canaries that include output-quality checks.

Decide: when infrastructure is green and users are unhappy, check finish_reason shares and the last config change.

### 12. Version skew between router and engine

![A three-step deprecation timeline ending in a removed metric that looks like no data, with a version-pair checklist.](./img/p3-2018-metric-deprecation.svg)

*Figure 20.18.14. Treat a missing series as a fault, not as a quiet system.*

Picture a rollout that finished an hour ago, and then a support ticket about odd answers on one route only. Symptom. Errors or odd outputs begin right after a rollout, and only on some routes. One side was upgraded, the other was not.

The mechanism. A router and an engine share assumptions: API fields, token accounting, metric names and defaults. vLLM's own docs show the risk. Its metrics deprecation policy says a metric deprecated in version X.Y is hidden in X.Y+1 and removed in X.Y+2. A deprecated metric still works for a while, but it is slated for removal. A dashboard or autoscaler that reads a removed metric goes blind, and the drop shows as "no data", which many alert rules treat as healthy. The Grafana text in the v0.32.0 metrics design page still mentions a swapped-requests metric, while the v0.32.0 source defines none, which shows how docs and code drift.

Confirm. Put the engine version and router version in labels or a startup log line, and compare across hops. A hop is one network step between two services, such as client to router and router to engine. Check which metric names exist with a query against `/metrics`. If a name is missing, check the version pair before you assume the system is idle.

Mitigate now. Pin both sides to a known pair and roll back the newer one. Pinning means fixing the version so nothing changes under you. Fix later with a compatibility matrix in CI, a rollout order for the control plane and data plane, and alerts that treat missing series as a fault. A compatibility matrix is a table of tested version pairs, and CI is the automated test system that checks each pair.

Decide: after any rollout, check versions at every hop before you debug behaviour.

### 13. A decision tree, an alert-to-cause table and a classifier

![A table mapping eight alerts to ranked likely causes and the single first check that separates them.](./img/p3-2018-alert-to-cause.svg)

*Figure 20.18.15. Use the tree to pick a family of causes, then the table to find the one number that separates them.*

During the incident you have three minutes to choose a direction, and a tree makes that possible. The tree uses only the signals above, so you can follow it without reopening every chapter. Start at the top and answer one yes or no question at each step.

![A decision tree, an alert-to-cause table and a classifier](./img/m20-18-2.svg)

*Figure 20.18.16. A decision tree, an alert-to-cause table and a classifier, as a diagram.*

The table maps the alert you are most likely to receive to the causes to rank first and the one check that separates them. Use it after the tree, when the tree has pointed you to a family of causes and you need the one number that tells them apart.

| Alert | Likely causes, in order | First check |
|---|---|---|
| TTFT p99 high | Queue growth, cache hit collapse, head-of-line blocking, KV exhaustion | `vllm:request_queue_time_seconds` p99 versus `vllm:num_requests_waiting` |
| Inter-token latency high | KV exhaustion, head-of-line blocking, low speculative acceptance | `vllm:num_preemptions_total` rate and prompt-token tail |
| Waiting queue growing | Capacity, noisy tenant, retry amplification | `vllm:num_requests_running` at limit, per-tenant tokens |
| 503s rising | Admission limit, pool shrink, overload | `vllm:admission_rejections_total` and ready replicas |
| Tokens per second is zero | Hang, Xid fault, crash loop | `dmesg` Xid lines and NCCL log |
| Pods restarting | Liveness kill, startup OOM, runtime OOM | Pod last state and restart reason |
| Ready below desired | Shrink, herd, slow load | Router backend list, load time in startup log |
| Output complaints, infra green | Finish_reason drift, quantisation, version skew, sampling defaults | `vllm:request_success_total` shares by finished_reason |

Writing the table by hand teaches it, and encoding it makes it testable. The classifier in `code/part20/` takes a set of readings, optionally with a calm baseline, and returns ranked causes with evidence, a confirmation step, an action now and a fix later. A baseline is a set of readings from a calm period, so you can say what "high" means for this system. Readings use real vLLM metric names with a derivation after an at sign, such as `vllm:time_to_first_token_seconds@p99`. Signals that vLLM does not export, such as Xid codes or restart reason, carry a `sig:` prefix so nobody mistakes them for metrics. The scoring engine is short, and you can read it in one sitting.

```python
# code/part20/failure_model.py
"""Scoring engine for the LLM serving failure-signature classifier.

Reading keys are either a vLLM metric name with a derivation after "@",
for example "vllm:time_to_first_token_seconds@p99", or a "sig:" signal that
does not come from vLLM (probe restarts, Xid codes, replica counts).
"@rate" means rate() over the exported "_total" counter series.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

FINISH_REASONS = ("stop", "length", "abort", "error", "repetition")


class Readings:
    """Current readings plus an optional baseline taken from a calm period."""

    def __init__(self, current: dict, baseline: Optional[dict] = None):
        self.current = dict(current)
        self.baseline = dict(baseline or {})
        self.missing: set = set()

    def get(self, key: str) -> Any:
        if key not in self.current:
            self.missing.add(key)
            return None
        return self.current[key]

    def up(self, key: str, factor: float) -> Optional[bool]:
        """True when current >= factor * baseline. None if either is unknown."""
        now, base = self.get(key), self.baseline.get(key)
        if now is None or not base:
            return None
        return now >= factor * base

    def finish_share(self, reason: str, baseline: bool = False) -> Optional[float]:
        src = self.baseline if baseline else self.current
        rates = {r: src.get(f"vllm:request_success@rate:{r}") for r in FINISH_REASONS}
        if all(v is None for v in rates.values()):
            return None
        total = sum(v or 0.0 for v in rates.values())
        return (rates[reason] or 0.0) / total if total else None


Check = tuple  # (weight, description, fn(Readings) -> Optional[bool])


@dataclass(frozen=True)
class Rule:
    cause: str
    confirm: str
    mitigate_now: str
    fix_later: str
    checks: tuple = field(default_factory=tuple)  # first check is the anchor


@dataclass
class Hypothesis:
    cause: str
    score: float
    evidence: list
    unknown: list
    confirm: str
    mitigate_now: str
    fix_later: str


def evaluate(rule: Rule, r: Readings) -> Optional[Hypothesis]:
    total = sum(w for w, _, _ in rule.checks)
    hit, evidence, unknown = 0.0, [], []
    for i, (weight, text, fn) in enumerate(rule.checks):
        ok = fn(r)
        if i == 0 and not ok:
            return None  # the anchor symptom must be present
        if ok is None:
            unknown.append(text)
        elif ok:
            hit += weight
            evidence.append(text)
    if not evidence:
        return None
    return Hypothesis(rule.cause, round(hit / total, 3), evidence, unknown,
                      rule.confirm, rule.mitigate_now, rule.fix_later)


def rank(rules: list, current: dict, baseline: Optional[dict] = None) -> list:
    """Return hypotheses sorted by score, best first. Ties break on cause name."""
    r = Readings(current, baseline)
    found = [h for h in (evaluate(rule, r) for rule in rules) if h]
    return sorted(found, key=lambda h: (-h.score, h.cause))
```

Each rule lists weighted checks. The first check is the anchor symptom. If it is false or unknown the cause is dropped, so a rule can never match on side evidence alone. Unknown checks are listed as "not measured", so the output tells you what to collect next. Weighted means some checks count for more than others, so the score reflects how strong the evidence is. Here is one rule from `failure_rules.py`, which has 19 rules in total. Read the rule once, then read the list of checks, and notice that the first check is the one that must be true.

```python
# excerpt: the KV-exhaustion rule in failure_rules.py
Rule("kv_cache_exhaustion_preemption",
     "kv_cache_usage_perc near 1 and rate(vllm:num_preemptions_total) above 0",
     "lower max_num_seqs or max_num_batched_tokens, or add replicas",
     "raise gpu_memory_utilization, add tensor parallel, quantise KV cache, resize for context length",
     ((3, "KV usage at or above 95 percent", gt(KV, T["kv_full"])),
      (3, "preemptions are happening", gt(PRE, 1e-9)),
      (1, "inter-token latency p99 at least 2x baseline", up(ITL, 2)),
      (1, "requests waiting", gt(W, 1)),
      (1, "end-to-end p99 at least 2x baseline", up(E2E, 2)))),
```

Decide: in the room, use the tree first and the table second, and say the classifier's logic aloud as "anchor symptom, then supporting evidence". Saying the logic aloud is what turns a script into an answer the interviewer can follow.

## How to answer out loud

The five answers below follow one shape: say the order, name the first check, and say what you do before the cause is known. Read each one aloud once before you use it in a round.

**Question 1. "TTFT tripled. What do you do?"** Say the order. First, check whether users are being hurt and whether it is one tenant, one route or everything. Then read waiting, running, KV usage and token rate. State your hypothesis from those four numbers. Mitigate before root cause: shed or scale. Name two follow-ups, the queue-time histogram and the preemption rate. Expect the interviewer to say "KV usage is 98 percent", which moves you to section 3. When that happens, say that the memory is now the constraint, and switch your mitigation from scaling to admission.

**Question 2. "Pods keep restarting and nobody changed anything."** Start by asking for the restart reason and the last state, because they name the probe or the memory event. Split the cause three ways: liveness, OOM at startup, OOM at runtime. For liveness, ask whether tokens were flowing, since a busy worker and a dead worker look different in the token rate. Say that liveness should be local and unconditional, that readiness should carry load state, and that a startup probe covers the weight load. Name the cost of a restart: lost in-flight requests and a fresh weight load.

**Question 3. "Capacity seems lower than it should be, but nothing is alerting."** Say "silent shrink" early, because the name tells the interviewer you have met this failure before. Compare ready with desired, then compare the router's backend list with ready pods. The gap between those two lists is where the silence lives. Mitigate by re-registering or replacing workers. The fix is an alert on ready versus desired and X+1 spare capacity. Mention that this symptom comes from the vendor case study, and say that Nebius has not published its detection design.

**Question 4. "Users say answers are worse. Metrics are green."** Say that infrastructure health and output quality are different signals, and that a green dashboard measures the first one only. Check the last change first: engine version, quantisation, speculation, sampling defaults. Show finish_reason shares against a baseline, so the change in the mix is visible. Roll back the change on a canary pool, then compare outputs on a fixed prompt set.

**Question 5. "Half your replicas die. Why does the rest of the system collapse?"** Explain retry amplification with the arithmetic, one step at a time. At a failure rate of 0.5 and four attempts the load is 1.875 times. It rises as the failure rate rises. Name the defences: retry budget, jitter, circuit breaker, edge shedding, and the 503 admission limit. Expect "what is a retry budget", and answer with a cap on retries as a fraction of requests.

## Worked scenarios

Two of the scenarios below are worth working on paper before you read the answer. Each one gives you a situation, a reasoning path and a short answer you can say aloud.

### Scenario A. The 16-request burst

![A two-column comparison of the toy simulator at 10 GB and 34 GB of free cache, showing preemptions and step counts.](./img/p3-2018-burst-sim.svg)

*Figure 20.18.17. The same 16 requests are calm with enough cache and crowded without it.*

A 24 GB GPU serves Llama-2-7B in FP16. A batch job sends 16 requests, each with a 3,000-token prompt and 1,000 output tokens. Users report slow, uneven streaming. Notice that no single request is unusual. The trouble comes from all of them arriving together.

Reasoning. Weights take 14 GB, leaving 10 GB. At 0.5 MB per token that is 20,480 tokens. Each request grows to 4,000 tokens. By prompt size six are admitted, and the rest wait, and as admitted requests grow, the cache fills and the newest is preempted. Walk through it in that order, because each step explains the next. The script models that behaviour. It is a toy and not vLLM, and it assumes the newest request is the victim. I did not verify vLLM's actual victim policy.

```python
# code/part20/kv_pressure_sim.py
"""Toy model of KV-cache pressure with preemption by recompute. NOT vLLM.
Capacity comes from the Hands-On LLM Serving book example: Llama-2-7B in FP16
on a 24 GB GPU leaves 10 GB, and each token needs 0.5 MB of KV cache."""
import json
import sys
from collections import deque


def simulate(n_req=16, prompt=3000, out=1000, free_gb=10.0, mb_per_token=0.5):
    cap = int(free_gb * 1024 / mb_per_token)
    waiting = deque({"p": prompt, "left": out, "gen": 0} for _ in range(n_req))
    running, steps, preempts, peak, max_wait, recompute = [], 0, 0, 0.0, 0, 0
    done = 0
    while waiting or running:
        steps += 1
        used = sum(r["p"] + r["gen"] for r in running)
        while waiting and used + waiting[0]["p"] + waiting[0]["gen"] <= cap:
            r = waiting.popleft()
            used += r["p"] + r["gen"]
            running.append(r)
        max_wait = max(max_wait, len(waiting))
        for r in running:
            r["gen"] += 1
            r["left"] -= 1
        used = sum(r["p"] + r["gen"] for r in running)
        while used > cap and len(running) > 1:  # newest request is evicted
            v = running.pop()
            used -= v["p"] + v["gen"]
            recompute += v["p"] + v["gen"]
            v["p"], v["gen"] = v["p"] + v["gen"], 0  # redo prompt plus generated text
            waiting.appendleft(v)
            preempts += 1
        peak = max(peak, used / cap)
        finished = [r for r in running if r["left"] <= 0]
        done += len(finished)
        running = [r for r in running if r["left"] > 0]
    return {"capacity_tokens": cap, "steps": steps, "preemptions": preempts,
            "peak_kv_usage": round(peak, 3), "max_waiting": max_wait,
            "recomputed_tokens": recompute, "finished": done}


if __name__ == "__main__":
    kw = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(simulate(**kw), indent=2))
```

I ran it. With 10 GB free the toy reports capacity 20,480 tokens, peak usage 1.0, 2 preemptions, 11 requests waiting at the worst moment, 6,759 recomputed tokens and 3,000 steps. With 34 GB free, the L40S case from the book, it reports no preemptions and 1,000 steps. The same 16 requests take three times as many steps on the small GPU, because admission is limited. The contrast is the lesson: the same traffic is calm on a larger memory budget and crowded on a smaller one.

Answer. This is KV exhaustion with queueing, section 3 and section 2 together. Now: lower the batch size limits or send the job to a bigger pool. Later: size the endpoint for the longest realistic request, or add replicas. Say the now and the later separately, because the interviewer wants to see that you protect users before you plan the fix.

### Scenario B. Pods restart under load

Traffic doubles, and the restarts begin before anyone has changed the config. Six pods of eight restart within ten minutes. Latency rises, and nothing in the logs shows a crash. This pattern often looks like a bug in the engine, but the first check is the probe, not the code.

Reasoning. Ask for the restart reason first. Suppose it says liveness probe failed. Then check tokens per second before the restarts. If tokens flowed, the workers were busy, not dead, and the probe was the problem. Now check the pool. Restarted pods need a fresh load, and meanwhile the two survivors take all traffic. That raises queue time, which makes more probes fail, which is a loop. Also check ready versus desired, because restarted workers may not have rejoined. Write the loop down as three arrows, since the interviewer may ask you to draw it.

The sample file `samples/liveness_kill.json` encodes these readings. The classifier output, which I ran, ranks the liveness kill and the silent shrink first, both at score 1.0, and queue growth third at 0.4. The two are linked, so seeing both is correct. A ranking like this does not tell you which failure came first, so the evidence of the restart timing still has to be read by a person.

Answer. Relax the liveness timeout, raise the failure threshold, add a startup probe and make liveness local. Re-register or replace unregistered workers. Add the ready-versus-desired alert. Say the probe fix first, because it stops the loop, and then say the registration fix, because it restores the capacity.

### Scenario C. A rolling restart of eight replicas

![Two timelines comparing eight replicas loading together for 80 seconds with small groups and staged weights.](./img/p3-2018-rolling-restart-gap.svg)

*Figure 20.18.18. Restart in small groups and stage weights locally so some capacity always serves.*

A new image is rolled out, and all eight replicas restart together. This is the most common way to lose an endpoint by accident. The model is 70 billion parameters in FP16, loaded from a shared source that delivers 14 GB/s.

Reasoning. Weights are 140 GB. One replica alone needs 10 seconds. Eight in parallel need 80 seconds each under the equal-share model, during which the endpoint has no capacity. If clients retry during that gap, the retry arithmetic in section 9 makes the first minute after recovery worse. The gap is the window to plan for, not the steady state.

Answer. Restart in small groups, keep at least X+1 replicas serving, and stage the weights on local disk so the source stops being the shared bottleneck. A real run on your own storage may differ, so measure the load time in the startup log and use that number in your answer. Saying you will measure first is more credible than a number you cannot defend.

## Hands-on lab

You have a laptop, a terminal and a short hour, and you want to see these failures for yourself rather than take the text on trust. Everything here runs on a laptop. I ran steps 1 to 5. Step 6 needs a GPU host and was not run.

1. From the repo root, run the toy KV simulation and read the output.

```bash
python3 code/part20/kv_pressure_sim.py
python3 code/part20/kv_pressure_sim.py '{"free_gb": 34}'
```

Expected result: 2 preemptions and 3,000 steps for the first command, and 0 preemptions and 1,000 steps for the second.

2. Run the herd calculation and confirm the 10, 20, 80 and 320 second lines.

```bash
python3 code/part20/herd_load_calc.py
```

3. Classify the two sample incidents.

```bash
python3 code/part20/classify_failures.py code/part20/samples/kv_exhaustion.json
python3 code/part20/classify_failures.py code/part20/samples/liveness_kill.json
```

Expected result: the first prints `kv_cache_exhaustion_preemption` at 0.889 on top. The second prints the liveness kill and the silent shrink at 1.0.

4. Think of a real incident you remember. Write a readings file for it, using the keys from `failure_rules.py`. Run the classifier on that file. Then read the "not measured" line. Ask yourself whether the missing signals were things you would really have checked.

5. Run the tests.

```bash
python3 -m pytest code/part20/test_failure_classifier.py code/part20/test_sim_and_calc.py -q
```

Expected result: 23 passed.

6. On a GPU host, start `vllm serve` with a small model. Send some load. Then `curl` the `/metrics` endpoint. Confirm that the metric names in section 1 are present, and note the `_total` suffix on counters. The expected shape of the output is lines starting with `vllm:` and a `model_name` label. This step was not run.

## Drill questions

These drill questions are the checks a colleague would ask you on a quiet afternoon. Each answer should hold up against the tables and code above, so when you disagree with one, go back to the arithmetic first.

<details><summary>1. Name the three places a request can wait in an LLM engine and the metric for each.</summary>
The waiting queue is `vllm:num_requests_waiting`. The running batch is `vllm:num_requests_running`. The KV cache is `vllm:kv_cache_usage_perc`, where 1 means full.
</details>

<details><summary>2. Why do you write `vllm:num_preemptions_total` in PromQL when the source defines `vllm:num_preemptions`?</summary>
Prometheus counters are exposed with a `_total` suffix. The vLLM metrics design page says the suffix is stripped in the definition and added when the series is exposed.
</details>

<details><summary>3. What does vLLM do when the KV cache is full, and what is the default mode in V1?</summary>
It preempts a request, frees its cache and recomputes it later. The default mode in V1 is recompute, because the docs say recomputation has lower overhead than swap there.
</details>

<details><summary>4. Name three levers that reduce preemptions.</summary>
Raise `gpu_memory_utilization`, lower `max_num_seqs` or `max_num_batched_tokens`, and raise tensor parallel size. Pipeline parallel size is a fourth.
</details>

<details><summary>5. Compute the KV cache per token for Llama-2-7B in FP16, and how many 4,096-token requests fit in 10 GB.</summary>
Two times 32 layers times 32 heads times head dimension 128 times 2 bytes gives 524,288 bytes, which is 0.5 MB. Ten GB is 10,240 MB, divided by 0.5 MB times 4,096 tokens gives 5 requests.
</details>

<details><summary>6. Your engine has work queued and zero token rate, but `/health` returns 200. Why?</summary>
In v0.32.0 the health route fails only when the engine is marked dead. A hang does not set that flag. So the route reports a crash, not a stall. Use the token rate or a real one-token probe.
</details>

<details><summary>7. How do you tell startup OOM from runtime OOM, and what differs in the fix?</summary>
Startup OOM happens during load or memory profiling, before serving, so sizing is wrong or a co-tenant holds memory. Fix by lowering `gpu_memory_utilization` or `max_model_len`. Runtime OOM happens under traffic, so headroom is too small. Fix by lowering batch limits and capping prompt length.
</details>

<details><summary>8. Why does a short liveness timeout hurt a busy LLM worker, and what should liveness check instead?</summary>
A busy engine answers slowly, so the probe fails and Kubernetes restarts a healthy pod, dropping requests and forcing a weight load. Liveness should fail only when a restart is needed, and it should not check external dependencies. Readiness carries load state.
</details>

<details><summary>9. Give the formula for expected attempts per request with failure probability p and k attempts, and its value at p = 0.5, k = 4.</summary>
The sum of p to the power i, for i from 0 to k minus 1. At 0.5 and 4 attempts it is 1 + 0.5 + 0.25 + 0.125, which is 1.875.
</details>

<details><summary>10. Infrastructure is green and users say answers are cut off. What do you check?</summary>
The share of `finished_reason` equal to length in `vllm:request_success_total`, compared with a baseline, plus repetition finishes. Then the last change: engine version, quantisation, speculation, or sampling defaults from `generation_config.json`.
</details>

## Common mistakes and weak answers

Picture the debrief after a round that went badly. The same few mistakes come up again and again, and most of them are about order rather than knowledge.

Saying "I would check GPU utilisation" as your first move. Utilisation is high both when the system is healthy and when it is saturated. Say you would read the waiting queue, the batch, KV usage and the token rate.

Jumping to root cause before mitigation. The interviewer scores whether users are protected in the first minutes. Shed, scale or roll back first, then investigate.

Trusting `/health`. In the version I read it reports a crash, not a stall. A green health check tells you the process is alive, and nothing more. Say you would watch token rate or send a real one-token request.

Putting load checks into liveness. This restarts healthy workers and causes a herd. Say that readiness carries load state and a startup probe covers the load.

Presenting numbers as facts. Say "my starting threshold is" for tails, ratios and acceptance rates, and say that Nebius has not published its own thresholds. A threshold you chose is a starting point, and the interviewer will respect you more for saying so.

Claiming Nebius internals. Say "the case study says" and tag it as vendor material. Say "a reasonable design is" for everything else.

Forgetting quality failures. Many candidates treat only latency and errors as incidents. Mention finish_reason drift, and say it needs a baseline.

## Connections to the rest of the handbook

You finish a drill and want to go deeper on one failure. The links below are where each topic gets its full treatment, so use them after the timed run.

- 15.3 vLLM in depth (`c15-03`) explains the scheduler and cache that this chapter's failures come from.
- 15.13 Profiling, debugging and tuning inference at scale (`c15-13`) covers TTFT versus inter-token stalls, preemption debugging and NCCL tail latency.
- 15.15 Autoscaling inference (`c15-15`) covers the fix for queue growth.
- 15.16 Production serving stack and reliability (`c15-16`) covers probes, XID remediation and circuit breakers.
- 17.6 Alerting, SLOs and health checks (`c17-06`), 17.7 Failure modes and detection (`c17-07`), 17.11 Incident response (`c17-11`) and 17.15 On-call runbooks (`c17-15`) cover the generic side.
- 20.13 Design: multi-tenant LLM API (`c20-13`) designs the tenant isolation that section 10 depends on.
- Later in this volume: 20.19 SLIs and SLOs, 20.20 autoscaling, 20.21 routing and retries, 20.26 incident role-play.

## Sources and review notes

Sources and dates fetched (2026-11-09):

- vLLM release v0.32.0, published 2026-10-18, the latest stable release at fetch time. A v0.33.0rc3 tag was also listed. Files read at tag v0.32.0 from the vllm-project/vllm repository: `docs/usage/metrics.md`, `docs/design/metrics.md`, `docs/configuration/optimization.md`, `docs/usage/troubleshooting.md`, `docs/features/speculative_decoding/README.md`, `vllm/v1/metrics/loggers.py`, `vllm/config/scheduler.py`, `vllm/config/cache.py`, `vllm/v1/engine/__init__.py`, `vllm/v1/engine/async_llm.py`, `vllm/entrypoints/serve/instrumentator/health.py`, `vllm/v1/worker/gpu_worker.py`. The metrics table in the docs is generated at build time, so metric names were taken from `loggers.py`.
- NVIDIA Xid catalog, docs.nvidia.com/deploy/xid-errors, page showing "Last updated on Nov 04, 2026".
- Hands-On LLM Serving and Optimization, chapter 5 "Challenges When Serving LLMs": model loading, KV cache size, memory table.
- AI Systems Performance Engineering, chapter 16 "Profiling, Debugging, and Tuning Inference at Scale": troubleshooting table, error handling, headroom, memory.
- Distributed AI Systems, chapter 9 "Production LLM Serving Stack": cold start, backpressure, probe settings, shared memory.
- Production Kubernetes, chapter 14 "Application Considerations": liveness, readiness and startup probes.
- LLMs in Production, chapter 6 "Large language model services": read for batching, rate limiting and autoscaling. No claim in this chapter depends on it beyond general background.
- Nebius chat-app case study, as summarised in `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` section 1, tagged vendor. The plan does not record a URL.

Explicitly labelled inferences:

- All thresholds in the classifier, including the 50 percent acceptance rate, the 8x prompt-length tail, 95 percent KV usage and the 15-point finish_reason shift.
- The explanation of why Nebius liveness probes killed healthy workers, and the design that alerts on ready versus desired replicas.
- The equal-share model in the herd calculation.
- That vLLM's preemption victim is the newest request. The toy assumes it.

Not verified:

- No real vLLM server was started, so no metric output, log line or `/metrics` text was observed. The preemption log line is quoted from the docs and may differ in your version.
- I did not check Nebius Token Factory documentation for the engine version it runs.
- The book's default of about 0.85 for `gpu_memory_utilization` conflicts with 0.92 in the v0.32.0 config class (`Field(default=0.92)` in `vllm/config/cache.py`). Real defaults can be changed at engine-config creation, so read the startup log. Trust the source for v0.32.0.
- Nebius has not published its alert thresholds, probe settings or router design.

### Verification log (fact-check pass, 2026-11-09)

Resolved 6 flagged claims: 4 confirmed, 1 corrected, 1 still unverified.

- CONFIRMED: `/health` returns 503 only when the engine is dead. `health.py` calls `check_health()`, and `async_llm.py` raises only if `errored` (engine dead flag or output loop not running) is true. A hung engine still returns 200. Read at tag v0.32.0.
- CORRECTED: the claim that a busy engine answers `/health` slowly. The route reads a flag and does not wait behind generation work. Slowness would come from a starved API server process, so the text now says that.
- CONFIRMED: `vllm:corrupted_requests` exists only when `VLLM_COMPUTE_NANS_IN_LOGITS` is set, and counts requests once at finish if any logits had NaNs (`stats.py`, `loggers.py`).
- CONFIRMED: a stream failing after the first token ends with a `data:` error chunk then `[DONE]` under HTTP 200. Engine errors count as `finished_reason="error"`, client disconnects as `abort` (`chat_completion/serving.py`, `output_processor.py`).
- CONFIRMED: Kubernetes probe fields and the 1 second `timeoutSeconds` default, and the startup probe pattern, from kubernetes/website `configure-liveness-readiness-startup-probes.md` at main.
- CONFIRMED: `gpu_memory_utilization` default 0.92 in v0.32.0.
- Latest stable vLLM at check time: v0.32.0 (2026-10-18). v0.33.0rc3 (2026-11-02) is flagged as a release candidate in the tag list, though the GitHub flag shows it as not prerelease, so keep v0.32.0 as the pin.
- STILL UNVERIFIED: the classifier thresholds and Nebius probe settings, which are labelled design choices.
