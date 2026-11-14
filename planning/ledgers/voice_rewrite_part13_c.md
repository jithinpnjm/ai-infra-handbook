# Voice rewrite ledger: Part 13 chapters 07, 08, 09 (batch c)

Scope: `docs/part-13-ai-storage/07-checkpoint-architecture-and-recovery.md`, `08-capacity-performance-and-cost-planning.md`, `09-storage-troubleshooting.md`.
Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).
Method: front matter, tables, fenced code and Mermaid blocks, and the checkpoint and Sources tail were restored byte-for-byte from HEAD by a template assembler (scratchpad), so only prose, headings and list items were written by hand.

## Status

| Chapter | Words before (wc -w) | Words after (wc -w) | Growth | rewrite_guard | chain_gate | Span check |
|---|---|---|---|---|---|---|
| 07-checkpoint-architecture-and-recovery | 5614 | 7356 | +31.0% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 per 1000 words | `{}` |
| 08-capacity-performance-and-cost-planning | 13150 | 16832 | +28.0% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.0 per 1000 words | `{}` |
| 09-storage-troubleshooting | 12797 | not started | n/a | not run | not run | not run |

Chapter 09 is NOT rewritten. The file on disk is still the HEAD version. The run stopped because the context window ran out after chapter 08 (the chapter is 764 lines, and the first 438 lines alone exceed the read cap).

Build: `npm run build` and `node tools/check_mermaid.mjs` were not run (the run instructions say no npm build). Mermaid blocks are byte-identical to HEAD.

Honest status: chapter 07 keeps "not been run on a cluster for this edit" in the Commands section and the Sources tail keeps "not run on a cluster". Chapter 08 keeps "were not run on live hardware" in the Commands intro. Chapter 09 still has the original "(untested here)" comments inside its bash blocks, which are locked code and were left as they are.

## Section openers

Each section in 07 and 08 opens with a situation (a training team, a storage alarm on a Friday, a capacity request on a Monday, a node that loses power mid-save, and so on). The outcomes list in 07 and 08 was rewritten as a plain paragraph with no "you will be able to". The exercises in 07 were split into single-question sentences, and the count is unchanged (6 in each chapter). Interview and "Common first mistakes" items keep their counts.

Known gap in 08: the six exercises still contain several imperative multi-ask sentences. They are not yet split to one question per sentence (rule 9). Revisit in a follow-up pass.

## Needs source (general explanations added, not from the original text)

Chapter 07:
- BF16 stores each value in half the space of an FP32 value. Adam's two FP32 moments are what make the optimizer state the large part of the file.
- Pinned memory cannot be moved or paged out by the operating system.
- `fsync` flushes written bytes to the device, and an atomic rename within one filesystem either completes or does not happen.
- Striping as dealing cards across several hands (analogy), and the relay race analogy for the staged write path.
- Restore correctness: every element must be read exactly once (stated from the lab check; the explanation of why is new).

Chapter 08:
- Payback as the division of upgrade price by daily waste (arithmetic from the original; the framing sentences are new).
- Parking-lot analogy for the thirty percent headroom (free space lets the allocator place large writes in clean blocks).
- Library analogy for the four storage tiers.
- Cashier-and-back-office analogy for two-tier staging.
- Bus analogy for the Spot discount and the two-minute warning.
- Stripe width as cutting a file into pieces (more pieces, less parity overhead, more machines in each read and rebuild).
- Advice on measuring the stall fraction from utilization gaps and data-loader wait (method is new, not sourced).
- Advice on sequence: write down growth rates per data kind, and check units first when a result is off by a large factor.

## Unresolved

1. Chapter 09 not started. Full rewrite still owed. The file has 764 lines. Read it in two passes (offset 1 to 438, then 439 to 764) and use the same template-and-assemble method used for 07 and 08 (locked blocks restored from HEAD).
2. Chapter 08 exercises not split to one question per sentence (see Section openers).
3. Chapter 08 math: the Protection Scheme table header uses `$N$` and `$K$` with no backticks. The table is locked and was left unchanged. No stray backticks were found in chapter 08 math. Chapter 09 has not been checked for this yet.
4. Chapter 08 keeps the bold interview question titles (one bold idea per item, but several items per section). Left as in the original.
