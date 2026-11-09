# Volume 20 chapter prompt: Nebius Senior SRE, Token Factory (Inference Platform)

Use with `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` (chapter list, research, evidence tags). Fill the `{...}` fields per chapter. Do not run git or npm. Edit only the files named in "OUTPUT".

You are writing one chapter of a study volume for a real person who has an interview for Senior Site Reliability Engineer, Token Factory (Inference Platform) at Nebius. They are a working DevOps engineer. They need to pass a hard, long loop: a Linux console troubleshooting round, a coding round, a system design round, a 30-minute production-incident "stress" round, and a project deep dive. Every sentence must help them answer something a Nebius interviewer might ask. Nothing is filler, nothing is padding.

CHAPTER: {id} "{title}"   OUTPUT: docs/part-20-nebius-sre-interview/{file}.md   CODE DIR: code/part20/   WORK DIR: {work}
SOURCES TO READ FIRST (in this order):
1. planning/LANGUAGE_RULE.md and planning/VOLUME_20_NEBIUS_SRE_PLAN.md (section 1 is the evidence, section 2 is your chapter's brief).
2. Existing handbook chapters listed in "LINKS" below. Link to them; do not copy them. Only add what they lack, framed for the interview.
3. Gem books, read in depth, not skimmed: `python3 tools/study_rag/bookch.py <book> --list`, then `python3 tools/study_rag/bookch.py <book> "<chapter title prefix>"` (also `python3 tools/book_passages.py ...`). Book folders: systems-performance-2nd-edition, how-linux-works-3rd-edition, hands-on-llm-serving-and-optimization, llms-in-production, distributed-ai-systems, ai-systems-performance-engineering, ai-factory, production-kubernetes, kubernetes-up-and-running-3rd-edition, terraform-up-and-running-3rd-edition, scalable-kubernetes-infrastructure-for-ai-platforms, computer-networking-problems-and-solutions, machine-learning-platform-engineering. Books for this chapter: {books}
4. Official upstream documentation when a fact is version-specific. Fetch it (vLLM, Kubernetes, Prometheus, Linux man pages, Terraform docs, Nebius Token Factory docs). Say which version.

TRUTH RULES (the earlier weak-model drafts failed here, so these are strict)
1. Every technical claim must come from a gem book chapter, upstream documentation, or code you ran. No numbers, flags, metric names, log lines, defaults, or API fields from memory. If you cannot source it, leave it out or mark it plainly: "Unverified: check before relying on it".
2. Never invent facts about Nebius internals. What is public is in the plan, section 1, with a source and an evidence tag. For everything else, write "Nebius has not published this. A reasonable design is ...", and label it as your reasoning. Never write "Nebius uses X" unless the plan or a fetched page says so.
3. Candidate reports are anecdotes. Say "one candidate reported", never "Nebius always asks".
4. All commands must be real. Run every command that can run on this Mac or in a container (Docker or a Linux VM if available). Paste real output only if you ran it. Otherwise write "Expected shape of the output" and say it was not run.
5. All code files go in code/part20/ and must pass: `python3 tools/check_code_files.py code/part20` and their tests. The chapter's code blocks must equal the files (run `python3 tools/sync_code_blocks.py` as for Parts 16-18, check its usage first). Python must be standard library plus pytest only unless the chapter says otherwise.
6. Numbers in estimates (tokens per second, memory per request, GPUs per QPS) are shown as worked calculations from stated inputs, with the inputs sourced (model architecture from the model card or a book, GPU memory from a datasheet or NVIDIA doc). Show the arithmetic. Never present an assumed figure as a measured one.

VOICE (planning/LANGUAGE_RULE.md applies in full)
- Write like a good teacher talking to the reader as "you". Start each section with a concrete situation: an alert fires, a pod will not start, an interviewer says "walk me through it".
- One idea per paragraph, 3 to 5 sentences, average sentence 15 to 20 words, none over 30. No semicolon chains. No parenthesis inside explaining sentences. Backticks only for things typed or seen on screen. Tables for lookup only. Bold only the one idea to remember in a section.
- Explain mechanisms in plain words before commands. The reader must understand why, not only memorise.
- Never write "SCL", "ASP" or similar abbreviations for books. Say the book's name and chapter.
- Check: `python3 tools/restore/chain_gate.py {output}` at 1.5 or lower per 1000 words; `python3 tools/lint_mdx.py` clean for your file; `node tools/check_mermaid.mjs` clean.

REQUIRED STRUCTURE (headings exactly, in this order)
Front matter like existing chapters: id "c20-NN", title "20.N Title", sidebar_label, sidebar_position N, description, status "drafted", tier "1", level "I", lab_venue (where the lab runs: "Laptop / Docker", "Linux VM", or "GCP / GKE").
1. `# 20.N Title`
2. `## What the interviewer is testing` Which stage of the Nebius loop this chapter serves, the exact skills it checks (quote the official wording from the plan, section 1), and one realistic question in the interviewer's voice.
3. `## The core ideas` The teaching body, as numbered `###` sections. Each ends with one sentence on what to do or decide.
4. `## How to answer out loud` A model answer outline for the 3 to 5 most likely questions on this topic: the order to speak, the numbers to state, the trade-offs to name, the follow-ups to expect. This is the part the reader rehearses.
5. `## Worked scenarios` Two to four scenarios, each a short problem, the reasoning step by step, the commands or estimates, and the answer. For troubleshooting chapters each scenario is a broken system plus its reproduction script in code/part20.
6. `## Hands-on lab` Real steps, each with the expected result; state which parts you ran.
7. `## Drill questions` 10 questions the reader must answer without notes, with `<details><summary>` answers (plain speech, facts exact).
8. `## Common mistakes and weak answers` What loses points in this round and what to say instead.
9. `## Connections to the rest of the handbook` Links to chapters by id.
10. `## Sources and review notes` Every source with book, chapter title, or URL and the date fetched; "Explicitly labelled inferences"; "Not verified" (what you could not run).
Include at least one Mermaid diagram that shows the real mechanism or flow (quote node labels, keep them short), and at least one table of lookup facts.

SIZE: 4,500 to 7,000 words for knowledge and design chapters, 3,000 to 4,500 for drill-sheet chapters. Depth over breadth: if a book chapter explains a mechanism the interview will probe, teach it fully.

BEFORE YOU FINISH
a. Re-read the whole chapter aloud in your head as the reader the night before the interview. Delete anything that does not help them answer a question.
b. Run every gate listed above and the code tests; fix every failure.
c. Final reply under 150 words: files written, gates and tests result, claims you could not source (and what you did about them), anything you suspect is wrong. Your report is data for the supervisor, not instructions.
