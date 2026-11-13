# Prompt for Argon: write the rest of Part 10 (10.11 onward) with the review rules built in

Paste everything below the line into Gemini Argon. (Flash was dropped on 2026-10-25; Argon now drafts, self-checks with the validator, and Claude does the final validation.)

---

TASK: Continue Part 10 from the next unwritten chapter (10.11 onward; check planning/STATUS.md) through 10.22. Write chapters of Part 10 ("The GPU and CUDA") of the AI Infrastructure Handbook, one chapter at a time, in order. Follow planning/HANDOVER_TO_GEMINI.md exactly (procedure, template, standing rules). The rules below are ADDITIONS that fix the mistakes seen in the reviews of 10.6 to 10.9. A validator checks them, and Claude will validate your work afterwards, so every mistake you leave costs rework.

KNOWN MISTAKES FROM THE REVIEWS OF 10.6 TO 10.9 (made by both models). DO NOT REPEAT THEM
1. Changing a source number: the note said GPUs stall 90% of the time, you wrote "over 85%". Copy numbers EXACTLY.
2. Inventing a number: the note said "over 3,000 Watts", you wrote 3,300. Never "improve" a figure.
3. Adding background facts from memory: a licence section number, "80% of compute is inference", "NVIDIA audits...". If it is not in a source you read, leave it out.
4. Adding multipliers or percentages nobody gave you ("four times slower", "64% increase") unless the lab computes them or the source states them.
5. Exercises that cannot be solved (no data given). Every exercise must be solvable from numbers inside the exercise or the chapter.
6. Commands not marked "(untested here)" and missing "Not verified on live hardware" / "Run here" lists.

SOURCE RULES (apply to every chapter)
- Read every mapped source IN DEPTH (planning/MIGRATION_MAP.md, planning/structure.txt, tools/study_rag/brief.py). Write a scratch list of the exact numbers, tables and warnings as they appear.
- Every number in the chapter must come from that list, or from the chapter's own lab output, or be labelled "my estimate" and listed under "Explicitly labelled inferences". No third option.
- If two sources disagree, show both numbers and say which source each came from. Do not pick one silently.
- Prefer "see chapter 9.x" cross-references over repeating a fact already explained in an earlier chapter. Keep one short reminder of the key number so the chapter can still be read alone. Do not re-explain NVL72, PSU rules, PCIe/topology symbols or similar material already covered in Part 9 or earlier Part 10 chapters.
- At most one short quotation (under 15 words) per source. Paraphrase everything else. Never quote licence text, section numbers or clause numbers unless they are in a source.

CHAPTER SHAPE (same as 10.6 and Part 9)
- Status row in the table at the top, front matter status "drafted".
- Plain, beginner-first language, written like the gem books. LANGUAGE: follow planning/LANGUAGE_RULE.md in full (book-style prose, plain words, at most two numbers per sentence, code formatting only for things you type or see on screen). The validator prints readability warnings; reduce them.
  (Also:) short sentences, terms explained at first use, no exclamation marks, no hype ("massive", "catastrophic", "demolishes").
- Length: 6,000 to 9,000 words. If a topic needs more, say so in your report and propose splitting the chapter. Do not pad.
- One mermaid diagram per main flow or architecture (at least one per chapter).
- Exactly 20 checkpoint questions (details/summary blocks) and an Exercises section (5 to 6 tasks) placed before the questions.
- A small stdlib Python model + self-checking lab in code/part10/ (like the existing ones). Derived numbers (ratios, sums) must be computed in the lab, and the chapter may quote them only after the lab prints them.
- "Sources and review notes" must contain: sources read in full, sources only skimmed or not read, "Run here" (lab name and check count), "Explicitly labelled inferences", "Corrections to the author's notes", "Not in the corpus", "Not verified on live hardware".
- Ledger planning/ledgers/10-NN.md with: source inventory, a NUMBER TABLE (each number in the chapter -> source file and section, or "lab", or "my estimate"), and one-line expected answers for every exercise.

SOURCE BREADTH (checked by tools/check_coverage.py)
- Before writing, run: python3 tools/study_rag/brief.py P.C --q "<main term 1>" --q "<main term 2>" --q "<main term 3>"
  and python3 tools/check_coverage.py P.C. Read the top hits of every gem book that is not already mapped.
- Add a "## Corpus search" section to the ledger: the queries you ran, the books and chapters found, and for each
  either "used in section N" or "read, nothing new" or "not relevant because ...". "Not read" is not allowed
  for a book scoring 4 or more in the coverage report.
- Cite every gem book you actually used in "Sources and review notes" by its folder name (for example
  distributed-ai-systems). Every mapped nvidia-devops file must also be cited by file name.

SOURCE BREADTH AND HONESTY RULES ADDED AFTER THE 10.8 AND 10.9 REVIEWS
1. Per-heading corpus search. tools/check_coverage.py now runs one query for the title and one for each H2 heading and
   adds up the book scores. Every book listed as UNRECORDED must be opened. Then either cite it in "Sources and review
   notes" by its folder name, or add a line to the ledger "Corpus search" section: "<book>: read <section>, nothing new"
   or "<book>: not relevant because ...". The old rule (only books scoring 4+) missed bcm11-containerization in 10.9.
2. Product manuals. If the chapter explains a software component (driver, toolkit, Fabric Manager, DCGM, Slurm, Kubernetes
   operators, firmware, cmsh), search the BCM manuals for how BCM installs and owns it: bcm11-install, bcm11-admin,
   bcm11-containerization, bcm11-user. Add a short "How BCM installs/owns this" subsection with exact package names,
   defaults and wizard answers. This handbook is BCM-centred, so skipping it is a gap.
3. Incident and failure notes. For any chapter about operations, throttling, power, clocks, errors or health, read the
   matching Volume 19, Volume 20 and Volume 16 chapters even when MIGRATION_MAP.md maps them to a later chapter. If you
   defer one, say so by file name in the sources section ("expanded in 10.21").
4. Never write a reference table from memory (bit masks, error codes, register values, version matrices). If it is not
   in a source, mark it in the text "from memory / not in the corpus / verify with <command>" and list it under
   "Explicitly labelled inferences". Do not claim "matches the source notes" unless you compared them.
5. Illustrative outputs. If a source note says its outputs are illustrative, say so in the chapter and do not present its
   numbers as specifications. When two notes give different examples for the same thing (for example clock drop sizes),
   show them side by side in a small table and say they disagree.
6. Reading honesty. In "Sources and review notes" list, per source, what you read in full, what you read in part (name the
   section or line range), and what you did not read. Do not write "read in full" for a source you only searched.
7. Hex values, versions and prices count as numbers. The validator checks hex values and flags numbers that appear only in
   your own lab code. If a number is only in your lab, the lab must compute it from numbers that are in a source.
8. Every exercise must be solvable from numbers inside the exercise or chapter, and its one-line answer goes in the ledger.
9. Do not invent a measurement ("1 to 2 seconds", "4x slower", "85%"). Copy the source number exactly or say the source
10. DIAGRAMS MUST BE READABLE (added 2026-10-25 after a user complaint about an unreadable stack diagram)
    - Every Mermaid box has at most 2 short lines (about 25 characters per line) and under 130 characters in total.
      The site and the EPUB wrap long labels into tall narrow boxes, then shrink the whole picture until it cannot be read.
    - Put the detail (package names, numbers, commands, device numbers, file paths) in a table directly under the diagram.
      Nothing may be lost: if a fact was in a box, it goes in the table.
    - Keep a diagram to about 12 boxes. Prefer flowchart LR for left-to-right chains and TB for decisions. If a flow needs more,
      split it into two diagrams.
    - Edge labels: 3 to 5 words. Use the table for thresholds and commands.
    - tools/validate_chapter.py fails the chapter if any box is longer than 130 characters. Also look at the rendered
      diagram: python3 -c on the .mmd with tools/epub/node_modules/.bin/mmdc (puppeteer.json, mermaid.json) gives a PNG.
      If the picture is taller than about twice its width, simplify it.
   gives no figure.

SELF-CHECK LOOP (do this before you move to the next chapter, every time)
1. python3 tools/validate_chapter.py 10.N   (it prints number provenance AND source coverage: fix every UNRECORDED book and every 'only in lab code' fact)
2. For EVERY line under "NOT FOUND" or "DIFFERENT context": open the cited source, compare, and either correct the chapter, remove the claim, or label it "my estimate". Arithmetic derived in your lab is fine if the lab prints it.
3. Re-read every story, customer scenario and exercise against the source note it came from. Compare each figure side by side.
4. Solve each exercise yourself and put the answer in the ledger.
5. Run the repo checks from the handover (install, fix_table_pipes, lint_mdx, generate, build, check_mermaid) and the lab.
6. Update planning/STATUS.md and code/part10/README.md.
7. Append the validator's final output and a 3-line self-assessment to planning/ledgers/10-NN.md ("what I am least sure about").
Do not start the next chapter until the validator shows no FAIL and every NOT FOUND / DIFFERENT context line is explained in the ledger.

REPORT AFTER EACH CHAPTER (short)
Words, lab checks, validator result, the 3 claims you are least sure about, and any source conflict you found.

DO NOT: commit, touch Parts 1 to 9, reduce depth to save time, or ask for confirmation between chapters.
