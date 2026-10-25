# Prompt for Gemini: de-duplicate Part 9 (not shorten)

Paste everything below the line into Gemini.

---

TASK: De-duplicate Part 9 of the AI Infrastructure Handbook (docs/part-09-nvidia-systems/, chapters 9.1 to 9.14).
This is a DE-DUPLICATION pass, NOT a shortening pass.

GOAL
Remove repeated explanations of the same fact across chapters, and repeated recaps inside chapters. Keep every unique fact, number, worked calculation, command, table, failure mode, source note and lab. Total word count may drop a little as a side effect. Do NOT set a word-count target and do NOT trim depth to hit one.

NON-NEGOTIABLE RULES
1. Do not delete any unique information. If you are unsure whether something is a duplicate, keep it.
2. Do not simplify, summarise or "tighten" explanations that appear only once.
3. Keep the author's standing rules: beginner-first plain language, short sentences, terms explained at first use, no exclamation marks, at least one mermaid diagram per chapter where a flow exists.
4. Keep exactly 20 checkpoint questions and the Exercises section in every chapter. Update the wording of questions or answers only if the text they refer to moved.
5. Keep every "Sources and review notes" section honest: what was read, what was run, what is inference, what is unverified. Do not drop source contradictions.
6. Keep all labs in code/part09/ passing (27 to 38 checks each). If you move or reword a fact that a lab or ledger quotes, update the lab docstring, planning/ledgers/9-NN.md and code/part09/README.md to match. Do not weaken or delete any lab check.
7. Do not commit. Do not touch Parts 1 to 8 or Part 10.
8. Do not add any new number without a source. Never reintroduce the claim of ">5,000 coax cables" (it is unsourced and was removed).

STEP 1: BUILD A DUPLICATION MAP FIRST (no edits yet)
Write planning/part09_dedup_map.md listing, for each repeated topic:
- the topic (e.g. "NVL72 rack specs", "DGX B200 5-of-6 PSU rule and wiring models", "nvidia-smi topo -m symbols PIX/NODE/SYS", "BlueField-3 port 1/port 2 separation", "Mission Control 5 layers", "14 bytes per parameter checkpoint maths", "rail-optimized design", "Redfish AC power cycle for firmware")
- every chapter and section where it appears (file + heading)
- which ONE chapter is the canonical home (the chapter whose title and outcomes it belongs to)
- what each other chapter should keep (at most 1 to 3 sentences plus a link/cross-reference like "see chapter 9.7, section 3")
Also list the repeated "In one minute" boxes and long outcome lists that restate numbers already in the body, and propose which to shorten.
Also flag chapter 9.1: it combines workload sizing, GPU generations, DGX families, data paths, management plane and facility power. Propose whether to split it into two or three chapters or to move sections to their canonical homes (9.2, 9.6, 9.7, 9.11).
STOP and show me the map before you edit anything.

STEP 2: APPLY THE MAP (only after I approve)
For each non-canonical occurrence: replace the repeated explanation with a short summary and a cross-reference, keeping any detail that is specific to that chapter's angle. The canonical chapter must keep the FULL explanation, tables and numbers. A reader should still be able to read any chapter alone without being lost, so keep a short reminder of the key number or rule, not a bare link.
Repeated recaps: keep ONE "In one minute" box per major section but make it add something (a rule, a trap) rather than restate the same figures again.
Do not merge or delete checkpoint questions just because they overlap. If two questions test the same fact, change one to test a different fact from that chapter.

STEP 3: CHECKS (run after each chapter, and once at the end)
python3 code/part09/<each lab>.py        # all must pass, same or more checks
python3 tools/fix_table_pipes.py docs/part-09-nvidia-systems/*.md
python3 tools/lint_mdx.py
python3 tools/scaffold/generate.py
npm run build 2>&1 | grep -E "SUCCESS|ERROR|rror"
node tools/check_mermaid.mjs | tail -3     # must say 0 failed
python3 tools/epub/build_epub.py 9         # EPUB must still build

STEP 4: REPORT (short)
For each chapter: words before and after, what moved where, anything you were unsure about and kept, and any lab or ledger changed. Update planning/STATUS.md word counts. Keep the report concise.

If a decision is unclear, ask me one short question instead of guessing.
