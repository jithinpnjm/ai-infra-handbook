# Voice rewrite, Part 20 chapters 19-21 (group g)

Scope: `docs/part-20-nebius-sre-interview/19-slis-slos-and-alerts-for-token-apis.md`, `20-autoscaling-gpu-inference.md`, `21-request-routing-retries-and-overload-control.md`.
Not committed. Only the three chapter files were changed.

Method: the locked blocks (front matter, fenced code, Mermaid, tables, checkpoint `<details>` blocks, and the Sources and review notes tail through end of file) were kept byte-identical by re-inserting the HEAD blocks with a splice script. Headings are identical. Only prose was rewritten or added.

## Results

| File | Words before (wc) | Words after (wc) | Growth | Prose growth (guard) | rewrite_guard | chain_gate | Span check |
|---|---|---|---|---|---|---|---|
| 19 SLIs, SLOs and alerts | 9035 | 11957 | +32.3% | 7458 to 10380, +39.2% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 | `{}` |
| 20 Autoscaling GPU inference | 9122 | 11708 | +28.4% | 7022 to 9608, +36.8% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 | `{}` |
| 21 Request routing, retries, overload | 9509 | 12177 | +28.1% | 7271 to 9939, +36.7% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 | `{}` |

Also checked for each file: locked blocks identical to HEAD (code, tables, `<details>` blocks), headings identical, Sources and review notes tail identical to HEAD, no exclamation marks in prose (the `!=` in code is locked), no "you will be able" or "should be able" lines, no raw `{` or `<` in prose. Each file keeps "Not verified" and the honest "not run" or "not verified" wording.

## Needs source (general explanations added, not Nebius facts)

Chapter 19:
- Prefill as the step that reads the whole prompt once, and decode as the step that produces one token at a time (section 2).
- KV cache as the memory that holds attention state for each running request, and preemption as evicting a running request to free that memory (section 7).
- 429 as the HTTP status for "too many requests" (section 10).
- Series as one stored line per unique metric and label combination (section 4).
- The `for:` clause as a wait before an alert fires (section 6).
- Retry amplification as retries adding load to a struggling service (section 11).
- Goodput as an operational name for requests that met both limits (section 9). The DistServe abstract is cited in the original for the TPOT and TTFT constraint wording.

Chapter 20:
- Cold start as the time from scale decision to a serving replica (section 5).
- Pending pods as pods waiting for a schedulable node (section 8).
- The ceiling function rounding the HPA result up (section 3).
- The Pod Pending to node provisioning sequence as described in the Mermaid chart (original).

Chapter 21:
- Idempotency keys as a client-supplied token the server uses to recognise a repeat (section 1 and Scenario C).
- Poisson arrivals as the arrival model in the simulator (section 3).
- EndpointSlice, kube-proxy and the endpoint race in the drain discussion (section 11). The Production Kubernetes citation is original.
- Token-bucket description of the retry budget (section 4). The gRPC throttling figures are original.
- Lognormal latency as the shape used in the hedging toy model (section 6). The shape value 0.6 is original.
- The repeat-offender reading of Envoy's growing ejection time (section 7). The 300 second maximum is original.

## Unresolved

- `node tools/check_mermaid.mjs` was not run. The brief said no npm build, so `npm run build` was not run either.
- The Mermaid blocks, tables and code are unchanged, so no new Mermaid syntax risk was introduced by this rewrite.
- Chapter 20 has five bold "Question N" lead-ins under "How to answer out loud". These are original structure, left in place. They may trip the one-bold-per-section rule.
- Chapter 19 prose growth is +39.2% by the guard measure, near the +40% ceiling. Total wc growth is +32.3%.
- No `$...$` math with stray backticks was found in these three chapters, so nothing was logged for repair.
- The first-person Part 20 lines were kept, including "I ran" and "my reasoning". Each honest-uncertainty line was kept in natural voice.
- Step 6 and 7 of the chapter 21 lab and step 6 of the chapter 20 lab remain "not run". Those statements were preserved as in HEAD.
- Ledger rule: `planning/EXTERNAL_EDITS.md` was not edited, as instructed.
