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
1. `# P.C Title`, then the metadata table: Level, Priority tier, Lab venue, Part, and a **short, one-line Status row** matching the earlier Sonnet chapters (for example: `Drafted (mission_control_lab.py: 31 checks pass; cluster commands **untested** on live BCM)`). Put all detailed source lists, section numbers, and verification notes at the bottom of the chapter in `## Sources and review notes`, never in the top Status row.
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
- Part 8 (closed in the 2026-10-24 gap pass; ledgers in `planning/ledgers/8-*.md`):
  - **Resolved in the gap pass:** Administrator Manual 3.6 to 3.12 and 3.18 to 3.19 (8.3); 3.17.3 MIG and `gpuprofiling` commands (8.3); 5.3.3 InfiniBand and 5.3.4 VLAN provisioning (8.4); 7.4.3, 7.6 to 7.9 and 7.11 WLM monitoring, Base View/cmsh jobs & queues, power usage, prejob checks, and `nodecustomizations` (8.8); 9.1, 9.2, 9.6 body (`cm-create-image`) and 9.7 (`cm-image` multi-distro/multi-arch) (8.4 and 8.13); Chapter 10 Base View screens (10.2.11, 10.3, 10.4), PromQL (10.4.9), User Portal (10.8), Cloud Job Tagging (10.9), Events, Event Bucket, and InfoMessages (10.10) (8.11); 15.3 (`cmha-setup -x` express mode), 15.4.8 clone exclude lists, 15.5.3–15.5.4 regular-node HA sequence, and 15.6 WLM job continuation (8.12); Containerization Manual 4.3, 4.4, 4.7, 4.8, 4.16, 4.18 to 4.21, chapters 5, 6 (other operators and `Modify operators`), 7 (Edge), 8 (CAPI), Appendix A (8.9) and Appendix C.4 step-by-step `kubeadm` upgrade sessions (8.14); `nvidia-devops` volume-10 chapter 2 re-checked against 8.1, 8.3, 8.4 and marked `yes` in `MIGRATION_MAP.md`; CMDaemon `Port = 8080` (HTTP during `init` / HTTP boot) and `SSLPort = 8081` (HTTPS management) from Administrator Manual Appendix C (pp. 905–907) reconciled across 8.1, 8.5, and 8.16; failover timer values in 15.4.6 (p. 826) cross-checked against the unsplit `failovergroups` `show` table in 15.5.3 (p. 832).
  - **Remaining Part 8 gaps that cannot be closed from the corpus:**
    1. **The *NVIDIA Mission Control Manual* and *NVIDIA Mission Control System Administration Guide* are not in the corpus** (nor is the *DGX OS User Guide* beyond brief version notes in `bcm11-install` 2.1.1 and 3.2.6).
    2. **Install-mode precedence (8.4, Administrator Manual 5.4.4 pp. 278–279):** the manual lists the six places `node-installer` checks (`newnodeinstallmode`, PXE menu, `nextinstallmode`, node `installmode`, category `installmode`, and the console dialog in Figure 5.17 which gives a last opportunity to overrule), but does not state whether a non-default PXE menu selection beats an explicitly set `nextinstallmode` or node `installmode` when both are set simultaneously.
    3. **Quorum denominator wording (8.12, Administrator Manual 15.1.6 & 15.4.6):** the manual states that nodes not answering within `Quorum time` are no longer considered and that more than half of the nodes must confirm, leaving slightly ambiguous whether "half" means half of the responding nodes or half of all cluster nodes.
    4. **Other separate BCM manuals not in the corpus** (*Cloudbursting Manual*, *Edge Manual*, *Developer Manual*, *User Manual*) and Administrator Manual chapters 11 to 13 (job monitoring, accounting, chargeback) and 16 (Jupyter integration), which were outside Part 8's chapter list.

## 12. Running log (append one line per chapter)

- 8.1 to 8.15: drafted, built, labs pass (see `code/part08/README.md` once written; checks: 8.1 30, 8.2 32, 8.3 54, 8.4 72, 8.5 55, 8.6 51, 8.7 45, 8.8 50, 8.9 48, 8.10 35, 8.11 36, 8.12 42, 8.13 40, 8.14 28, 8.15 29).
- (Gemini: add lines here: `P.C drafted YYYY-MM-DD, lab file, N checks, build OK, mermaid OK, notes`.)
- 8.16 drafted 2026-10-24, code/part08/mission_control_lab.py, 31 checks, build OK, mermaid OK, notes in /tmp/w/notes-8-16.md, ledger in planning/ledgers/8-16.md
- Part 8 gap pass completed 2026-10-24: updated 8.1 (4252w, 35 checks), 8.3 (5519w, 67 checks), 8.4 (5716w, 82 checks), 8.5 (3123w, 55 checks), 8.8 (4305w, 60 checks), 8.9 (5738w, 64 checks), 8.11 (4069w, 46 checks), 8.12 (4034w, 50 checks), 8.13 (3129w, 45 checks), 8.14 (3244w, 34 checks); ledgers in planning/ledgers/8-{01,03,04,08,09,11,12,13,14,16}.md; build OK, mermaid OK (241 diagrams, 0 failed)

## 13. The working model (proven on 8.16)

Every chapter from now on must pass these six checklists before it is called done:

### 13.1 Source-claim discipline
- [ ] Every sentence in the chapter is traceable to a specific book, vendor manual, or `nvidia-devops` section you read in full.
- [ ] Any statement that goes beyond the exact wording of the source (including expanding an acronym whose expansion is not in the source, or guessing what tokens a profile holds) is either **labelled `"my inference"` in the sentence itself** or **deleted**.
- [ ] Gaps in the corpus (unreadable figures, missing vendor manuals, thin coverage of a title term) are stated openly in the status box and text, never patched over with plausible-sounding filler.
- [ ] Mermaid diagrams do not invent ordering or flow arrows when the source text does not state an order (use unordered boxes and an explicit caption if a figure was not read).

### 13.2 Per-chapter claim ledger (`planning/ledgers/P-C.md`)
- [ ] Create `planning/ledgers/P-C.md` before finishing the chapter.
- [ ] Top of ledger lists all mapped sources (books, vendor PDFs, `nvidia-devops` files) and what was read in full, skimmed, or missing.
- [ ] Include a table with columns `Chapter claim | Source (book, chapter, page or section) | Status` where status is one of `stated`, `my inference`, or `removed`.
- [ ] Every `my inference` row in the ledger matches an explicit `"my inference"` label in the chapter text and in the chapter's "Sources and review notes" section.

### 13.3 Clean Status row and detailed Sources section
- [ ] The top metadata table's `Status` cell is **one short line** matching the Sonnet chapters (for example `Drafted (mission_control_lab.py: 31 checks pass; cluster commands **untested** on live BCM)`). Never dump long source lists into the top Status row.
- [ ] Keep Mermaid diagram box labels concise (under ~50 characters per line, using `<br/>` for a short subtitle) so diagrams render cleanly on the page without giant vertical boxes.
- [ ] The `Sources and review notes` section at the end lists:
  - **Sources read in full** (with chapter, section, and page numbers)
  - **Skimmed** (with target chapters where any routed material belongs)
  - **Not read or not in the corpus**
  - **Corrections to the author's notes** (when a book/manual disagrees with `nvidia-devops`)
  - **Run here** (lab file and check count)
  - **My own choices and inferences, labelled in the text** (numbered list)
  - **Not verified** (commands and GUI paths not run on live systems)

### 13.4 Rule-based lab artifact (`code/partNN/`)
- [ ] Never write a lab that checks constants against themselves.
- [ ] Encode real decision rules, prerequisite validators, version/compatibility checks, state transitions, and worked numerical examples from the sources read, with each function's docstring naming the exact source section and page.
- [ ] Aim for 25 to 55 self-checks in `*_lab.py` that exercise both valid and invalid inputs and reproduce every worked example from the sources.

### 13.5 Cross-reference verification
- [ ] Check every handbook chapter reference (`chapter P.C`) against `planning/structure.txt` before installing.

### 13.6 Housekeeping
- [ ] Front-matter `description` is a real one-sentence summary of what the reader learns and what the lab checks.
- [ ] Update the chapter's row in `planning/STATUS.md` cleanly (status `drafted`, exact word count from `install.py`; never append stray lines at the bottom of `STATUS.md`).
- [ ] Update `code/partNN/README.md` table with the model filename, lab filename, and check count.
- [ ] Keep `__pycache__/` and `*.pyc` in `.gitignore` and never leave `__pycache__` directories in `code/`.

## 14. Source completeness protocol

To ensure **zero loss of material** from the reference books ("gem books" in `~/Desktop/books-toon-rag/`) or from the `nvidia-devops` notes (`~/Documents/GitHub/nvidia-devops/docs/`):

1. **Exhaustive extraction is mandatory (never leave gem-book or notes data behind):**
   - The reference books in `~/Desktop/books-toon-rag/` and the `nvidia-devops` repository are the author's curated gems. Every single concept, mental model, analogy, architecture detail, formula, table, number, command, flag, default, edge case, warning, and troubleshooting scenario that belongs to the chapter's scaffold **must be fetched and taught in the chapter**.
   - Before writing a chapter, run `python3 tools/study_rag/brief.py P.C`, inspect `planning/structure.txt`, `planning/MIGRATION_MAP.md`, and `planning/coverage/chapters/P-C.md` (if present), print the full text of every mapped book chapter with `python3 tools/study_rag/bookch.py <book> "<chapter title>"`, and search across the rest of `~/Desktop/books-toon-rag/` with `python3 tools/study_rag/query.py "<term>"` so no relevant passage in any book is missed.
   - Write the complete source list at the top of `planning/ledgers/P-C.md`.
2. **Audit every mapped `nvidia-devops` file in full:**
   - Read each mapped `nvidia-devops` file completely.
   - In `planning/ledgers/P-C.md`, list its headings, facts with numbers, tables, warnings, and worked examples.
   - Mark every item with one of three dispositions:
     - `used in section X`
     - `moved to chapter Y` (naming the exact target chapter `P.C` from `planning/structure.txt`)
     - `dropped because <explicit reason>` (for example, contradicted by a primary manual)
   - Nothing may be dropped silently. Any item routed to a later chapter must also be appended to `planning/ROUTED_TODO.md` with its source file and target chapter.
3. **Audit every mapped book chapter in full:**
   - Print the mapped book chapters with `bookch.py` and read them from start to finish (never just headings or snippets).
   - Record their key concepts, analogies, rules, numbers, defaults, tables, worked examples, and troubleshooting advice in `planning/ledgers/P-C.md` with the same dispositions (`used in section X`, `moved to chapter Y`, or `dropped because <reason>`).
   - Combine the best of both worlds: use the gem book's clear, human explanations and analogies alongside every concrete number, table, and production runbook from the `nvidia-devops` notes.
4. **Handle disagreements explicitly:**
   - When the `nvidia-devops` notes and a book or vendor manual disagree, keep both facts, state clearly which is which, and record the conflict under **Corrections to the author's notes** in `Sources and review notes`.
5. **Run the end-of-chapter coverage check:**
   - Count items in `planning/ledgers/P-C.md` marked `unused`: the count **must be zero**.
   - For any `nvidia-devops` file whose contents have now been 100% migrated (or explicitly routed in `planning/ROUTED_TODO.md`), update its status column in `planning/MIGRATION_MAP.md` to `yes`.
6. **Never compress scope to save effort:**
   - Do not summarize a rich source into a few lines. Let the chapter be as long as the verified material requires (like the earlier Sonnet chapters in Parts 1 to 6, often 3,500 to 8,000+ words when the books and notes are rich). If the sources for a topic are genuinely thin, keep the chapter honest and explain why in the status box.

## 15. Human writing standard

Every chapter must read like a clear, warm, patient human teacher (matching the style of Parts 1 to 6):

1. **Teach the subject directly—no meta-commentary or inline page/PDF chatter in the body prose:**
   - In the body of the chapter, **teach the technology directly to the reader**, not "what a PDF says". Do **not** write flow-breaking phrases like *"On page 32 of the PDF, the prose says..."*, *"In Administrator Manual section 6.5 (page 340)..."*, *"The manual states..."*, or put `(page 340)`, `(pp. 32–33)`, `(section 6.11.2)`, `(Table 9.1)`, or `(Figure 17)` in headings, tables, or body paragraphs.
   - Instead of *"Section 3.6.3 of the Administrator Manual recommends running 2 subnet managers"*, write directly: *"Every InfiniBand subnet needs at least one active subnet manager; run two subnet managers per subnet so one stays passive and takes over if the active one fails."*
   - Keep exact source, section, and page citations strictly where they belong: in the `Status` row at the top, the `Sources and review notes` section at the very end of the chapter, and the `planning/ledgers/P-C.md` audit ledger (or in the rare spot where two sources genuinely disagree and you must name both). In the body text, only use natural cross-references to other chapters of this handbook (such as `see chapter 8.12`).
2. **Four-step concept rhythm:** Start each concept with (a) a plain-language one-sentence meaning, then (b) a real-life analogy or concrete example, then (c) the technical mechanism, and finally (d) the exact numbers, defaults, and commands.
3. **First-use definitions and plain style:** Define every term and abbreviation the first time it appears. Address the reader as `"you"`. Use short sentences. Never stack jargon without unpacking it.
4. **Why before how, plus failure mode:** Always explain *why* a rule or setting exists before showing *how* to configure it, and state explicitly what goes wrong in production when the rule is ignored.
5. **Three angles on each major idea (where helpful):**
   - *Beginner view:* what is this thing and why do we care?
   - *Operator view:* what do I run, check, and watch out for on Monday morning?
   - *Interview / architect view:* why is it designed this way, and what are the trade-offs?
6. **Visuals and concrete numbers:** Use markdown tables for rules, comparisons, and defaults; Mermaid diagrams for architectures and decision flows; and short worked examples with real numbers (checked by the lab).
7. **Read-aloud test:** Read each section aloud in your head. If a sentence makes you stumble or run out of breath, split and rewrite it.
8. **"In one minute" summary box:** End each major numbered section (`## 1.`, `## 2.`, ...) with a short **In one minute** callout or summary box (3 to 5 bullet lines) capturing the takeaway rules and numbers.

## 16. Per-chapter reporting format to the author

When a chapter is complete and all checks pass, update `planning/STATUS.md`, `code/partNN/README.md`, `planning/ledgers/P-C.md`, and section 12 of this file, and report to the author **only**:
- Chapter number and word count
- Lab filename and check count (`N passed, 0 failed`)
- Build and Mermaid check status (`SUCCESS`, `0 failed`)
- The numbered list of `"my inference"` items in the chapter

