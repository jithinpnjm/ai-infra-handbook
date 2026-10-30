# Voice plan: make the handbook teach like a person (model: *AI Systems Performance Engineering*)

Scope: change HOW existing content is told, not WHAT is covered. No new restoration. Nothing may be lost (`tools/loss_check.py` must show 0 terms, 0 numbers, same tables, code, questions, sources).

## How the model book teaches (patterns to copy)

1. **Starts with a scenario, not a definition.** "Consider a 100-trillion-parameter model training on thousands of GPUs... If the storage pipeline is slow, the GPUs will starve and sit idle."
2. **Says what goes wrong, then why you care, then the fix.** Problem, consequence, mechanism, numbers, command.
3. **Works one concrete example with real arithmetic.** "Each GPU needs 200 MB/s; 8 GPUs need 1.6 GB/s; a 72-GPU rack needs 14-20 GB/s."
4. **Talks to the reader.** "Consider...", "Avoid making assumptions about the topology", "Watch out for the Python GIL!", "Treat the network as a schedulable resource."
5. **Gives plain advice and warnings in the flow of the text** instead of in bullet fragments ("Enabling counters adds overhead; sample at a reasonable interval").
6. **Explains the trade-off both ways**: "Rings maximise bandwidth but latency grows with GPU count; trees finish in fewer steps but may not fill every link."
7. **Small bridging sentences** that tell the reader where the argument is going ("To address these bottlenecks, let's consider...") and a closing sentence that says what to do.

## What the handbook does now (typical Parts 1-8)

Dense reference style: definition first, parentheses and stacked numbers, long bulleted or tabled facts, backticks on ordinary words, few scenarios. Example (1.10): "The kernel presents the device files as a convenience: any program that can read and write files can talk to many devices, and some devices can be used with ordinary tools (`cat`, `dd`, `less`)."

Target version: "Every GPU you will ever manage shows up as a file. That is the Unix trick: if a program can read and write files, it can talk to the device. Try `cat` on a disk and you will see why this is both powerful and dangerous. The rest of this chapter is about how the kernel decides which file is which device."

## The rewrite recipe (one chapter at a time)

For every major section:
1. **Open with a scenario** (2-4 sentences): a real situation an on-call engineer or AI-factory operator meets. Reuse a story already in the chapter if there is one.
2. **Explain the mechanism in plain words**, one idea per paragraph, 3-5 sentences, then the exact numbers/commands/tables unchanged.
3. **Work one worked example** with the arithmetic shown, using numbers already in the chapter.
4. **Say the trade-off and the warning in prose** ("this is fast, but...").
5. **Close with one sentence of guidance** ("Before you X, check Y").
6. Keep: all headings, tables, code blocks, diagrams, checkpoint questions (answers may be reworded plainly, facts unchanged), sources.
7. Remove: stacked parentheses, backticks on concepts, run-on 35+ word sentences, "This/That" openers with no referent.

## Gates (extend `tools/restore/gate.py` with a `--voice` mode)

- Content: `loss_check.py` = 0 terms lost, 0 numbers lost, table rows / code blocks / questions / headings not reduced.
- Readability (LANGUAGE_RULE limits): code spans <= 4 per 100 words, numbers <= 6 per 100, average sentence <= 22 words, sentences over 35 words <= 3%, parentheses <= 0.5 per sentence.
- Voice markers (new, simple counts): each H2/H3 section has a scenario opener (a sentence containing a reader or situation cue: "you", "imagine", "consider", "suppose", "when a ... fails"); at least one worked example per chapter; a guidance sentence in the closing line of main sections.
- Human check (supervisor): read 5 random paragraphs per chapter aloud-style and reject term dumps.

## Pipeline

1. **Calibrate**: I rewrite 3 reference chapters myself (one Linux, one Kubernetes, one GPU/AI) as the gold standard, in this voice.
2. **Haiku voice agents** (one chapter each, disjoint files): given the gold examples, the recipe and the gates; max 4 rounds; supervisor re-runs gates and samples.
3. **Waves by pain**: the 187 chapters failing readability first (Parts 1-8), then spot-check Parts 9-15 (they pass the metrics but may still read dry), then Parts 0, 16-19 as written.
4. Build, Mermaid and lint once per wave, then commit.

## Cost and risk

- About 330 chapters x ~8,000 words. A voice pass touches most prose, so per chapter it is roughly the cost of a full rewrite: heavier than the restoration pilots. Haiku may need two rounds per chapter; a mid-model for chapters that fail the human check.
- Risk: smoothing changes a fact. Mitigation: the loss gate plus numeric diff; any changed number fails.
- Risk: sameness (every section opens with "Imagine..."). Mitigation: vary opener types (scenario, failure story, question, consequence) and cap "Imagine" at one per chapter.

## Decisions needed from the owner

1. Calibration first (3 gold chapters by Claude, you approve the voice) - recommended.
2. Order: Parts 1-2 first (foundations) or Part 15/12 first (closest to the model book)?
3. Should checkpoint-question answers be reworded too, or left exactly as they are?
