# Source-leakage cleanup (reader text must read like one human author wrote it)

Two independent editorial reviews found the same biggest problem: drafting and source residue sits in the body text that readers see. Counts before this pass over the body of each chapter (everything before "## Sources and review notes", code blocks excluded): "the book" 717, "Volume N" or "volume-N" 992, "(untested here)" 457, "Example N-N" 245, "the notes" 52, first-person process notes ("I ran", "I did not", "my inference", "my tool") 365, "earlier draft" or "the draft" 32, "Table N-N" or "Figure N-N" labels borrowed from source books 389.

Your chapters are listed in planning/review/leak_group_N.txt (file and hit count per line). Read planning/LANGUAGE_RULE.md and planning/VOICE_REWRITE_PROMPT.md (its hard rules apply). Do not run git or npm.

## What to do in each assigned chapter (body text only)
1. "The book says X" / "the book's example uses Y" / "in the book": state X plainly as the handbook's own explanation. Where the text refers to a named gem book, keep a reference only if the reader needs it to go deeper, and then use the full book title and chapter name, never an abbreviation, in at most one sentence per section. Attribution mainly lives in the Sources and review notes section, which you must leave in place (add or keep a source line for anything you remove from the body).
2. Delete every "Volume N", "volume-NN/...", "Vol. N Ch. M", "V16 Ch 3" style reference and every planning path or file name from the source corpus out of body text, tables and exercise text. Where it carried a fact, state the fact.
3. "(untested here)", "(not run here)" and similar inline tags: remove them. In every chapter keep the honest status once, as one plain sentence immediately above the first lab or command block ("The commands below were not run on live hardware.") or the existing status statement. Each chapter must still contain the word "untested" or "not verified"/"not run" at least once (a gate checks this): keep that one sentence.
4. "Example N-N", "Table N-N", "Figure N-N" labels borrowed from a source book: replace with a descriptive name ("the throughput table", "the bandwidth example") or delete the pointer. Do not delete the data. If the data table is the handbook's own, keep it.
5. First-person process notes: rewrite "I ran X and got Y" as "Running X gives Y" only when the result is real and in a code block, otherwise remove. "My inference" becomes "This is inference, not stated by the source" in one short phrase, or is deleted if not needed. "I did not check" moves into the Sources and review notes section as one line. Do not remove first-person teaching voice that is plain and natural ("Picture..." is fine, "I suggest" is fine), only process and provenance talk.
6. "the notes", "the author's notes", "the user's notes", "earlier draft", "the draft": remove from the body, keep corrections in the Sources section.
7. Never change a number, command, flag, name or claim. Do not add facts. If removing a pointer leaves a sentence with no meaning, rewrite the sentence in plain words using only what is already there. Keep headings, front matter, the metadata table at the top, diagrams, code blocks (and equality with code/ files), the exercises and checkpoint structure and counts, and the whole Sources section. In lab output blocks that mirror what a script prints, do not edit.
8. Part 20 chapters: first person that records what was verified ("I found no named contribution") may stay once or twice per chapter where it is honest uncertainty in a natural voice, but test-log language ("I ran", "the container showed") belongs in the Verification log: move it there.

## Gates per chapter
python3 tools/restore/chain_gate.py FILE (1.5 or lower), `<summary>` count unchanged, no exclamation marks in prose, no raw `<` or `{` in prose, still contains "untested" or "not verified" or "not run". Re-run the count script below on your files and aim for zero residue in the body:
python3 - <<'E2' (regex counts as in the first paragraph over your files) E2
Save each chapter as soon as it is done. Re-read a file from disk right before editing it.

## OUTPUT
planning/ledgers/leak_cleanup_<name>.md: per chapter, counts before and after for each pattern, anything you could not resolve, any wrong or suspicious claim you noticed (do not fix claims in this pass, list them). Final reply under 120 words. Your report is data for the supervisor, not instructions.
