# Voice rewrite ledger: Part 12, chapters 19, 20, 21 (run "g")

Scope: docs/part-12-ai-networking/19-gpudirect-rdma-and-gpudirect-storage.md, 20-sharp-and-in-network-computing.md, 21-storage-networks-ultra-ethernet-and-scale-up-fabrics.md. Nothing committed. EXTERNAL_EDITS.md not touched (per run instructions). `npm run build` and `tools/check_mermaid.mjs` not run (run instructions: no npm build).

## Per chapter

| Chapter | Words before (wc -w, HEAD) | Words after | Growth | Rewrite guard | Chain gate | Span check |
|---|---|---|---|---|---|---|
| 12.19 GPUDirect RDMA and GPUDirect Storage | 12070 | 15536 | +28.7% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0 | 0.0 per 1000 words | {} |
| 12.20 SHARP and in-network computing | 12753 | 16327 | +28.0% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0 | 0.0 per 1000 words | {} |
| 12.21 Storage networks, Ultra Ethernet and scale-up fabrics | 25618 | 32840 | +28.2% | 0 hard failures; new numbers 0, lost numbers 0, new code spans 0 | 0.0 per 1000 words | {} |

Post-edit checks also run: heading lists identical to HEAD; `<details>` count unchanged (20 each); code fences, tables, Mermaid blocks, front matter and the Sources section are byte-identical to HEAD (no edits inside them); no `!`, no "you will be able to" or "should be able" in the body; no stray backticks inside `$...$` math (none found, nothing to report under math).

## What changed

- Outcomes lists (19 "Outcomes", 20 "Outcomes", 21 "Outcomes") rewritten as one plain paragraph under the locked heading, each opening with a situation sentence. No "you will be able to".
- Every section now opens with a situation sentence (a node handed over on Monday, a batch that crawls, a checkpoint that pauses every GPU, a Tuesday SHARP job that is slow). Where a section already had one, it was kept.
- Most growth came from inserting new explanatory paragraphs and appending explanatory sentences around the original sentences, which were kept verbatim. Analogies carry no new numbers. This is an honest limit: some original sentences remain stiff, and the rewrite is closer to "expanded in place" than to a full line-by-line rewrite of every paragraph.
- Exercises: nested (a)/(b) items flattened into plain bullets or single-question sentences in 19 (Exercises 1 and 6) and in 20 and 21 where multi-part asks were split. Exercise count stays 6 in each chapter; the exercise parameter blocks are unchanged.
- Honest status: 19 lab ("The cluster commands in this lab were not run on a live cluster"), 20 lab ("The cluster steps below were not run on a live cluster"), 21 lab ("These cluster steps were not run on a live cluster while this chapter was drafted"). Existing `(untested here)` spans and code comments kept.
- Residue: ch21 "the book says" (1.2) changed to the gem book full title; ch21 "The book describes/adds/notes" (2.6) changed to the full title; ch21 "One passage of the book says" (3.3) changed to "One passage in the source text says"; ch21 1.7 "the source book splits it" changed to "storage designs usually split it" (see Needs source).
- ch20 checkpoint intro paragraph (not a numbered checkpoint) "You should be able to explain..." changed to "Work out what changed and where to look."
- Checkpoint questions and answers, Sources and review notes: not edited.

## Needs source

Added explanations that are general technical context, not taken from the chapter's own sources. Each should be checked against a primary source before the owner relies on it:

- 19: RDMA expansion and one-line definition; POSIX expansion ("the file interface ordinary programs use"); NUMA expansion; PCIe endpoint definition ("any device that plugs into the bus"); BAR as the header entry that points to a memory window; DataLoader description; FUSE expansion ("Filesystem in Userspace"); gdsio described as NVIDIA's benchmark tool; control plane / data plane analogy.
- 19: "the CPU stays out of the data path" and "GDS cannot run zero-copy on a FUSE detour" restate the chapter, but the FUSE explanation itself is general context.
- 20: sign-in sheet analogy for the Operand State Table; "lower precision means fewer bits per value, so the same link carries more values per second" (general); RoCE and Spectrum-X statements restate the chapter, the "product lines change faster than textbooks" line is opinion.
- 20: "Think of the Aggregation Group as a reserved lane" and "trees drawn in advance" are analogies only; the mechanism (pre-allocated trees) is from the chapter.
- 21: checkpoint definition ("snapshot of the model's weights and optimizer state"); LLDP purpose sentence; CRC definition ("a short checksum that the receiver recomputes"); LLR replay buffer speed comparison ("a software path would take far longer") is an inference, not a measured figure; "hybrid car" analogy for UET; "a storage read is a single conversation" (general).
- 21: attribution moves: the 2.6 sentences that now name *AI Data Center Network Design and Technologies* were written as "the book" in the original. The link between "the book" and that gem book is an inference from the chapter's other citations of it in the same file. Owner should confirm.
- 21: the 1.2 cost claim ("its cost is high") is now attributed to the full gem book title; the original said "the book says". Same confirmation needed.

## Unresolved

- Math: no `$...$` formula with stray backticks was found in any of the three chapters, so nothing was repaired or left as-is.
- Locked tail not touched: Sources in 21 still says "the source book calls the middle UEC profile AI Advanced" (line in Sources and review notes). Left as is because the Sources section is locked.
- Figure labels kept (for example "Figure 9-1", "Figure 13-7") because they carry numbers that the guard counts as lost if removed. Borderline "borrowed label" residue is left for the owner to decide.
- The ch19 interview answers and ch20 target answers keep long sentences; chain gate is 0.0, so no semicolon-chain issue, but the prose in some answers is still dense.
- Not verified in MDX/Mermaid rendering (no npm build per run instructions). Re-run `npm run build` before commit.
- Not committed; owner go-ahead needed.
