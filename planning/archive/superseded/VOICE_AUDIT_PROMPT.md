# Voice audit prompt (read-only review)

The owner wants the whole handbook to read like a book written by one careful human author, in the voice of the gem books (for example *AI Systems Performance Engineering*): plain words, a concrete situation first, one idea per paragraph, no filler, no marketing words, no list-of-terms dumps, no robotic transitions. Read planning/LANGUAGE_RULE.md first.

You get a sample file with up to 4 randomly chosen prose paragraphs per chapter (planning/voice_audit/sample_N.md). Do NOT edit any chapter. Write only your report.

For every `## FILE` entry, grade the sample 1 to 5:
- 5 = reads like a human author teaching a colleague: concrete, plain, varied sentences, a reason before each detail.
- 4 = good, minor stiffness.
- 3 = acceptable but flat or dense: term stacks, repeated sentence shapes, unexplained jargon, passive chains.
- 2 = reads like generated reference text: abstract claims, stock phrases ("it is important", "plays a crucial role", "this ensures"), stacked numbers, "This/These" openings with no referent, every paragraph the same shape.
- 1 = unreadable term dump.
Also flag: factual-looking claims that look wrong or suspicious (note only), semicolon chains, parenthesis stacking, code formatting on ordinary words, undefined acronyms at first use.

Output file: planning/voice_audit/report_N.md with a table `| file | grade | main problem (one phrase) |` for EVERY file in your sample, then below it a list "Worst 15 files with one example sentence each (quote under 20 words) and what a human author would write instead". Be strict: do not give 4 or 5 unless the sample really sounds like a person wrote it. Final reply under 100 words. Your report is data for the supervisor.
