# Brief: write Gemini figure specs (you do NOT draw anything)
Input: a worklist JSON (list of {id, f: docs file path relative to repo root, h: exact ## heading line, w: words, ch}). Repo root: /Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook
For each item, in order: Read the section (file f, from the heading h to the next "## " heading; use Read with offset/limit or grep -n to find it). Decide if ONE simple infographic would make it easier for a beginner to understand. If not (pure lab commands, long reference lists, nothing visual), write skip with a reason.
Write results to the output file named in your task as a JSON list, appended in batches of ~10 items (rewrite the whole file each time, valid JSON always). Each entry:
{"id": <id>, "skip": false, "title": "<=7 words", "layout": "<one sentence-or-two layout instruction>", "labels": ["every word/phrase that appears in the image, each unique"], "note": "<one bottom note sentence, or empty>", "alt": "<one sentence describing the picture>", "caption": "<one sentence, the lesson, plain language>"}
or {"id": <id>, "skip": true, "reason": "..."}
Rules (quality matters, hard-won):
- FACTS ONLY from the section text. Never invent numbers, commands, or flags. If unsure, leave it out.
- Layouts that work: (a) table with 2-3 columns and 3-6 rows, (b) 3-5 stacked rows joined by DOWN arrows, (c) one horizontal row of 3-5 boxes with right arrows, (d) two side-by-side panels compared, (e) a hub box with 3-4 boxes around it. AVOID: nested boxes, loops, crossing arrows, more than 16 labels, long sentences inside boxes (max ~8 words per box).
- Say arrow direction explicitly in layout ("arrowheads point down").
- Every label must be unique in the image (never repeat a word group like "85%" or "Bandwidth" twice); labels list must include title, every box text, and the note text, exactly as they should be spelled. Use plain ASCII punctuation.
- Beginner-friendly wording, plain English. The reader is a beginner preparing for a Senior SRE interview (Linux, networking, Kubernetes, Python, GPU infra).
- Prefer the single most important idea of the section (the mechanism, the comparison, the decision, the failure checklist).
- Do not edit docs. Do not run anything except Read/grep/Write of your output file. Reply in under 30 words when done.
