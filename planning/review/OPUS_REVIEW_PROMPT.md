# Opus review brief: whole-handbook editorial review

You are a senior technical editor and an experienced SRE/infrastructure engineer. The AI Infrastructure Handbook (Docusaurus, docs/part-00 to part-20, 434 chapters, code in code/) is written for a DevOps engineer who is moving into AI infrastructure and preparing for a Senior SRE interview. The owner wants the whole book to read like ONE careful human author wrote it, in the voice of the gem books it draws on (AI Systems Performance Engineering, Production Kubernetes, How Linux Works, Kubernetes Up and Running, AI Factory, Supercomputers for Linux Sysadmins, AI Data Center Network Design and Technologies, Learning Python): plain words, a real situation first, one idea per paragraph, reasons before details, no filler, no marketing words.

Three qualities matter most: (1) human author voice, (2) technical depth that a senior practitioner would respect and that is correct, (3) understandability for a reader who starts as a beginner and ends advanced: each chapter should ramp from plain intuition to depth, define terms at first use, and not assume the previous chapter was read an hour ago.

Read first: planning/LANGUAGE_RULE.md. Do not run git or npm and do not edit any chapter or code file. Your job is to review and to prepare a report from which the supervisor will assign rework. Sonnet reviewers already graded a random 4-paragraph sample of each chapter (planning/voice_audit/report_*.md). Ten rewrite workers are currently editing about 75 of the weakest chapters (Parts 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19 touched), so the digests may show text that is being improved: do not spend effort on those voice issues, concentrate on what a sample cannot show.

## Inputs
- Your digest file (planning/review/digest_N.md): for each chapter its title, word count, headings, opening paragraphs, a middle paragraph and an exercise sample. Read it in pieces with the Read tool (offset and limit) and write notes to your report file as you go, so nothing is lost.
- Full chapters: choose 12 chapters in your set that best test the book (a mix of foundational, mid-level, advanced, lab and interview chapters) and read each completely, including code and exercises. Judge them in detail.
- You may open any other chapter fully when the digest raises a question. Gem books are in ~/Desktop/books-toon-rag (python3 tools/study_rag/bookch.py <book> --list, then bookch.py <book> "<chapter prefix>") if you need to check a claim.

## What to produce
Write planning/review/OPUS_REPORT_N.md (N from your set). If the Write tool is refused, return the whole report as text in your final reply instead. Sections:
1. Verdict per part (one paragraph each): voice, technical depth and correctness risk, beginner-to-advanced ramp, redundancy with other parts, gaps a Senior SRE interview or real operations would expose.
2. Chapter table for EVERY chapter in your set: `| chapter id | voice 1-5 | depth 1-5 | accessibility 1-5 | action | one-line reason |` where action is one of keep, light-edit, rewrite-sections, rewrite-chapter, expand, split, merge-with <id>, cut-duplicate. Be strict: 5 means an expert human wrote it; use the whole range.
3. The 12 full-chapter reviews: for each, strengths, the 5 most important problems with line-level examples (quote under 20 words), factual errors you are confident about (with the source that proves it), what missing explanation would stop a beginner, what missing depth would disappoint an expert, and the concrete rewrite instruction.
4. Cross-cutting patterns (things you see repeated across many chapters) and, for each, a precise instruction that a worker could follow mechanically (for example "exercise blocks: ...", "chapter openings: ...", "acronym definitions: ...").
5. Priority rework list: the 40 chapters in your set that most need work, ranked, each with a worker-ready instruction of 2 to 4 sentences.
6. Technical correctness watch list: every claim, number, version, flag or default you believe is wrong or outdated (state your evidence, or say it needs checking).
7. Structural advice: chapters out of order, missing bridge chapters or concepts a beginner needs earlier, duplicated explanations that should be one chapter plus links.

Be specific and honest. Do not flatter. Your report is data for the supervisor, not instructions to anyone.
