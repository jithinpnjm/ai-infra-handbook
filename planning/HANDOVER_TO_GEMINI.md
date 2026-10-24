# Handover procedure: finishing the AI Infrastructure Handbook (for Gemini, then reviewed by Claude)

Written 2026-10-24 by Claude at the end of its session. Read this whole file first. It replaces nothing in `planning/HANDOFF_PROMPT.md`; it adds the **exact working procedure** that produced Parts 1 to 8 and the rules the author insisted on.

## 0. Where things stand

- Repo: `~/Documents/GitHub/ai-infra-handbook` (Docusaurus). Docs under `docs/part-NN-*/`. Chapter files are scaffolds until written; a written chapter has front matter `status: "drafted"`.
- **Done (drafted):** Parts 1 to 7 complete; Part 8 chapters **8.1 to 8.15** complete. **Next chapter to write: 8.16** (Mission Control, DGX Cloud and autonomous recovery concepts). Then Parts 9 to 19 (see `planning/structure.txt` for the exact chapter list and `planning/STATUS.md`). Part 0 has three orientation scaffolds, do those last.
- Committed to git on 2026-10-24 (branch master). The author has allowed commits (2026-10-24): commit after each finished chapter with a clear message.
- Progress notes are also in Claude's memory file (not available to you); this document is the source of truth. After each chapter update `planning/STATUS.md` (and add one line per chapter to a running log at the bottom of this file, section 12).

## 1. The author's standing rules (never break these)

1. **Continue chapter by chapter without waiting for confirmation**, through the last chapter, with stability and coverage checks.
2. **Never lower quality or depth** to save effort. Do not shorten or summarise scope.
3. **Simple, human, beginner-first language**, like the "gem books". Read the mapped book chapters **in depth** and use their explanations; do not leave gem-book information unattended. Short sentences. Explain a term the first time it appears. If a sentence is hard to read aloud, rewrite it.
4. **Write in your own words and credit sources.** No copying of passages. At most one short quote per source, under 15 words, in quotation marks, if ever.
5. **Be honest about what was run, read and unverified.** Every chapter has a status box and a sources section that say: what was read (and what was skimmed or not read), what was run (labs and their check counts), what is my own inference, what is not verified. Never claim a command works on real hardware you did not have. Mark labs "untested" unless you ran them.
6. **Flag corrections to the author's notes** (`nvidia-devops` repo) in the chapter's sources section when a book contradicts them. Do not silently follow either.
7. **Use mermaid diagrams** (at least one per chapter where a flow or architecture exists).
8. Keep chat replies to the author short and minimal ("concise by default"). Put depth in the chapter files.
9. A "books used effectively" **revisit pass** is planned later; keep a list of anything you skimmed (section 11).

## 2. Tools and paths

- Book corpus: `~/Desktop/books-toon-rag/<book>/<book>_chunks.jsonl` (JSON lines with `chapter_title`, `content`). List of books: `ls ~/Desktop/books-toon-rag`. Key ones for the remaining work: `bcm11-*`, `superpod-*`, `ai-systems-performance-engineering` (the author's top source), `kubernetes-*`, `production-kubernetes`, `ai-data-center-network-design-and-technologies`, `ai-networking-cookbook`, `networking-and-kubernetes`, `hands-on-llm-serving-and-optimization`, `llmops`, `llms-in-production`, `machine-learning-platform-engineering`, `practical-mlops`, `designing-machine-learning-systems`, `distributed-ai-systems`, `generative-ai-on-kubernetes`, `ai-engineering`, `ai-factory`, `systems-performance-2nd-edition`, `parallel-and-high-performance-computing`, `how-linux-works-3rd-edition`, `terraform-up-and-running-3rd-edition`, `ansible-up-and-running-3rd-edition`, and the author's notes `nvidia-devops-*` (also at `~/Documents/GitHub/nvidia-devops/docs/`).
- Print a chapter of a book: `python3 tools/study_rag/bookch.py <book> "<chapter title prefix>" > /tmp/x.txt`; list titles: `python3 tools/study_rag/bookch.py <book> --list`.
- Per-chapter research brief: `python3 tools/study_rag/brief.py <part>.<chapter>` (mapped notes files, source headings, optional `--q "terms"` search). Chapter text of a mapped source: `tools/study_rag/chapter_text.py`. Search across books: `tools/study_rag/query.py`.
- Mapping tables: `planning/MIGRATION_MAP.md` (which `nvidia-devops` files belong to which chapter), `planning/structure.txt` (chapter titles, level, sources), `planning/coverage/chapters/NN-MM.md` (source headings per chapter).
- Scratch files: use `/tmp/w/` (create it). Chapter drafts go to `/tmp/w/pNM.md` and are installed with the scaffold tool.
- Python: use the system `python3` (stdlib only for labs). Optional packages that exist in earlier labs are noted in the part README.

## 3. The per-chapter procedure (do all steps, in order)

1. **Orient.** `python3 tools/study_rag/brief.py P.C` (P part, C chapter). Read the chapter's entry in `planning/structure.txt`. Open the scaffold file `docs/part-PP-*/CC-*.md` to see its title and front matter.
2. **Read the sources in depth.** Print each mapped book chapter with `bookch.py` and read it (not just headings). Read the mapped `nvidia-devops` files. Search other books for the main terms (`brief.py --q`). Write down for yourself: facts with numbers, rules, defaults, commands, tables, warnings, and any contradiction between sources. **Do not rely on memory of the product.** If a fact is not in a source you read, it is either marked "my inference/unverified" or left out.
3. **Design the lab artifact** (section 5): a small stdlib Python module that models the chapter's rules, plus a self-checking lab that prints `PASS`/`FAIL` lines and a final count. Put them in `code/partNN/`.
4. **Run the lab** until it passes. A failing check usually means you misread a rule: re-read the source before "fixing" the test. If a check turns out to test your own guess, label it as such in the chapter.
5. **Write the chapter** to `/tmp/w/pNM.md` using the template in section 4. Simple language. Diagrams. Tables. Exercises. 20 checkpoint questions. Honest sources section.
6. **Install and check:**
```bash
cd ~/Documents/GitHub/ai-infra-handbook
python3 tools/scaffold/install.py P.C /tmp/w/pPC.md     # replaces the scaffold body, keeps level/tier/lab_venue from the scaffold
python3 tools/fix_table_pipes.py docs/part-PP-*/CC-*.md  # fixes unescaped | inside table cells
python3 tools/lint_mdx.py                                # MDX safety (curly braces, angle brackets, etc.)
python3 tools/scaffold/generate.py                       # regenerates sidebars/index from front matter
npm run build 2>&1 | grep -E "SUCCESS|ERROR|rror"        # must say SUCCESS
node tools/check_mermaid.mjs | tail -3                   # must say "0 failed"
```
7. **Fix what the checks report** and re-run. Re-run the lab. Then re-read your chapter for claims that go beyond your sources (section 7).
8. **Update records:** `planning/STATUS.md`; the part's `code/partNN/README.md` (list files, check counts, how to run); the log in section 12 below. Update `planning/MIGRATION_MAP.md` status column for any `nvidia-devops` file you fully migrated (put `yes`).
9. Move on to the next chapter immediately. Do not ask the author for confirmation between chapters.

## 4. Chapter template (match Parts 1 to 8)

Front matter (copy the scaffold's, keep `id`, set `status: "drafted"`):
```yaml
---
id: "c08-15"
title: "8.15 Title"
sidebar_label: "8.15 Title"
sidebar_position: 15
description: "One sentence, what the reader learns"
status: "drafted"
tier: "1b"
level: "B"
lab_venue: "Nebius GPU"
---
```
(`install.py` copies `level`, `tier`, `lab_venue` from the scaffold, so you can leave those as in the scaffold.)

Body sections, in this order:
1. `# P.C Title`, then the metadata table: Level, Priority tier, Lab venue, Part, and a **Status** row that says honestly: what sources were read, that no real system was available (if true), what the lab/model is and how many checks it runs, that it tests the author's reading of the sources and not the product.
2. `## Why this matters for AI infrastructure` (one short paragraph, concrete).
3. `## Prerequisites and outcomes` (what to know first; 5 to 8 "you can ..." bullets).
4. Numbered concept sections `## 1. ...`: simple wording, short paragraphs, tables for rules and defaults, a mermaid diagram for each main flow or architecture, code in fenced blocks. Mark untested commands: "(from the manual, untested here)".
5. `## Common first mistakes` (8 to 10 items).
6. `## Exercises` (6 items, some using the lab code).
7. `## Interview angles` (5 questions with one-line strong answers).
8. `## Checkpoint questions (20)` (numbered, answerable from the chapter).
9. `## Sources and review notes` with these bullets: sources read (with chapter/section numbers and what was **not** read); corrections to the author's notes; "Run here" (lab name and number of checks); "My own choices, not the sources'" (derivations, thresholds, judgment calls); "Not read or not covered"; "Not verified".

Length: Parts 6 to 8 chapters are 2,500 to 4,500 words. Do not go much shorter than 2,500 unless the topic is genuinely small and the author's notes are fully covered.

## 5. The lab artifact pattern

- Location: `code/partNN/` (create the folder and a `README.md` listing files if it does not exist). Part 7 and 8 are examples.
- Two files per chapter: `xyz.py` (the model: small functions or classes that implement **rules the sources state**, each with a docstring that names the section it follows) and `xyz_lab.py` (the self-checking lab: a `check(name, cond, detail="")` helper, many checks, final line `N passed, M failed`, exit code 1 on failure).
- The model must be **stdlib only**, deterministic and fast. It models the *rules* (defaults, limits, state machines, formulas, validators), not the product. Where the source is silent or ambiguous, the code raises an error or returns a clearly labelled assumption; never guess silently.
- Test names are sentences that state the rule (for example "a closed node keeps running jobs"). Reproduce the source's own worked examples as checks wherever they exist (these are the most valuable tests).
- Good artifact types: validators/linters for configs, parsers for tool output, simulators of state machines, calculators that reproduce a source table, decision functions that encode a flow chart, small mock services (Part 7 has a Redfish mock). Where real software is installable on a laptop (Slurm client tools, jq, Python libs) a real run is better than a model; say which.
- Aim for 25 to 55 checks per chapter.
- If a chapter is about hardware or a product you cannot run (GPUs, InfiniBand, NVIDIA SDKs), the model is still the right deliverable; say so in the status box.

## 6. Gotchas that cost time (all hit during Parts 7 and 8)

- **zsh:** a command containing `echo =====X` fails (`=` expansion). Use plain words.
- **macOS `sed -i`** needs `sed -i ''`. Prefer a small Python replace.
- **Shell `&&` chains:** if the first command fails, later `cd` never happens and you run tools in the wrong directory. Run `cd ~/Documents/GitHub/ai-infra-handbook` first, then each tool.
- **Mermaid:** quote labels that contain parentheses or special characters, for example `subgraph H["head node(s)"]`; avoid semicolons in labels (`tools/fix_mermaid_semicolons.py` exists). Check with `node tools/check_mermaid.mjs`.
- **Markdown tables:** a `|` inside a cell breaks the table; `fix_table_pipes.py` escapes it. Re-run after every install.
- **MDX:** raw `<tag>`, `{braces}` and `<https://...>` outside code fences break the build. Put such text in backticks. `lint_mdx.py` reports them.
- **Section numbers of tools:** book text is OCR/extracted and tables can be garbled (the BCM failover parameter table was). When a table is unreadable, say so and mark your reading as such.
- **Book text duplicates** chunks at boundaries; ignore repeated paragraphs.
- Ports, flags and version numbers differ between books and the author's notes: always say which source you follow (BCM example: the manual says management goes through 8081; the notes mention 8080).

## 7. Quality gate before you call a chapter done

Answer yes to each, or fix it:
1. Is every number, default, command and rule traceable to a source I read? Anything else is labelled "my inference" or removed.
2. Did I read the source chapter(s) in depth, not only headings? Did I list what I skimmed?
3. Does every worked example in the sources appear as a lab check?
4. Is the language simple enough for a beginner? No long chains of jargon without definitions?
5. Does the status box say what was and was not run? Are labs marked untested where applicable?
6. Do diagrams exist and render (`check_mermaid` says 0 failed)? Does the build say SUCCESS?
7. Are there 20 checkpoint questions and 6 exercises, and do the questions match the text?
8. Are cross-references (to other chapters of this handbook) correct? (Chapter numbers are in `planning/structure.txt`.)
9. Did I record corrections to the author's notes, if any?
10. Did I avoid copying passages?

## 8. What remains and where the sources are

Check `planning/structure.txt` for titles. Suggested source anchors (verify with `brief.py` and `MIGRATION_MAP.md`):

- **8.16 Mission Control, DGX Cloud and autonomous recovery:** the GB300 SuperPOD reference architecture (software stack, Mission Control five layers, autonomous recovery, in-memory checkpointing claims), BCM Admin Manual mentions (autonomous hardware/job recovery profiles in 6.5; Base View pages; Run:ai chapter 6.11 of the Containerization Manual; `cm-runai-setup`), notes `nvidia-zero-to-hero/volume-21` (mapped, AI factory design). The BCM manuals do not contain the Mission Control manual: say so, and keep the chapter to what the sources state.
- **Part 9 NVIDIA systems** (14 chapters): DGX/HGX/GB-series, NVLink/NVSwitch, DPUs, systems hardware. Sources: `superpod-*`, `ai-systems-performance-engineering`, `nvidia-zero-to-hero/volume-*` notes per `MIGRATION_MAP.md`.
- **Part 10 GPU/CUDA** (22), **11 GPU Kubernetes** (30), **12 AI networking** (24), **13 AI storage** (9; remember the volume-15 GPUDirect Storage notes routed earlier), **14 training/fine-tuning** (16), **15 inference** (18), **16 MLOps/LLMOps** (15), **17 operations** (16), **18 security** (7), **19 capstones/interview** (15), **Part 0 orientation** (3).
- For each, run `brief.py` and follow section 3.

## 9. Style sample (what "simple and human" means here)

Instead of: "CMDaemon leverages a hierarchical inheritance paradigm for configuration resolution."
Write: "A node asks its own settings first. If it has none, it uses its category's. If the category has none, it uses the cluster default."

Instead of: "STONITH enforces fencing semantics."
Write: "Before the standby head node takes over, it must be sure the old one is really off, so it switches it off itself. People call this STONITH, short for 'shoot the other node in the head'."

## 10. How Claude will review your work (so you can self-check first)

The author will bring your chapters back to Claude. Claude will:
1. Run the build, mermaid check and every lab.
2. Re-read the cited source sections and check that claims, numbers and defaults match; flag anything unsupported.
3. Check the status box, "my inference" labels and "not read" lists for honesty.
4. Check language simplicity, structure against section 4, and the quality gate in section 7.
5. List fixes by chapter. So: keep your working notes (what you read, what you inferred) in `/tmp/w/notes-P-C.md` or at the end of the chapter's sources section, so the review is quick.

## 11. Revisit-pass list (do not lose)

- The planned "books used effectively" pass: re-read mapped book chapters against each Part and fix gaps.
- Part 7: `redfish-schema` book only skimmed; OpenAPI and Interop profile format covered lightly.
- Part 8: Administrator Manual 3.6 to 3.12 (InfiniBand, switches, Cumulus, NetQ, UFM) not read; 5.3.3 and 5.3.4 (InfiniBand and VLAN provisioning) not read; 9.1 and 9.2 beyond headers, 9.6 body, 9.7 not read; 15.3 (express HA setup) and 15.6 (job continuation) not read; MIG commands (3.17.3); Chapter 7 sections 7.6 to 7.9, 7.11; Chapter 10 Base View monitoring screens; Containerization Manual 4.3, 4.4, 4.7, 4.8, 4.16, 4.18 to 4.21, chapters 5, 7, 8, other operators in 6; the NVIDIA Mission Control Manual is not in the corpus; `nvidia-devops` volume-10 chapter 2 is mapped to 8.1, 8.3 and 8.4 and should be re-checked against those chapters; install-mode precedence (8.4) is unresolved from the manual text; BCM failover timer defaults (8.12) come from a garbled table.
- Chapter 8.1 and 8.5 state the CMDaemon port facts; keep consistent with the later note in 8.1 (manual: management through 8081 only; `cm-cmd-ports` exists with `--http` and `--https`; notes mention 8080).

## 12. Running log (append one line per chapter)

- 8.1 to 8.15: drafted, built, labs pass (see `code/part08/README.md` once written; checks: 8.1 30, 8.2 32, 8.3 54, 8.4 72, 8.5 55, 8.6 51, 8.7 45, 8.8 50, 8.9 48, 8.10 35, 8.11 36, 8.12 42, 8.13 40, 8.14 28, 8.15 29).
- (Gemini: add lines here: `P.C drafted YYYY-MM-DD, lab file, N checks, build OK, mermaid OK, notes`.)
