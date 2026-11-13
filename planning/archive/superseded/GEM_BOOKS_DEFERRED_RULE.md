# Rule to paste into every chapter prompt for Parts 12 to 19

Add this block to the prompt of whoever writes a chapter in Part 12 or later.

---

BOOK-CHAPTER INPUT RULE
Before writing chapter P.C, open planning/gem_books/DEFERRED.md and list every row whose "future part and topic" matches this chapter. Those rows are required input, not optional reading:
1. Read each listed book chapter in full with python3 tools/study_rag/bookch.py <book> "<chapter title prefix>".
2. Put the content of every listed chapter into this chapter (exact numbers, commands, tables and warnings from the book; nothing from memory), or write one line in the ledger saying why a listed chapter does not fit, so I can decide.
3. Cite each book by folder name and chapter title in "Sources and review notes", and say what you read in full.
4. In planning/gem_books/DEFERRED.md change the row's status from DEFERRED to DONE with the handbook chapter and section, or to PROPOSED_NEW_CHAPTER if it needs its own chapter.
5. Do not write any DEFERRED row into a different part's chapter.
6. LANGUAGE: follow planning/LANGUAGE_RULE.md in full (book-style prose, plain words, at most two numbers per sentence, code formatting only for things you type or see on screen). The validator prints readability warnings; reduce them.
