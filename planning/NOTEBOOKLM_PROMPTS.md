# NotebookLM: instructions and prompts for writing the handbook from the uploaded sources

NotebookLM answers only from the sources in the notebook and gives citations. That is its strength here: it is hard for it to invent facts. Its limits: each answer is short (about 1,000 to 1,800 words), it cannot run code or labs, it forgets the structure of the whole book, and it will happily summarise. So the work is done one section at a time, with a fixed outline and a fixed voice, and every section is checked afterwards.

Use the two notebook-level instructions below once, then the per-section prompt for every section.

## 1. Notebook instruction (Chat settings, "Custom" style and response length "Longer")

Paste this into the notebook's chat configuration:

```text
You are the author of "The AI Infrastructure Handbook", a book for a working AI platform and DevOps engineer who is aiming for NVIDIA GPU platform roles. Write only from the uploaded sources. If the sources do not contain something, say "not in the sources" and stop; never fill gaps from general knowledge.

Voice: write like the best chapters of the source books. Plain words, short paragraphs of three to five sentences, one idea per paragraph, a reason before every detail. Explain the why, tell the author's examples, stories, analogies and history, and keep the author's warnings. Do not write a summary, a list of terms, or a table instead of an explanation. Use a table only after the explanation, for comparison or lookup.

Depth: when a source spends three paragraphs on an idea, spend about as many words on it. Keep every script and command sequence the author builds up, with the author's reason for each step. Keep the author's numbers exactly. Say "in the book's example" for example figures. Do not round, merge or improve numbers.

Format: markdown. Headings only for real sections. Put commands, flags, file paths and field names in code formatting; write everything else in plain text (write RAID 0, Lustre and epoch without code formatting). At most two numbers in a sentence. No exclamation marks, no hype words. End each section with one plain sentence about what to decide or do.

Citations: after every paragraph give the source name and chapter or section in brackets. If two sources disagree, show both and name them.
```

## 2. The per-section prompt (one section per run)

Replace the angle brackets. Take the chapter title and section list from `planning/structure.txt` and the book chapters from `planning/coverage/GEM_BOOKS_MASTER.md` and `planning/coverage/maps/`.

```text
Write section <number and title> of chapter <part.chapter, title> of the handbook.

Sources to use (and only these): <book A, chapter x "title">; <book B, chapter y "title">; <nvidia-devops note file name>.
Reader already knows: <chapters it builds on>. Do not repeat what those chapters teach; give one sentence of reminder.

Cover, in this order: <the ordered list of topics for this section>.
Length: about <900 to 1,400> words.

Requirements:
1. Follow the voice and depth rules of the notebook instruction.
2. Use every example, script, story, warning and number in the named source passages that belongs to these topics. Keep the author's order and reasons.
3. After the section, list in a short block: (a) every number you used and its source, (b) every source paragraph or example in the named chapters that you did NOT use, with one line saying why.
4. Do not write a summary, key takeaways, or a conclusion unless asked.
```

## 3. Prompts to check coverage after a chapter is assembled

Run these in the chat after you have pasted the finished chapter text as a note or source.

```text
For <book, chapter "title">: list every distinct concept, example, script, story, warning and number in the chapter, in the book's order. Then, for each item, say whether the pasted chapter text contains it, only mentions it, or leaves it out. Show the left-out items first.
```

```text
Read the pasted chapter text and the source chapter side by side. Find every paragraph of the source chapter whose explanation is reduced to a heading, a table row or a single sentence in the pasted text. Quote the source paragraph's first sentence and say what was lost.
```

```text
List every number in the pasted chapter text. For each, give the source passage it comes from. Flag any number you cannot find in the sources.
```

## 4. What NotebookLM cannot do for this book

- It cannot run the labs, so the self-checking Python models and the "untested here" markers still need our tools (`tools/validate_chapter.py`, `tools/book_passages.py`, `tools/loss_check.py`).
- It does not keep the whole outline in mind; always paste the outline and the "reader already knows" list.
- It will not produce a 10,000-word chapter in one answer. Ask section by section and assemble the pieces.
- Large uploads: check that every important book is fully ingested (open the source and look at its chapter list), because very long books can be truncated.
- It can still paraphrase too loosely. The third check prompt (numbers) and our validators are the safety net.

## 5. Suggested order of work

1. Pick one chapter that already exists in the handbook (for example 6.7 user accounts on clusters).
2. Generate it section by section with the prompt in section 2.
3. Run the three check prompts, and fix gaps with follow-up prompts ("add the pull-based sync design, the master-sync script and the NIS history from chapter 11").
4. Paste the assembled chapter into the handbook as a draft file, run `python3 tools/validate_chapter.py P.C`, `python3 tools/book_passages.py <book> "<chapter>" P.C`, and compare it with the Gemini version.
5. Keep whichever version reads better and covers more; merge the best paragraphs.
