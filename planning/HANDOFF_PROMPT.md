# Bootstrap prompt (copy this whole block into any new chat or model)

> You are continuing a long-running writing project: the **AI Infrastructure Handbook** in `~/Documents/GitHub/ai-infra-handbook` (Docusaurus). Do not rely on memory of earlier chats. First read `planning/PROJECT_MAP.md`, then `planning/HANDOFF_PROMPT.md`, `planning/CURRICULUM_MAP.md` (all revisions), `planning/STATUS.md`, `planning/INTERVIEW_TOPICS.md` and `planning/JD_MAPPING.md`. Chapter structure and numbering come from `planning/structure.txt` / `planning/STRUCTURE.md` (generated scaffold under `docs/`). Continue with the next unfinished Tier 1 item in STATUS.md; replace the scaffold file's content in place and set its frontmatter `status: drafted`. Before writing any chapter, create its coverage file (planning/COVERAGE_PROCESS.md), search the corpus with `tools/study_rag/query.py` across several sources (the author's top source is *AI Systems Performance Engineering*; capture it fully), write original, deep, basics-to-advanced prose with large diagrams, labs and checkpoint questions, flag anything to verify, and update STATUS.md. Do not shorten, summarise or change scope. Keep chat replies short; put the depth in the chapter files. If anything conflicts or is unclear, ask the author.

---

# Handoff prompt: paste this into any LLM session (new chat, restart, or different model) to continue the book

---

You are continuing work on the **AI Infrastructure Handbook**, a private study book (publishable later) for a DevOps engineer who is strong in Linux and networking but wants to refresh from basics and reach senior level in **AI infrastructure / AI factory platform** roles (NVIDIA-style: Linux, HPC/Slurm, networking incl. InfiniBand/RoCE, Kubernetes, Ansible, Terraform, Python, GPU stack, distributed training, fine-tuning, inference/serving, MLOps/LLMOps).

## Your first steps, every session
1. Read `planning/CURRICULUM_MAP.md` (the contract: parts, chapters, sources, levels, lab venues, template, rules).
2. Read `planning/STATUS.md` (what is done, in review, next). Work only on the next unfinished chapter unless told otherwise.
3. Read one finished chapter from `docs/` as the style reference (once any exist) so tone and depth stay consistent.

## Author feedback that overrides defaults (2026-10)
- Depth must match the quality of the source books: teach in the same way they do (motivation, mechanism, worked example, pitfalls). Earlier pilot chapters were ~10% of the source material and were judged too thin. **Do not compress.** If a topic needs 15k words, split it into several chapters.
- Coverage is tracked: before writing any chapter create its coverage file per `planning/COVERAGE_PROCESS.md` using `planning/source-outlines/`.
- `planning/INTERVIEW_TOPICS.md` is mandatory scope. Slurm, multi-node GPU pods on Kubernetes, SR-IOV, virtualization and vGPU were asked in a real NVIDIA interview and must be covered to interview depth. Where the books are thin (marked T), use NVIDIA/Kubernetes/kernel official documentation and flag it in the chapter.
- Diagrams must be large and legible (the site has click-to-zoom). Prefer several focused diagrams over one dense one.

## Migration rule (author feedback, 2026-10): bring nvidia-devops in, so that repo can be archived
The author wants everything in `nvidia-devops` brought into this book. It is the author's own content, so reuse it directly (text, tables, Mermaid diagrams, labs, interview Q&A, troubleshooting runbooks), not just as a reference. For every chapter:
1. Run `python3 tools/migration/inventory.py` and read the nvidia-devops files listed against the chapter in `planning/MIGRATION_MAP.md` (search the corpus with `--book nvidia-devops` or read the files in `~/Documents/GitHub/nvidia-devops/docs`).
2. Merge them into the chapter: one consistent voice and the template, no duplicated content across chapters, raise depth, **check every claim** (the repo has already corrected itself in places, and may still hold errors; verify against the books, vendor PDFs and official docs, and flag what you cannot verify).
3. Add `Migrated from nvidia-devops: <file names>` (use `(partial: sections ...)` if only part was used) to the chapter's Sources and rerun the inventory. Non-document assets (images, data files, interactive pages) follow `planning/MIGRATION_ASSETS.md`.
4. Already-written chapters get a migration pass when new material is found (6.7 had one; 1.1 and 1.2 have no mapped files).

## Foundations rule (author feedback, 2026-10): do not skip the basics
The author is a DevOps engineer who lacks solid basics in Linux, networking and how Kubernetes really works (bare-metal setup, pod and Service life cycles, the underlying network, what the Linux kernel does at each step), is new to Ansible, and has used Terraform. Therefore Parts 1, 2, 4 and 5 are **Tier 0 (foundations)**, written first and from zero:
- Assume nothing: define terms, use a concrete analogy, then the mechanism, then a worked example the reader can run and observe (`strace`, `ip netns`, `iptables-save`, `crictl`, `tcpdump`).
- Every Kubernetes life-cycle chapter (pod, Service, DNS, storage, networking) has a "what the kernel does" table: system calls (clone, unshare, setns, mount, pivot_root), cgroup writes, namespace creation, veth and bridge or route setup, netfilter and conntrack rules, with the commands to see them.
- Capture the "gem" foundation books exhaustively (How Linux Works, Systems Performance, Computer Networking Problems and Solutions, Kubernetes Up and Running, Production Kubernetes, Networking and Kubernetes, Ansible Up and Running, Terraform Up and Running, Learning Python, Fluent Python). `python3 tools/coverage/map_sources.py` audits that every chapter of each is cited by some handbook chapter; `planning/coverage/MASTER_MAP.md` must stay empty of unmapped chapters, and deliberate skips live in `planning/coverage/skips.txt` with a reason.
- Writing order: Tier 0 first, then Tier 1, 1b, 2, 3 (chapter 6.7 was written early as the depth model).

## Non-negotiable quality bar (do not dilute)
- **Depth:** basics to advanced in the same chapter. The advanced section must reach what a senior engineer is asked in a design or incident interview: internals, trade-offs, failure modes, tuning knobs with realistic values, numbers where they matter. Never replace depth with a summary or a list of tool names.
- **Original writing only.** Use the source books for research, then write in your own words, with your own Mermaid diagrams and your own examples. No copied passages, no copied figures, no code beyond tiny API fragments. Credit sources in the chapter's last section as "Sources" (book, chapter number).
- **Cross-check:** every non-obvious technical claim is supported by at least two sources, or marked `single-source` and flagged for verification. Where the books are thin (Network Operator, Lustre, Grafana/Loki, executive framing), say so and point to NVIDIA's public documentation.
- **Runnable material:** commands, configs and labs must be correct. Say which lab venue (Mac / GCP / Nebius GPU) they run on, give the expected output, and note anything not yet executed as `untested`.
- **Template (every chapter):** why it matters for AI infra → prerequisites and outcomes → concepts basics→intermediate→advanced with a Mermaid mental-model diagram → commands/configs that matter → how it fails (4–6 failure modes: symptom, diagnosis, fix) → hands-on lab → 8–12 checkpoint questions with answers → sources.
- **Length:** roughly 6,000–10,000 words per chapter file; split topics instead of shortening them.
- **Do not widen scope.** Stick to the curriculum map. New ideas go in `planning/BACKLOG.md`, not into the current chapter.

## Tools available on the author's Mac
- Book corpus (26 O'Reilly books, 8 vendor PDFs (BCM, Redfish, SuperPOD), and the author's own nvidia-devops volumes; private, never commit): `~/Desktop/books-toon-rag/<book-slug>/` with `*.toon` (full text per chapter) and `*_chunks.jsonl`.
- Search index: `python3 tools/study_rag/query.py "terms" -n 8 [--book SUBSTR] [--full]`. Rebuild with `ingest.py` in tools/study_rag/. Run several queries per topic, across different books, before writing.
- Existing material to mine and rewrite (not paste): `~/Documents/GitHub/nvidia-devops/docs/nvidia-zero-to-hero/volume-NN/` (the "Reuse" column in the map says which).
- Book site: Docusaurus in this repo; chapters live in `docs/part-NN-<name>/NN-<slug>.md`.

Also read `planning/NVIDIA_DEVOPS_INVENTORY.md` (every nvidia-devops topic must be present) and `planning/CURRICULUM_MAP.md` Revision 3 (HPC/supercomputer track, BCM, Redfish, SuperPOD, complete Linux and networking). Internet research is approved for gap topics; always cite the public document and flag it for version verification.

## How to work a chapter
1. Pull the sources named in the curriculum map for that chapter, plus 3–6 extra searches for gaps.
2. Write a short outline first (headings and the key claims per heading) and note which source supports which claim.
3. Write the chapter in full following the template.
4. Self-review: re-read against the quality bar, fix shallow sections, check every command, check that no passage resembles a source too closely.
5. Update `planning/STATUS.md` (status, word count, open questions, `untested` items). Do not mark a chapter done if labs are untested; mark it `drafted`.

## When resuming after a break or switching models
- Do not summarise the project from memory. Re-read the files above, then continue from `STATUS.md`.
- If the previous chapter's depth looks lower than this bar, say so and expand it before moving on.
- If instructions conflict with this file, ask the author; do not silently change scope, depth or format.
- Keep answers short in chat. The depth belongs in the chapters, not in the conversation.

---
