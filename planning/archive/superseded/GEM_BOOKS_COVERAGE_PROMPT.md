# Prompt for Gemini (Argon): make sure the relevant chapters of eight gem books are in the handbook

Paste everything below the line into Gemini Argon. Claude validates afterwards ("validate book <name>").

---

TASK: Check, book by book and chapter by chapter, that the chapters I care about in eight gem books are covered in the AI Infrastructure Handbook. Add what is missing from those chapters. Do NOT invent new topics, and do NOT cover book chapters I do not need.

WHO I AM AND WHAT I NEED
I am an AI platform / DevOps engineer working toward NVIDIA GPU platform roles (DGX, GPU Kubernetes, Slurm/BCM, networking, inference platforms). I do not need everything in a book. I need the chapters that matter for that job, with their real content: the exact numbers, commands, tables, procedures and warnings from the book. A chapter I mark as skipped is fine. A chapter I need must not be missed.

THE EIGHT BOOKS (folder names in ~/Desktop/books-toon-rag/)
1. supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to-hardware
2. how-linux-works-3rd-edition
3. ai-systems-performance-engineering
4. ai-data-center-network-design-and-technologies
5. learning-python-6th-edition
6. ai-factory
7. production-kubernetes
8. kubernetes-up-and-running-3rd-edition

TOOLS
- List a book's chapters: python3 tools/study_rag/bookch.py <book> --list
- Read one chapter in full: python3 tools/study_rag/bookch.py <book> "<chapter title prefix>"
- Find where the handbook already covers something: python3 tools/study_rag/query.py "<terms>" and grep -rn "<term>" docs/
- Handbook structure: planning/structure.txt, planning/STATUS.md. Parts 1 to 11 are written. Parts 12 to 19 are not written yet.

PHASE 1: TRIAGE (do this first, then STOP and show me the table)
For each of the eight books write planning/gem_books/<book>_triage.md with one row per book chapter:

| Book chapter | Relevant to me? (YES / PARTLY / SKIP) | One-line reason | Where it belongs (handbook chapter number, or "deferred to Part N: <topic>") | Already covered? (FULL / PARTIAL / NONE, with the handbook chapter and section that covers it) |

Rules for the triage:
- Decide relevance from my job profile above, not from how interesting the chapter is.
- "Already covered" must be checked by reading the handbook text, not by keyword matching. Open the handbook section and compare it with the book chapter. PARTIAL means say what is missing in one line.
- A book chapter that belongs to a part that is not written yet (Parts 12 to 19) is not a gap. Mark it "deferred to Part N" so it is picked up when that part is written. Do not force it into an existing chapter.
- Skip index, preface, praise, colophon, appendices of solutions, and front matter.
- At the end of each triage file, add the totals: chapters YES / PARTLY / SKIP, and how many of the YES and PARTLY chapters are FULL, PARTIAL, NONE, or deferred.

My starting suggestion (you may disagree, but give a reason):
- how-linux-works: YES for devices, disks and filesystems, boot, user space start, system configuration (logging, time, batch jobs), processes and resource use, networking and network applications, file transfer, virtualization. Probably SKIP the desktop and printing chapter and basic shell-script intro unless Part 1 chapter 9 lacks something.
- supercomputers-for-linux-sysadmins: YES for what a supercomputer is, how to build and start one, hardware, InfiniBand, network file systems, remote management, schedulers (OpenPBS, Slurm), monitoring, compilers and parallel libraries, booting and node setup, cluster management (xCAT). SKIP the basic UNIX chapter if Part 1 already covers it.
- ai-systems-performance-engineering: Chapters 1 to 14 are already largely covered by Part 10. Chapters 15 to 20 (inference) belong to Part 15, so mark them "deferred to Part 15".
- ai-data-center-network-design-and-technologies: YES for design considerations, optics and cabling, load balancing, RoCEv2 and congestion, IP routing, storage networking, KPIs, monitoring, UEC, scale-up. Most belongs to Part 12 (not written): mark "deferred to Part 12" unless Part 2 or Part 9 should hold it now.
- learning-python-6th-edition: only what an infrastructure engineer needs: objects and dynamic typing, scopes, functions and arguments, comprehensions and generators, modules and packages, classes (basics, operator overloading, designing with classes), exceptions, Unicode and bytes, decorators. SKIP the interludes, platform tips, metaclasses unless Part 3 chapter 11 needs them. Target is Part 3.
- ai-factory: probably mostly SKIP. Mark YES only the chapters that matter for an AI platform engineer (for example the AI Factory roadmap and distributed computing chapters) and say why.
- production-kubernetes: YES for container runtime, storage, pod networking, service routing, secrets, admission control, observability, identity, platform services, multitenancy, autoscaling, supply chain. Target is Part 5 (and Part 11 where GPU-specific).
- kubernetes-up-and-running: YES for pods, services, ingress, deployments, jobs, config and secrets, storage, extending Kubernetes, securing and policy. SKIP what Part 5 already explains well.

STOP after Phase 1. Show me the eight triage files and a one-screen summary. Wait for my corrections. Do not start Phase 2 before I approve.

WHAT IS DONE NOW AND WHAT WAITS (important)
Parts 12 to 19 are not written yet, so many book chapters will be covered by chapters that do not exist today. Therefore:
- NOW: Phase 1 triage for all eight books, and Phase 2 only for book chapters whose target is a handbook chapter in Parts 1 to 11 (Part 1 Linux, Part 2 networking, Part 3 Python, Part 5 Kubernetes, Part 6 HPC/Slurm, Parts 9 to 11 NVIDIA systems, GPU/CUDA, GPU Kubernetes).
- NOT NOW: every row marked "deferred to Part N". Do not write content for these into existing chapters. Instead collect them in planning/gem_books/DEFERRED.md with columns: book, book chapter, relevance (YES/PARTLY), the future part and topic it belongs to, and the one-line reason. This file is required input for whoever writes Part N (see planning/GEM_BOOKS_DEFERRED_RULE.md).
- LATER (Phase 3, after all parts are written): re-run the triage tables as a final audit. Every YES/PARTLY row that is not FULL then gets fixed. Do not start Phase 3 now.

PHASE 2: ADD THE MISSING CONTENT (only for rows I approved as YES or PARTLY, status PARTIAL or NONE, target in Parts 1 to 11, not deferred)
Work one book chapter at a time, in the order of the triage file.

A. Read the book chapter in full with bookch.py. Write a scratch list of its exact numbers, commands, tables, warnings and procedures as they appear.
B. Read the handbook section that is supposed to cover it. List what is missing.
C. Add the missing content to the handbook chapter named in the triage file:
   - Put it under an existing heading when it fits, otherwise a new "### " subsection in the right chapter.
   - If a book chapter needs more than about 1,500 words and fits no existing chapter, do not write a new chapter. Add a row to planning/gem_books/PROPOSED_NEW_CHAPTERS.md (book, chapter, why, suggested chapter title, suggested position) and move on. I decide.
   - Keep the handbook chapter's length reasonable. Do not delete or shorten existing content.
D. Record it in planning/gem_books/<book>_ledger.md: one row per book chapter with: handbook chapter and section, what was added (one line), the book passage length versus the words you added, the book_passages.py result, and the date. Update the triage row to FULL only when the acceptance check is clean.
E. Cite the book in that handbook chapter's "Sources and review notes" by its folder name and chapter title, and say what you read in full.


KEEP THE BOOK'S VOICE AND EXPLANATION (the most important rule of Phase 2)
The reader wants what the gem book actually teaches: the author's reasoning, examples, scripts, stories and the "why" behind each choice, in the same natural voice. A summary that keeps the topic names and drops the explanation is a failure, even if every heading is "covered". Rules:
1. Carry over the explanation, not only the conclusion. If the book spends three paragraphs on why something is done a certain way, the handbook spends about as many words on it. For explanatory passages aim for at least 70 percent of the book passage's length, in your own words, in the book's order and tone.
2. Keep the author's examples, analogies, history and small stories (for example, why a tool has the name it has), every script and command sequence the author builds up step by step (with the author's reason for each step), and the warnings and "do not forget" remarks.
3. Never replace a passage with a table. Write the passage first. Add a table afterwards only if comparison helps. A table row may not be the only place a book idea appears.
4. Keep the author's trade-off reasoning. "Pros and cons" lists become sentences that say why each pro or con happens.
5. Paraphrase closely; do not quote more than one short sentence (under 15 words) per source and do not copy paragraphs. Keep the author's numbers exactly. Mark the book's examples as examples.
6. Do not add facts that are not in the book chapter. Do not remove facts that are.

Worked example of what went wrong (supercomputers-for-linux-sysadmins, chapter 11, "Users - Accounting Management"). The book spends about 1,900 words on cluster accounts. It explains the classic approach with its pros and cons, then the design choice that makes it safe: copy the files from the destination node, not from the master, so a replaced or rebooted node updates itself at start-up; it gives the /usr/sbin/master-sync script and explains each line; it warns that mass user changes should trigger one manual sync, run in pools or at 0.1 to 0.5 second intervals, or with pdsh or clush, and gives the loop script with its timeout trap; it tells the history of NIS (Sun, 1985, called Yellow Pages until the trademark owner sued, hence the yp prefix), says NIS and NIS+ are not compatible, explains why NIS+ struggles beyond 30 to 40 clients, lists the three server daemons (ypserv, yppasswdd, ypxfrd), the firewall services to open, the NIS domain and what it is not, the Makefile and securenets file, and the client steps. The handbook version was a three-row table and two sentences, about 250 words. That is the failure to avoid. The correct version tells it as the book does, step by step, with the scripts and the reasons.

ACCEPTANCE CHECK FOR EVERY BOOK CHAPTER YOU ADD OR EXTEND
Run: python3 tools/book_passages.py <book> "<chapter number or title prefix>" <handbook chapter labels>
It lists the book paragraphs whose distinctive terms are not in the handbook chapter(s). For each listed paragraph either add its content (rules above) or write one line in the book ledger saying why it is skipped (author biography, repeated material, off-topic). Paste the final command output into the ledger. Claude will run the same command and read a sample of paragraphs side by side before accepting a book.

RULES (same as the chapter workflow, they are checked by tools/validate_chapter.py)
1. Every number, command, flag, path and table value must be copied exactly from the book chapter you read. If the book gives an example, say "in the book's example" and do not present it as a specification.
2. Do not add anything from memory. If a useful fact is not in the book chapter, leave it out. If you think it is important, list it in your report under "Suggested, not in the book".
3. If the book and the handbook (or another source) disagree, show both numbers, name each source, and do not pick one silently.
4. If the book marks its numbers as illustrative or an example, say so in the handbook text.
5. LANGUAGE: follow planning/LANGUAGE_RULE.md in full (book-style prose, plain words, at most two numbers per sentence, code formatting only for things you type or see on screen). The validator prints readability warnings; reduce them. Terms explained at first use. No exclamation marks, no hype. When you add book content to a chapter, write it in book style, not as a list of terms and numbers.
6. Mermaid boxes: at most 2 short lines each, under 130 characters. Put detail in a table under the diagram.
7. Commands you did not run are marked "(untested here)". Keep the chapter's "Run here" and "Not verified on live hardware" lists true.
8. Keep exactly 20 checkpoint questions per chapter. If you add content, replace the weakest question or change a question to test the new material. Update the answer.
9. Do not commit.

AFTER EACH BOOK
Run for every changed handbook chapter:
  python3 tools/validate_chapter.py P.C
  python3 tools/check_coverage.py P.C
then: python3 tools/lint_mdx.py ; node tools/check_mermaid.mjs | tail -1 ; npm run build 2>&1 | grep -E "SUCCESS|ERROR"
Reply with a short report per book: chapters added or extended (handbook chapter and section), chapters skipped and why, chapters deferred to later parts, items in PROPOSED_NEW_CHAPTERS.md, rows added to DEFERRED.md, and anything you were unsure about. Claude will validate the book against the real chapters when I ask.

If a decision is unclear, ask me one short question instead of guessing.
