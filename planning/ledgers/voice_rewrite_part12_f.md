# Voice rewrite ledger: Part 12, chapters 16, 17, 18 (run "f")

Scope: docs/part-12-ai-networking/16-nccl-topology-channels-transports-and-environment-variables.md, 17-nccl-tests-and-fabric-benchmarking.md, 18-nccl-debugging-hangs-timeouts-and-errors.md. Nothing committed. EXTERNAL_EDITS.md not touched (per run instructions). `npm run build` and `node tools/check_mermaid.mjs` not run (run instructions say no npm build). Mermaid blocks, code fences, tables, headings, front matter, checkpoint questions and the Sources section are byte-identical to HEAD.

## Per chapter

| Chapter | Words before (wc -w, HEAD) | Words after | Growth | Rewrite guard | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 12.16 NCCL topology, channels, transports and environment variables | 12925 | 17290 | +33.8% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 per 1000 words | {} |
| 12.17 NCCL tests and fabric benchmarking | 14118 | 18958 | +34.3% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 per 1000 words | {} |
| 12.18 NCCL debugging: hangs, timeouts and errors | 15548 | 19908 | +28.0% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 per 1000 words | {} |

Guard output (last line each): 16 "words 9499 -> 13864"; 17 "words 9814 -> 14654"; 18 "words 11282 -> 15642" (the guard's own non-code word column; the growth figures above use raw `wc -w` on the whole file, which includes the locked checkpoint and Sources tail).

## What changed

- Every prose group opens with a situation or a plain picture (a stalled job, a relay team, a car with a slipping clutch, a kitchen timer, a mailing list, a shared attendance sheet). The original situation openers were kept where they already fit.
- The "Outcomes" and "Expected learning outcomes" lists were rewritten as a plain paragraph of what the chapter walks through. No "you will be able to" lines remain.
- The Interview angles in 12.18 were merged back into one group (the four questions were one list block in the original). Bold question labels were removed so each section has at most one bold idea. Interview content and numbers are unchanged.
- Exercises in 12.16 (six), 12.17 (six) and 12.18 (six) keep the same count and the same commands and inputs. Multi-part items were split into short single-question sentences. The nested (a)(b) items in 12.18 were flattened.
- Lab sections: the status sentence appears once above the lab in each chapter ("These steps were not run on a live cluster"). The 12.17 lab output intro lost "in this workspace" wording. The 12.18 Step 2 closing sentence was shortened and points at live hardware.
- Residue removed from body prose: "(untested here)" outside backticks in prose (12.18 commands intro and layer table intro), "untested in this workspace" (12.17), "this chapter did not run them on live hardware" repeated (12.18). Spans inside headings, code comments and table headers were kept.
- Code fences, tables, Mermaid, headings and front matter untouched.

## Needs source

These general explanations or inferences were added in prose. They are not in the original text.

12.16
- Channel buffers are allocated when the communicator is created (2.2 explanation).
- Each doorbell is rung once per small message, so many small messages make the doorbell cost add up (3.1 IBGDA paragraph). Inference.
- The four copies in host memory on the traditional path are the reason GPUDirect RDMA matters most for large tensors (3.1 copy paragraph). Restates the original, but the cost-on-memory-bus wording is general.
- Analogies only (no facts): highway and country road, relay teammate, stage manager, dinner-party seating, kitchen with two stoves, bus-map distances, photocopier and corrected master.

12.17
- A compiler does its work the first time it sees a shape, and CUDA Graph capture records steps once (warmup paragraph). General PyTorch behavior.
- A dropped link can show up as later log lines on other nodes (kernel timestamps paragraph is in 12.18, not 12.17). General operations advice.
- Analogies only: relay race for a barrier, kitchen shift for phases, car speed limit for peak FLOPs versus MFU, car after winter for cold starts, bakery for silent corruption, bench press for nccl-tests, bus wait times for percentiles, restaurant for LLM latency metrics.
- Advice: check formula by hand once before trusting a script; record the number of ranks next to each saved result.

12.18
- Writing down the exact port label before a cable or transceiver replacement keeps repair tickets accurate (advice, not sourced).
- Clock drift across nodes; sorting by the job's own log order when clocks disagree (advice, not sourced).
- A Flight Recorder keeps only the last few entries in memory (general description of the ring buffer; the original states the N entries).
- Interview answer advice: do not reboot the whole cluster before you know which rank failed; raising the timeout first is the wrong first action (advice, not sourced).
- Runbook practice: dated changes, saved baseline lab output, saving command output with job name and time (advice, not sourced).
- Analogies only: relay team with a missing runner, building inspection from the basement, car with a slipping clutch, kitchen timer, shared attendance sheet, closed highway lane, phone line with static, construction crew, half-the-street bisection (leaking pipe).

## Unresolved

- Math with stray backticks: checked with a line-based scan of every `$...$` span in the three bodies. Zero found. Nothing was repaired.
- The 12.18 interview answers were merged into one list group. The question labels now appear as plain quoted text, not bold.
- Locked headings still contain "(untested here)" and "(Verified Here)" and "Verified run" wording. These are headings or table headers and were kept because the span check counts them.
- The tool reported "file modified on disk since last read" notices while I edited 12.16, 12.17 spec, and 12.18. The changes were my own applied edits. No other writer was identified. Worth a look if another run is active on these files.
- 12.18 growth is +28.0%, which clears the +27% floor but is below the +30% aim. Adding more body paragraphs would bring it closer to +30%, but the locked tail limits how much the total can grow.
- Mermaid check and `npm run build` were not run.
