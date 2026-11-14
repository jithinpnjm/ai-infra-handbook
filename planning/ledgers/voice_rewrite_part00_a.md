# Voice rewrite ledger: part 00 orientation (chapters 0.1, 0.2, 0.3)

Scope: docs/part-00-orientation/01, 02, 03. Not committed. EXTERNAL_EDITS.md not edited (step 6 skipped per run instructions).

## Results

| File | wc -w before | wc -w after | wc growth | guard words (before to after) | guard hard failures | new numbers | lost numbers | chain gate | span check |
|---|---|---|---|---|---|---|---|---|---|
| 01-the-ai-factory-landscape-and-the-roles-in-it.md | 1960 | 2666 | +36.0% | 1837 to 2543 (+38.5%) | 0 | 0 | 0 | 0.0 | {} |
| 02-how-to-use-this-book-and-set-up-your-labs-mac-gcp-gke-nebius.md | 551 | 753 | +36.7% | 457 to 659 (+44.2% by guard count) | 0 | 0 | 0 | 0.0 | {} |
| 03-learning-paths-by-role-platform-mlops-llm-inference-hpc-gpu-cloud.md | 457 | 590 | +29.1% | 344 to 477 (+38.7%) | 0 | 0 | 0 | 0.0 | {} |

Build: `npm run build` and `node tools/check_mermaid.mjs` were not run (the run brief said no npm build). Mermaid blocks are byte-identical to HEAD.

Note on ch02 guard count: the guard counts 457 words for the original where wc -w gives 551 (tables and code tokens are treated differently). Growth by wc -w is +36.7%, inside the band. Guard growth is +44.2%, which is over 40 by its own count. Owner to decide whether to trim roughly 30 words from ch02 if the guard count is the gate.

## What was kept (rule 5)

- Front matter, H1 and every section heading, in order.
- Every inline code span (span check empty on all three), all fenced code blocks, all Mermaid blocks, all tables.
- Checkpoint blocks: ch01 has 4 `<details>` blocks with answers unchanged. ch02 has 3 numbered items in its original form. ch03 has 3 numbered items in its original form.
- Ch01 Sources and review notes, unchanged, including the "Earlier draft" bullet and the note that the Llama 3 figures were quoted from memory and not re-fetched.
- Ch02 setup list items (3) and both sanity-check commands, verbatim.
- Ch02 "untested here" wording in the prose (italic, not backticked) is the chapter's one honest status line. Ch01 keeps "not re-fetched" in its Sources.

## Each section opens with a situation

- ch01: intro (first week on a new team), what a GPU server is (colleague pulls a server from the rack), the layers (a user reports a slow job), training versus inference (two teammates say it is broken), training job end to end (teammate's job about to start), inference request (user types in a chat window), what goes wrong at scale (job restarted every few hours on a large cluster), the roles (pager at night), common failure (dashboard shows low utilisation), checkpoint questions (lead-in only).
- ch02: how chapters are built (opening a chapter for the first time), three lab venues (which lab suits a namespace exercise), minimum setup (first evening with the book), cloud labs (a bill with an unknown GPU node), how it fails (a lab that worked last week fails today), checkpoint (lead-in only).
- ch03: intro (joined a team running a GPU Kubernetes platform), rules of thumb (term from earlier unclear), how it fails (colleague asks which chapters first), checkpoint (lead-in only).

## Needs source (general explanations added, not from the original text)

These are general definitions and mechanisms that remain in the rewritten text. None adds a number. Check each against the gem books or vendor docs before a final pass.

- ch01: a token is a small piece of text, so even a short answer is made of several tokens.
- ch01: an accelerator is any chip built to speed up one kind of work.
- ch01: the fabric is the network that joins the servers, and collective operations are the steps where many GPUs exchange data together.
- ch01: Slurm as a job scheduler that decides which jobs run on which machines; MPI as a common way for machines to send messages; HPC as the older world of large scientific simulations.
- ch01: RoCE expansion (RDMA over Converged Ethernet) and RDMA as remote direct memory access.
- ch01: NCCL expansion (NVIDIA Collective Communications Library) and that it runs collectives such as all-reduce.
- ch01: optimiser state as the set of running numbers the training method keeps.
- ch01: model weights as the learned numbers that make up the model.
- ch01: KV expansion (key and value), the two kinds of intermediate results kept for each token.
- ch01: a switch port is one connection on a network switch.
- ch01: SRE expansion (site reliability engineering) and its one-line definition.
- ch01: a driver is the software that lets the operating system talk to the GPU.
- ch01: a replica is one running copy of the model; an engine is the software that loads the model and runs it on the GPU.
- ch01: GPU, CPU, NIC and BMC expansions were kept from the original except the NIC and GPU/CPU expansions, which are added. Verify.
- ch02: a mental-model diagram as a picture of how the parts fit together.
- ch02: "so you can stop at the level you need" and "read it as an example of the shape of the output" are added reading advice, not facts.
- ch03: none added beyond the reading-order advice.

## Unresolved

1. ch03 table (locked, not edited): "14 (parallelism)" under AI networking points at Part 14 as a whole. The parallelism chapters in docs/part-14-training-finetuning are 04 to 07 (data parallelism, FSDP, DeepSpeed, Megatron parallelism). Similar: "12 (NCCL)" and "12 (RDMA basics)" point at the whole of Part 12; the NCCL chapters are 15 to 18 and the RDMA chapter is 02. Table is locked by rule 5, so the owner must decide whether to change the table.
2. ch02 checkpoint block uses the plain numbered form with italic answers, not `<details><summary>` as RULES_AND_WORKFLOW section 1 item 10 describes. Kept byte-identical per rule 5. Owner to confirm which form this part uses.
3. ch02 "Each chapter goes basics, then intermediate, then advanced" is an original claim about all chapters. Not verified here.
4. ch01 Llama 3 interruption figures (466, 419, 78 percent, 54-day, 16,384 H100) are unchanged from the original and still flagged in its Sources as quoted from memory, not re-fetched.
5. ch01 "Parts 1-4" through "Parts 14-15" mapping and ch03 Part references checked against docs/ folder names: all chapter numbers cited exist (for example 2.22-2.25, 9.9, 10.10, 11.20 and Parts 16-17).
6. Ch02 guard count growth +44.2% (see note above).
