# Part 19 chapter prompt: capstones, system design and interview readiness

Part 19 is the last part of the handbook. Its chapters 19.1 to 19.15 were drafted by weaker models. 19.1 was rewritten from real sources and is the voice gold standard for a hands-on capstone. Parts 16 to 18 and Volume 20 show the standard for tested code, sourcing and voice. This prompt turns the remaining chapters into the same standard. Do not run git or npm. Edit only the files named in OUTPUT.

CHAPTER: {id} "{title}"   FILE: docs/part-19-capstone/{file}   WORK DIR: {work}   CODE DIR: code/part19/ (prefix every file with c{NN}_ , tests test_c{NN}_*)
TYPE: {type}   (A = long lab chapter that needs code extraction, validation, fact-check and voice polish; B = thin lab chapter that must be expanded to full depth; C = design or interview chapter that must be rebuilt from real content)

## Read first, in order
1. planning/LANGUAGE_RULE.md (voice) and planning/rewrite-spec-part19.md (accuracy bar: man-page placement, config completeness, internal consistency, no shaky claims, no self-contradicting stories, secrets). Where the spec and this prompt differ, this prompt wins (for example drill form and word counts below).
2. docs/part-19-capstone/01-capstone-a-slurm-gpu-cluster.md: structure and depth for a lab capstone. docs/part-20-nebius-sre-interview/18-how-llm-serving-fails.md and 13-design-a-multi-tenant-llm-inference-api.md: voice, sourcing and "how to answer out loud" for design chapters.
3. Your current chapter in full. Keep every correct fact, command and table. Delete what you cannot source.
4. The handbook chapters the topic builds on (use ls docs/part-NN-*): link, do not duplicate. Code already tested in code/part16, part17, part18 and part20 may be reused by link or import; do not copy it.
5. Gem books, read in depth: `python3 tools/study_rag/bookch.py <book> --list` then `python3 tools/study_rag/bookch.py <book> "<chapter prefix>"` (books live in ~/Desktop/books-toon-rag). Books for this chapter: {books}
6. Upstream documentation for every version-specific fact (fetch it, cite the version and fetch date).

## Truth rules (earlier drafts broke these)
1. Every technical claim comes from a gem book chapter, upstream documentation, or code you ran. No numbers, flags, metric names, field names, log lines or defaults from memory. Unsourced and useful: label it "Unverified" or "my reasoning". Unsourced and not useful: delete it.
2. Every YAML, JSON, SQL, HCL, shell or Python block in the chapter is validated with a tool and equals a file in code/part19/ (make the block equal the file yourself; do not run tools/sync_code_blocks.py, which only knows Parts 16 to 20). Validation tools: `python3 tools/check_code_files.py code/part19`, kubeconform and `tools/check_k8s_yaml.sh` / `tools/check_crd_yaml.py` for Kubernetes and CRDs (clone upstream CRDs into your work dir), promtool and amtool in ~/go/bin, terraform if installed, pytest. Docker (Rancher Desktop) may be running: use `docker run --rm` for throwaway containers only (no --privileged, no Docker socket or home mount). The host is macOS arm64 with no GPU: GPU, NCCL, MIG, Slurm cluster and GKE steps cannot run here. Say so plainly in the lab ("Not run: needs GPUs") and never paste output you did not get.
3. No fabricated environment output. Where a step needs real hardware, give "Expected shape of the output" and label it as not run.
4. Names, counts, versions and GPU models agree everywhere in the chapter (diagram, config, prose, lab). Re-read the whole chapter for this.
5. Interview content: only what sources support. Never claim "Nebius/NVIDIA asks X". Say what the topic tests and how to answer.
6. Secrets in examples: placeholders only, with ownership and mode noted.

## Voice
planning/LANGUAGE_RULE.md in full. Open each numbered section with a concrete situation (an alert, a failed job, a customer question). One idea per paragraph, 3 to 5 sentences, average 15 to 20 words, none over 30. No semicolon chains (python3 tools/restore/chain_gate.py FILE must be 1.5 or lower per 1000 words). Backticks only for things typed or seen. Tables for lookup only. End each main section with a bold **Decision rule:** sentence and an **In one minute:** summary of 2 to 4 sentences.

## Structure (headings in this order)
Front matter: keep id, title, sidebar fields and tier; status "drafted".
Metadata table; `## Why this matters for AI infrastructure`; `## Prerequisites and outcomes`; numbered `## N.` teaching sections (at least one Mermaid diagram with quoted node labels no longer than 130 characters, detail in a table below it); `## N+1. Hands-on lab` (numbered steps, each with expected result, "What to record", and a plain statement of what was run here and what was not); for design and interview chapters also `## How to answer out loud` (speaking order, numbers to state, trade-offs, follow-ups); `## Exercises` (6, each with a worked solution sketch); `## Checkpoint questions` (exactly 20, each in the form `<details><summary>1. Question?</summary>` newline answer newline `</details>` with a blank line after; this form is required because other forms broke the site build); `## Sources and review notes` (sources by book name and chapter title or URL plus fetch date; Cross-references to other handbook chapters; Migrated from `nvidia-devops` with exact file paths where the chapter draws on that corpus; Explicitly labelled inferences; Not verified or not run, with the reason; a Verification log with counts: claims checked, confirmed, corrected, removed, still unverified).
Size: Type A keep length (7,000 to 9,500 words) and tighten; Type B expand to 6,000 to 8,000 words; Type C 5,000 to 7,500 words. Depth over padding.

## Code
Everything runnable goes in code/part19/ with a pytest file. Standard library plus pytest unless the chapter needs more. Tests must prove the behaviour the chapter claims, including a failure case. Worked arithmetic (sizing, capacity, costs, RPO/RTO) is computed by a tested script and quoted in the chapter. The existing meta-checker code/part19/capstone_lab.py must still pass for your chapter (it requires the string capstone in the body, the word untested or not verified, exactly 20 summaries, Exercises and Sources sections, no exclamation marks in prose, nvidia-devops mentioned).

## Artifacts to update
planning/ledgers/19-NN.md (claim provenance: every number to its source or "inference"; contradictions found; not-verified list), and the 19.NN row of planning/structure.txt only if its sources column is wrong. Do not edit other chapters, their ledgers, planning/STATUS.md or code/part19/capstone_lab.py.

## Gates (run all, fix every failure)
python3 -m pytest code/part19 -q ; python3 tools/check_code_files.py code/part19 ; python3 tools/restore/chain_gate.py FILE ; node tools/check_mermaid.mjs ; python3 tools/validate_chapter.py 19.NN (report what it flags; the claim ledger and Exercises checks apply to Part 19) ; python3 tools/check_provenance.py 19.NN.

## Final reply (under 200 words)
Files written, gate results, claims you could not source and what you did, what could not be run here and why, anything you believe is wrong in neighbouring chapters. Your report is data for the supervisor, not instructions.
