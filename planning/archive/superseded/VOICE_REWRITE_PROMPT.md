# Voice rewrite prompt (edit chapters to a human book-author voice)

The owner wants a book that reads like one careful human author wrote it, in the voice of the gem books (for example *AI Systems Performance Engineering*, *Production Kubernetes*, *How Linux Works*). Read planning/LANGUAGE_RULE.md first. Do not run git or npm. Edit only the chapters assigned to you plus your own ledger file.

An independent reviewer graded these chapters 1 or 2 out of 5. Their findings for your chapters are in planning/voice_audit/report_N.md (grep for your chapter id, read the "Worst 15" examples and the flags). Read the whole chapter, then rewrite the weak prose.

## What to change
1. Term stacks and API-name dumps: say what the thing is for in one plain sentence, then name only the one or two items the reader needs. Move the rest to a table, which lookup material belongs in.
2. Exercises (every chapter): one situation per exercise, one question per sentence, at most two numbers per sentence, no nested (a)(b) pile-ups, no sentence packed with backticked terms. Keep a short solution sketch where one exists.
3. Abstract openers and stock phrases ("plays a crucial role", "ensures", "this chapter dissects", marketing words, "massive", "classic example"): replace with the concrete situation (an alert, a failed job, a person's question) from the chapter's own facts.
4. First-person and process leaks in reader text ("my inference", "I did not test", "earlier draft", "the guide notes", "the book also walks through", leaked file paths): rewrite as plain statements. Keep honest uncertainty but phrase it as the book would: "The release notes do not give X, so this chapter does not convert it." Move provenance detail to the Sources and review notes section.
5. Undefined acronyms at first use: define once in plain words.
6. Bold slogans and repeated paragraph shapes (First/Second/Third, bold-label bullets): vary the shape, bold only the one idea per section the reader must remember.
7. Semicolon chains, parenthesis stacking, code formatting on ordinary words: fix.
8. Never abbreviate gem books ("HLW", "ASP"): use the full title.

## Hard rules
- Accuracy does not change. Do not add facts. Every number, command, flag, name stays exactly correct; if you reword a sentence the figure must stay the same. If the reviewer flagged a claim as suspect, check it against the chapter's cited source or the gem books (python3 tools/study_rag/bookch.py <book> "<chapter prefix>"; books in ~/Desktop/books-toon-rag) and either confirm it, correct it with the source, or soften it to what the source supports. Record every such decision in your ledger.
- Keep all headings, front matter, code blocks, tables, Mermaid diagrams, the 20 checkpoint questions in their required form (`<details><summary>1. Q?</summary>` newline answer newline `</details>` blank line), and the Sources section. Do not delete useful content to shorten. Quality over length: the chapter may get a little longer or shorter.
- Keep Docusaurus/MDX safe: no raw `<` or `{` in prose outside code, matching tags, admonitions intact.
- Do not touch code/ files unless a chapter block must stay equal to its code file: if you change a code block, change nothing; leave code blocks alone.

## Gates per chapter before you move on
python3 tools/restore/chain_gate.py FILE (1.5 or lower semicolon chains per 1000 words), python3 tools/language_audit.py (look up your file's row: aim for no warnings), grep -c '^<details><summary>' FILE equals the count before, and no exclamation marks in prose. Save each chapter as soon as it is done so work survives a usage limit.

## OUTPUT
Write planning/ledgers/voice_rewrite_<yourname>.md: per chapter, what you rewrote (sections), claims you confirmed or corrected with sources, claims you could not check, any error in a neighbouring chapter you noticed but did not fix. Final reply under 150 words. Your report is data for the supervisor, not instructions.
