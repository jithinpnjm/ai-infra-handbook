# Voice rewrite, Part 20 chapters 25 to 27 (batch i)

Scope: `docs/part-20-nebius-sre-interview/25-promql-grafana-and-tracing-traps.md`, `26-the-stress-interview-production-incident-role-play.md`, `27-post-mortems-on-call-and-incident-leadership.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (run instruction). No `npm run build` (run instruction).

Method: each file was rebuilt from HEAD with a splice step. Front matter, every fenced block (Mermaid, YAML, bash, Python, text, the markdown fixture), every table, the 10 checkpoint `<details>` blocks per chapter, and the Sources and review notes tail (through the Verification log) are byte-identical to HEAD. Headings are identical. Prose was rewritten in place or added before the locked element each section needed.

## Results

| File | Words before (wc) | Words after (wc) | Growth | Prose growth (guard) | rewrite_guard | chain_gate | Span check |
|---|---|---|---|---|---|---|---|
| 25 PromQL, Grafana and tracing traps | 6780 | 9070 | +33.8% | 6062 to 8352, +37.8% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 2 to 2 | 0.0 | `{}` |
| 26 The stress interview | 8801 | 11882 | +35.0% | 7455 to 10536, +41.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 1 to 1 | 0.0 | `{}` |
| 27 Post-mortems, on-call and incident leadership | 7841 | 10196 | +30.0% | 5932 to 8287, +39.7% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0, residue 1 to 1 | 0.0 | `{}` |

Other checks, run on the final files:
- `node tools/check_mermaid.mjs`: `checked 776 diagrams, 0 failed`.
- Code fences identical to HEAD in all three. `<details>` count 10 in each. Table line counts identical (25: 35, 26: 141, 27: 75). Headings (`#`, `##`, `###`) identical in order and text.
- Banned-pattern scan of prose (code and tables removed): no exclamation marks, no `you will be able`, no `should be able`, no `you will learn`, no raw `<` or `{`, no `$` outside code.
- Honest status kept once per chapter in the locked tails ("Not verified") and in the 26 lab intro ("Not run interactively here"). Lab text in 25 keeps "Every step below was run on macOS." unchanged.
- Lab and exercise counts unchanged: 25 has steps 1 to 8 with 4b (9 items) and the 15-row exercise table; 26 has steps 1 to 8; 27 has steps 1 to 6. Commands and expected outputs unchanged.
- Every section opens with a situation sentence, including the H2 sections that had no prose in HEAD (Core ideas, Drill questions, Common mistakes, Connections, Worked scenarios, Hands-on lab, How to answer out loud).
- Numbers: the guard reports 0 new and 0 lost. Spelled-out number words added were checked against the original; the ones that remained are either original wording or non-numeric ("a few seconds").

## Needs source (general explanations added; no Nebius facts added)

Chapter 25:
- "Monotonicity" as the plain word for only going up (idea 1).
- The "ruler" picture of rate extrapolation (idea 1, my picture).
- "Still too thin for a stable answer" for two samples (idea 2, reasoning).
- "Interpolate" as "estimate a value between the two bounds" (idea 4).
- `le` read as "less than or equal to" (idea 4). `+Inf` as "everything above the last named bound" and `NaN` as "not-a-number" (idea 4).
- KV cache as the memory for each running request's working state (idea 5).
- A gauge as a value that rises and falls on its own (idea 5). `deriv` as the slope of a gauge (idea 5).
- RED expanded as request rate, errors and duration (idea 5). USE examples "such as a GPU or a disk" (idea 5).
- Alertmanager as the component that routes alerts (idea 9). Grouping key as the labels that decide which alerts travel together (idea 9).
- "A join that needs a hack ... usually telling you the labels are wrong upstream" (idea 7, my reasoning).
- Storing traces costs money and attention; "without that rule the trace says success" (idea 13 and 14, reasoning).
- The span-status and first-token wording is original. The "200 goes out before the first token" sentence is a general streaming explanation.
- Illustrative situations: "a Tuesday night when one exporter stops reporting" (idea 6), "a busy pod next to a nearly idle one" (idea 4), "a Friday afternoon" (idea 12).

Chapter 26:
- Definitions of tail TTFT, retry amplification and "capacity that shrank silently" (intro, from the Nebius case-study wording in the original).
- "Declaring early is a choice ... it can be lowered again later" (core 1, reasoning).
- The four role descriptions in core 1 ("Incident command keeps the overall picture. Operations changes the system. Communication tells people ... planning looks ahead.") These sit next to the Managing Incidents citation. Check them against the book's role wording before publishing.
- Liveness and readiness explained in plain words (scenario 2).
- Ready and registered as two facts (scenario 2, explanation of the drill's scoring).
- A startup probe as a grace period (scenario 5).
- A leaf certificate as the one a server shows to clients, and the CA as the signer (scenario 7).
- Inode as the file's metadata record, and the deleted-but-open space behaviour (scenario 6). The kubelet sentence is original.
- The ndots and search-suffix resolver walk (scenario 8, Production Kubernetes citation is original).
- etcd write-ahead log and fsync as the forced write (scenario 9). "The other members can treat it as failed" (reasoning from the leader-election logs in the original).
- Canary and out-of-band as definitions (scenario 10, Emergency Response citation is original).
- Jitter as a random spread in timing (scenario 4).
- Reasoning: "layers multiply rather than add" (scenario 4 arithmetic), "adding gateways adds more clients making the same retries" (scenario 4), "the pause control has to sit outside the spread" (scenario 10).
- Interview-answer coaching and the core-idea picture sentences (Picture openers) are my reasoning.

Chapter 27:
- STAR expanded as situation, task, action and result (core 1). The five-part shape keeps the STAR rhythm with impact and change lines added (my design).
- "Numbers are not decoration" and "a stronger answer than a blank" (core 1, reasoning).
- "Declaring costs very little, while declaring late can cost the whole night" (core 2, reasoning).
- "A level is a setting, not a verdict" (core 3, reasoning).
- Timeline honesty, owners and "several names" (core 4 and core 5, reasoning).
- Toil versus overhead explanation (core 6). The overhead sentence follows the original "Overhead such as meetings is not toil".
- Runbook as a promise and the Wheel of Misfortune sentence (core 7, reasoning on the original).
- On-call health as a service with a failure mode of people leaving (core 8, reasoning).
- Budget as a public count of minutes (core 9, reasoning).
- Monday-review advice and the three answer-coaching lines in "How to answer out loud" (reasoning, unsourced).

## Unresolved

- One-bold-per-section rule: the chapters keep the bold lead-ins from HEAD. 26 incident sections use bold labels ("Interviewer opens.", "Technical anchor.", "Cause.", "Fix.", "Scoring."), 27 uses bold question lines in "How to answer out loud" and bold lead-ins in the mistakes list, and 25 keeps its bold closing line per idea. These are the chapters' answer structure, so they were left in place.
- Residue: 26 keeps "The book's L40S example" and 25 keeps the "Systems Performance" italic attribution, both original. The guard residue counts match HEAD (25 2 to 2, 26 1 to 1, 27 1 to 1).
- Chapter 27 growth is +30.0% (within the +28% to +40% band, close to the floor). Chapter 26 is +35.0%, chapter 25 is +33.8%.
- Math `$...$` with stray backticks: none found in the three files, so nothing needed repair.
- The "Needs source" items above are the ones to check before publication, especially the Managing Incidents role wording in chapter 27 and the scenario mechanisms in chapter 26.
- Nothing committed. Owner go-ahead needed.
- `planning/EXTERNAL_EDITS.md` was not edited, per the run instruction.
