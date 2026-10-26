> UPDATE 2026-10-25: Flash was dropped. Argon now drafts and self-checks (Steps 1 and 2 combine); Claude still does Step 3. Use `planning/ARGON_PART10_PROMPT.md`. The rules block below still applies in full.

# Three-step chapter workflow: Flash drafts, Argon improves, Claude validates

Why: Flash is fast and follows the chapter template well, but in the 10.7 test it drifted on numbers
(85% instead of 90%, an invented 3,300 W, an EULA section number, an unsourced "80%" claim, an
unsolvable exercise). Argon is slower but stayed closer to the sources (10.6). So: Flash writes,
Argon tightens against the sources, Claude runs the final validation. Nobody commits until the
author says so.

## Step 1: Flash drafts (paste this prompt, then the usual per-chapter procedure from HANDOVER_TO_GEMINI.md)

```text
You are drafting chapter P.C of the AI Infrastructure Handbook. Follow planning/HANDOVER_TO_GEMINI.md
section 3 exactly. In addition, these STRICT SOURCE RULES apply (a validator will check them):

1. Every number in the chapter must be copied EXACTLY from a source you read (nvidia-devops note, gem
   book, or the chapter's own lab output). Do not round, "improve", or restate a number differently
   (if the source says 90%, write 90%, not "over 85%").
2. If you need a number that is not in a source (a price, a percentage, a section number, a count),
   either leave it out or write it as an estimate and label it "my estimate" in the text and list it
   under "Explicitly labelled inferences". Never state it as fact.
3. Do not add background claims from memory (for example "NVIDIA audits...", "80% of compute is
   inference", clause or section numbers of licences). If it is not in a source, leave it out.
4. At most one short quote (under 15 words) per source. Paraphrase everything else.
5. Every exercise must be solvable from numbers given IN the exercise or in the chapter. Give each
   exercise a one-line expected answer in planning/ledgers/P-C.md.
6. Mark every command you did not run "(untested here)" and add a "Not verified on live hardware"
   list in the sources section, plus a "Run here" line with the lab and its check count.
7. Quote derived numbers (sums, ratios) only if the lab computes them; the lab file is then the source.
8. Keep the 20 checkpoint questions and Exercises section; plain beginner-first language written like the gem books (planning/LANGUAGE_RULE.md); no
   exclamation marks.
9. SOURCE BREADTH (checked by tools/check_coverage.py)
   - Before writing, run: python3 tools/study_rag/brief.py P.C --q "<main term 1>" --q "<main term 2>" --q "<main term 3>"
  and python3 tools/check_coverage.py P.C. Read the top hits of every gem book that is not already mapped.
   - Add a "## Corpus search" section to the ledger: the queries you ran, the books and chapters found, and for each
  either "used in section N" or "read, nothing new" or "not relevant because ...". "Not read" is not allowed
  for a book scoring 4 or more in the coverage report.
   - Cite every gem book you actually used in "Sources and review notes" by its folder name (for example
  distributed-ai-systems). Every mapped nvidia-devops file must also be cited by file name.
10. When finished, run: python3 tools/validate_chapter.py P.C
   and fix every FAIL and every item under "NOT FOUND" or "DIFFERENT context". Paste the final
   validator output at the end of your reply.
```

## Rules every drafting model must follow (added after the 10.8 and 10.9 reviews)

```text
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
```

## Step 2: Argon improves (paste this prompt after Flash finishes; give Argon the chapter number)

```text
Review and improve chapter P.C that another model drafted. You are the SOURCE-FIDELITY EDITOR.
Do not shorten it and do not remove unique facts or depth. Work in this order:

A. Run: python3 tools/validate_chapter.py P.C
   For every number listed as NOT FOUND or DIFFERENT context, open the cited source and decide:
   (1) it matches, ok; (2) the source says something different: correct the chapter to the source;
   (3) the source says nothing: remove the claim, or label it "my estimate" and list it under
   "Explicitly labelled inferences". Never keep an unsourced claim stated as fact.
B. Re-read every story, customer scenario and exercise against the source note it came from. Fix any
   changed figure (percentages, multipliers, wattages, prices, counts, dates).
C. Check every exercise is answerable from the data inside the exercise or chapter. Rewrite or
   replace any that are not. Put expected answers in planning/ledgers/P-C.md.
D. Check every command is marked "(untested here)" unless run, and that the sources section has
   "Run here" and "Not verified on live hardware" lists. Add them if missing.
E. Language: short sentences, terms explained at first use, no exclamation marks, no hype wording.
F. Legal and quote rules: no quotation over 15 words except where a source note itself quotes a
   licence; no invented section or clause numbers.
G. Re-run the lab, then python3 tools/validate_chapter.py P.C again. Reply with a short list of every
   change you made (old text -> new text -> source). Do not commit.
```

## Step 3: Claude validates (the author asks "validate P.C")

Claude runs `python3 tools/validate_chapter.py P.C` and then independently:
- opens every book the coverage check lists as UNRECORDED or low-scoring-but-plausible (for example a BCM manual) and reads the relevant chapter, then adds or asks for the missing material,
- searches the corpus for the chapter's exact terms (commands, package names, error codes) and checks for sources the heading queries missed,
- reads the Volume 19, 20 and 16 chapters that match the topic,
- re-checks each flagged number and every story against the source note,
- reads the exercises and checks they can be solved,
- runs the lab, build, lint and mermaid check,
- reports PASS or a short list of issues. The author decides whether to send it back to Argon.

## What the validator does and does not catch

- Catches: changed or invented numbers (it searches the cited notes, gem books and the chapter's code),
  missing 20 questions or Exercises, exclamation marks, missing diagrams, failing labs, missing
  untested/not-verified notes.
- Does not catch: a wrong claim that has no number, a wrong explanation, or a number that exists in
  the sources but in a different context with similar words (these appear under "DIFFERENT
  context" for a human check). Derived arithmetic (ratios, sums) shows up as "not found" unless the
  lab computes it; that is expected and harmless.
