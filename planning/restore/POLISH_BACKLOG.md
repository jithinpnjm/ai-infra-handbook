# Polish backlog (second pass after waves)

1. Templated section closers ("Before you...", "Keep this in mind...", "Remember..."): 76 found in Part 1 chapters 1.2-1.21 (most in 1.16: 12, 1.19: 9, 1.15: 8). Keep only closers that add specific guidance from the source; vary or delete the rest. Never add advice that is not in the source.
2. Code-format consistency (flags, config options, file names) in "How it fails", tables and checkpoint answers: 1.2-1.15 were produced before the rule; re-run tools/restore/restore_code_format.py and extend its detector to short flags.
3. Abbreviations leaked from sources (HLW, SCL, ASP): grep and spell out.
4. Exercises/Lab/Sources sections copied unchanged by early waves (1.2-1.15): rewrite exercise prompts and lab leads in voice.
5. Closing sentences in 1.21 sections 3, 6, 12 removed by hand; check other security chapters for advice beyond the source.
6. Headings that still contain source abbreviations (FP, LP, HLW, SCL, ASP...) in Parts 1-4: grep '^#.*\(FP\|LP\|HLW\|SCL\|ASP\)' docs and spell them out.

- 6.10: source says "four" triage commands but lists three (agent avoided the count).
- 6.15 Exercise 1: "three intermediate hops" conflicts with its arrow path (source issue).
