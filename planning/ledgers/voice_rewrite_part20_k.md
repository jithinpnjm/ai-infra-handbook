# Voice rewrite ledger: Part 20, chapters 31 to 33 (run k)

Scope: `docs/part-20-nebius-sre-interview/31-nebius-ai-cloud-foundation-gpu-fabric-and-platform-choices.md`, `32-token-factory-model-lifecycle-serving-and-economics.md`, `33-ai-factory-solution-architecture-ha-and-recovery.md`. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (step 6 skipped per run instruction). No `npm run build` (per run instruction). Only the three chapters and this ledger were touched. Other chapters in the diff (34 to 36 and others) were edited by other agents and were not touched here.

## Method

Each chapter was rewritten from its prose. Front matter, headings, tables, Mermaid, code blocks, checkpoint `<details>` blocks and the Sources and review notes tail (through the Verification log) were kept byte-identical to `HEAD`. Locked blocks were inserted from `HEAD` by script after drafting, so no copying error could reach them. Every checkpoint question and answer is unchanged.

## Word counts (`wc -w`, HEAD vs worktree)

| File | Before | After | Growth |
| --- | --- | --- | --- |
| 31 AI Cloud foundation | 4908 | 6674 | +36.0% |
| 32 Token Factory lifecycle and economics | 7470 | 9745 | +30.5% |
| 33 AI Factory design, HA and recovery | 6860 | 8855 | +29.1% |

Guard prose-word counts: 31 `4799 -> 6565`, 32 `6855 -> 9130`, 33 `6492 -> 8487`.

## Gates (run on the final files)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three. New numbers 0 and lost numbers 0 on all three. New code spans 0 and lost 0 on all three. Residue counts unchanged on 32 (2 to 2) and 33 (2 to 2). On 31 residue is 5 to 5, the honest "I could not find" and "I did not find" statements from the original.
- `python3 tools/restore/chain_gate.py <file>`: 31 = 0.0, 32 = 0.3, 33 = 0.0 per 1000 words (target 0.2 or lower; 32 is 0.3 and within the 1.5 limit).
- Mandatory inline-span check (HEAD vs worktree, fenced blocks excluded): `{}` for all three.
- Structure, HEAD vs worktree, checked by script: tables identical in order and text (31: 37, 32: 53, 33: 42), H1 to H3 headings identical (31: 24, 32: 28, 33: 28), fenced blocks identical (31 has 1 Mermaid, 32 has 5 fences including Mermaid and Python, 33 has 2), `<details>` checkpoint blocks identical (10 on each), Sources tail identical, front matter identical.
- Banned-pattern scan: no new `!`, no "will be able to", no "should be able to", no "you will learn", no new raw `{`. Raw `<` count unchanged on all three (inside existing tags, Mermaid and code).
- Mermaid: not run. The Mermaid fences are byte-identical to `HEAD`, so `node tools/check_mermaid.mjs` should give the same result as before.

## What was kept (rule 5)

- Front matter, H1 and every heading, in order.
- Every inline code span, every fenced block, every table, every Mermaid block.
- Every number from the original prose. The guard reports 0 new numbers and 0 lost numbers on each file.
- Every evidence tag (`[official]`, `[vendor]`, `[gap]`, `[design]`, `[mine]`, `[inference]`) and every "Not verified" and "Explicitly labelled inferences" line.
- Every checkpoint question and answer. Each drill answer is byte-identical.
- Lab step count (31: 6 steps, 32: 3 steps, 33: 5 steps) and the commands and "Expected" facts in them.
- The honest status lines: 31 "I ran no commands", 32 "Steps 1 and 2 run on a laptop and I ran them. Step 3 ... was not run.", 33 "I ran step 1 and step 2".
- Book attributions as the original gave them: *The Energy Behind AI* (vendor blog), *AI Data Center Network Design and Technologies*, Hands-On LLM Serving and Optimization chapter 6, Production Kubernetes chapter 2, Terraform: Up and Running chapter 3. No new book attribution was added.

## Section openers

Every section now opens with a situation sentence. Locked headings with no body (for example "The core ideas", "Worked scenarios") were left empty, and the first subsection carries the situation. The "What the interviewer is testing" and "How to answer out loud" sections begin with the situation in their first sentence.

## Lab step changes (rule 9)

- 33 step 2 had four facts in one sentence, which broke the two-numbers rule. It was split into four sentences in the same step, each naming one expected result. The facts are the same.
- 33 step 3 had "512 times 10 / 60" in one sentence. It was split into two sentences with the same arithmetic and the same result, about 85.3 GPU-hours.
- 31 and 32 steps were kept close to the original text, with one situation line added above each lab.

## Needs source (general explanations added, no Nebius, book or vendor facts added)

These are general teaching explanations written for this rewrite. None is a claim about Nebius internals. Each should be checked before publication.

- 31: PUE expanded as power usage effectiveness and described as a ratio of facility energy to IT energy (the original gave the definition in words; the expansion of the acronym is general). Weight memory, KV cache, concurrency and quantisation glosses. SIGTERM and SIGKILL as operating system signals (SIGTERM asks for clean shutdown, SIGKILL cannot be caught). NVLink as a fast link between GPUs in one server. InfiniBand as a high-speed network technology. P-Key as the InfiniBand partition key. IAM as identity and access management. Switch and POD glosses. NCCL as NVIDIA's collective communication library and AllReduce as the operation where every rank receives the combined result. NAT as network address translation. VPC as virtual private cloud. Egress. DNS zone. Security group as firewall rules attached to a machine. Erasure coding and close-to-open consistency. Inode as the record of file metadata. S3-compatible as the same API as Amazon S3. Pre-pull. Pending pod. Etcd as the cluster state store. Slurm as a batch scheduler. Preemptible and spot as interruptible discounted capacity. FOCUS as a shared billing data format. Node Problem Detector as a Kubernetes add-on that reports node faults. Xid as an NVIDIA driver error code in the kernel log. ECC as error-correcting memory. Cordon and drain definitions. The statement that a preset name reads as GPUs, vCPUs and memory was removed from the final text, so it is not claimed.
- 32: Post-training, LoRA adapter, drafter and decoding head glosses. Speculation as guessing ahead (general reading of speculative decoding). Batch as a group of requests worked on together. Continuous batching analogy (a bus taking on passengers) with no numbers. Percentile definition for p50, p90 and p99. Federate path as a Prometheus endpoint that returns a chosen set of series. Fail closed as a router refusing when a rule forbids the request. Exponential backoff with jitter as a common client pattern. ZDR expanded as Zero Data Retention (the expansion is also in the original table). Shared rental fleet analogy for the GPU pool.
- 33: SLA as a service level agreement. AZ as availability zone. Snapshot as a point-in-time copy of a disk. Multiply-out explanation for downtime minutes. Supplemental Terms as extra legal text on top of the main terms. Cordon and drain glosses. Reconcile-only controllers and the request path. Write-ahead log as the database change record that makes point-in-time recovery possible. Point-in-time recovery defined as restore to a chosen moment. Capacity block group as the reserved pool both sides draw from. Quorum as the majority of votes needed to agree a write. State file as Terraform's record of what it built. Active-passive as a standby region that takes traffic after a switch. Role as a named set of permissions. Declined card as an outage in disguise (reasoning). Case-study caution and the "door and room" phrasing (my reasoning, labelled as reasoning in the text where it matters).

## Unresolved issues

- 31 section 3: the sentence about how a preset name reads was removed on purpose, because the name reading is not documented. If the owner wants it back, it needs a source.
- 32 section 7 and 33 section 4 keep the original "[mine]" and "[design]" tags, but several added sentences in those sections are my reasoning and are not tagged one by one. Reviewer should check that no added sentence reads as a Nebius fact. The added sentences are general or reasoning sentences, and none states a number or a product behaviour.
- 32 and 33: the locked Verification log text in each file still uses draft-history wording (32: "The earlier draft was found to be mostly about AI Cloud..."; 33: "where the draft called it a customer concern"). These sit in the Sources tail, which is byte-identical to `HEAD` per rule 5. A clean-up of that wording, if wanted, is the owner's call.
- 31 section 2 and 33 section 3 keep the first-person lines about claims that were removed. These are honest status, kept per rule 13.
- Math `$...$` with stray backticks: none found in the three files.
- Mermaid and `npm run build` not run (see gates).
