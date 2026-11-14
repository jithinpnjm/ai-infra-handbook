# Voice rewrite ledger: Part 13 chapters 04, 05, 06 (batch b)

Scope: `docs/part-13-ai-storage/04-lustre-for-ai.md`, `05-beegfs-weka-vast-and-object-storage.md`, `06-data-loading-small-files-and-metadata.md`.
Not committed. `planning/EXTERNAL_EDITS.md` not edited (per run instructions).
Method: front matter, tables, fenced code and Mermaid blocks, headings, the checkpoint section and the Sources section were carried over byte-for-byte from HEAD. Only prose and list items were rewritten. Each chapter was assembled from a template with the locked blocks pulled from `git show HEAD:<file>`.

## Results

| Chapter | Words before (wc -w) | Words after (wc -w) | Growth | rewrite_guard | chain_gate | Span check |
|---|---|---|---|---|---|---|
| 04-lustre-for-ai | 13993 | 18235 | +30.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.1 per 1000 words | `{}` |
| 05-beegfs-weka-vast-and-object-storage | 11481 | 14880 | +29.6% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 0, lost 0 | 0.3 per 1000 words | `{}` |
| 06-data-loading-small-files-and-metadata | 12226 | 15804 | +29.3% | 0 hard failures, new numbers 0, lost numbers 0, new code spans 2 (guard count; see Unresolved 8), lost 0 | 0.0 per 1000 words | `{}` |

Build: `npm run build` and `node tools/check_mermaid.mjs` were not run (run instructions say no npm build). Mermaid blocks are byte-identical to HEAD, so their status is unchanged from HEAD.

Honest status: each chapter keeps "untested" or "not run" in prose. 04 uses the existing "`untested here`" status sentence in Commands and the lab note. 05 and 06 keep "not run" in the lab Venue section.

## Section openers

Each section opens with a situation or a picture (for example "Picture a training run...", "Imagine a new engineer asks...", "Suppose your manager asks..."). Outcome lists were rewritten as plain paragraphs. Exercises were split into single-question sentences with the same count (04: 6, 05: 6, 06: 6). Common first mistakes, interview items and lab steps keep their counts.

## Needs source (general explanations added, not from the original text)

Chapter 04:
- Definitions of parallel file system, MGS, MDS, MDT, OSS, OST, RPC, RDMA, NUMA socket, NVMe, DMA, FUSE, page cache, extent lock, rank, fencing, east-west traffic, in-band management network, all-reduce, pinned memory, RAID 10, extended attribute, failure to probe kubelet.
- Little's Law explanation (the rule itself is in the original).
- The walkthrough of a 45.2 ms open latency night in "How it fails" (illustrative, no new data).
- Statement that a single client with wrong mount options fails in a way that is hard to trace (general practice).

Chapter 05:
- Definitions of IOPS, NVLink domain, RAG, synchronous dump, IAM signatures, TLS, daemon and user-space, failure domain, erasure coding trade, polling mode, interrupt jitter, cache coherency, O_DIRECT, io_uring, endurance, LRU, tail latency, mdtest use.
- Analogies: the three storage shelves, the SCM receiving area and dock, the cache shelf. None adds a number.
- Hypothetical example in "How do you pick?" (a team of two engineers). It is illustrative, not a claim about any real team.
- Claim that the metadata ceiling should be found on your own hardware before planning (advice, not a fact).

Chapter 06:
- Definitions of wall-clock time, Tensor Core, stat, open, read, close, SM, PCIe bus, collation, `__getitem__`, `collate_fn`, persistent workers, pread, io_uring, JSONL, PII, MinHash deduplication, padding, straggler rank, computation graph, nvJPEG, scaling efficiency, DistributedSampler.
- Explanation of why a faster disk does not cut metadata wait (reasoning from the original figures).
- Explanation that each host-device copy is a separate bus trip (general).

## Unresolved

1. Chapter 05 internal figures disagree. Interview angle 4 says Epoch 1 "takes 3 hours" and Common first mistake 3 uses a "180 minutes" first epoch, while the table and the lab use a 45.3 min cold wait. Kept as written (facts must not change). Owner should reconcile.
2. (Removed on review: the cache-fill figures in Exercise 6 and lab check 23 are consistent.)
3. Chapter 06 lab output block (locked) still contains "Vol 06" and "Lab 04" references, and the Sources section still says "Volume 15" and "Vol 06". These sit inside locked blocks, so they were not changed. The reader-text residue in prose is zero.
4. Chapter 06 `Outcomes` in HEAD was a numbered "By the end of this chapter, you will be able to" list. It is now a plain paragraph. The four skills are unchanged in content.
5. Math `$...$` in chapter 04 (`$C$`, `$S$`, `$O_0$`, and the `$C$` stripe math in section 1.2) is plain math with no stray backticks. Left unchanged.
6. Chapter 04 "How it fails" intro and Chapter 05 "How it fails" intro were rewritten to open with a situation. Table rows are unchanged, including original "Fix" column wording.
7. Chapter 04 `(untested here)` labels stay inside code blocks, as the span rule requires. The prose status sentence is unchanged.
8. Spans added in prose (a set difference against HEAD, so it is broader than the guard count): 04 `/lustre`, `lfs getstripe`, `llite`; 05 `/beegfs`, `mdtest`; 06 `/dev/shm`, `.bin`, `.idx`, `stat`, `read`, `% time`, `usecs/call`, `__getitem__`, `next(data_iterator)`, `collate_fn`, `tar -tf`, `dshm`, `D`. The guard reports 2 new spans for 06. The rest are typed commands, paths or manifest names. Owner may want to confirm before commit.
