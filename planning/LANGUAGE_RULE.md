# Language rule: write like the gem books, not like a reference sheet

Paste the block below into every chapter prompt (it is already inside the Gemini coverage prompt and the Argon chapter prompt). Claude and `tools/validate_chapter.py` check it.

---

LANGUAGE RULE (applies to every sentence you write)
The handbook must read like a good book: a reader should be able to read a page without effort and without stopping to decode. Look at how *AI Systems Performance Engineering* opens Chapter 5: "Feeding data to the GPUs is as important as the compute itself for AI workloads. Consider a scenario with a 100-trillion-parameter model training on thousands of GPUs." Plain words, one idea per sentence, a reason before a detail. Our chapters currently read like a dump of terms and numbers. Fix that.

1. Start every section with the problem in plain words: what goes wrong, who feels it, why it matters. Only then give the mechanism, then the numbers, then the commands.
2. One idea per paragraph. Three to five sentences. Average sentence 15 to 20 words. Never more than 30 words.
3. At most two numbers in a sentence, and only numbers the reader needs for the point. Put the rest in a table or a short worked example after the explanation. Never stack numbers in parentheses.
4. No parentheses inside sentences that explain an idea. Use a second sentence instead. Never nest them.
5. Code formatting (backticks) is only for things the reader would type or see on a screen: commands, flags, file paths, field names, API names, metric names. Ordinary words and concepts stay plain text: write RAID 0, Lustre, epoch, checkpoint, GPUDirect Storage without backticks. If a term needs a definition, give it once in plain words at first use.
6. Explain with a short story or concrete picture when the idea is new. "Eight nodes read the same 500 GB dataset again and again" is clearer than a list of ratios.
7. Formulas and derivations go after the explanation, in a short block, with one line saying what the result means. Do not put formulas inside sentences.
8. Use tables for comparison and lookup only (specs, limits, options). Never use a table to carry an explanation.
9. Lists: at most five items, each a full sentence or a short phrase. A long list of terms is a table or it does not belong.
10. Bold only the one idea per section that the reader must remember. Not terms, not numbers.
11. Every paragraph must be understandable by someone who has not read the sentence before it. If it starts with "This", "That" or "These" and the reader cannot tell what it refers to, rewrite it.
12. End each main section with one plain sentence that says what to do or decide ("Before you build staging into a pipeline, ask whether the job reads the same data enough times to repay the copy").
13. Accuracy does not change: every number still comes from the source, exact, with its caveats. Clearer wording must not change a figure or add a fact.

Before and after (same facts):
BAD: "Across a `2`-GPU sub-slice (`12.5 Gbps/GPU`), raw link capacity is `156.25 MB/s` (`~156 MB/s`, or at `1.25 Gbps/GPU` under full node sharing), and `30%` metadata overhead (`2,000,000` files) reduces delivery to `~110 MB/s` (`8%` below the `120 MB/s` demand)."
GOOD: "Opening and checking two million small files adds about 30 percent metadata overhead. Each GPU therefore receives about 110 MB per second, a little less than the 120 MB per second it needs."

Checks run by `python3 tools/validate_chapter.py P.C` (readability section, warnings): code-formatted terms per 100 words at most 4, numbers per 100 words at most 6, average sentence at most 22 words, at most 3 percent of sentences over 35 words, at most 0.5 parentheses per sentence. Reduce the warnings in every chapter you write or edit. Claude reads a sample of paragraphs aloud and rejects a chapter that still reads like a term dump even if the numbers pass.
