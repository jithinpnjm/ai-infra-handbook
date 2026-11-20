# Brief for chapter-mapping agents (read-only on docs; write only into planning/nebius_plan/map/)

Goal: for each assigned chapter, read the WHOLE chapter in chunks (Read with offset/limit ~400 lines; never skim, never grep-only) and write a section-level map used to build a personal interview study plan.

Reader profile: BEGINNER in Linux and networking (never did a Linux troubleshooting task), needs a REFRESH of Python and Kubernetes, never did a system-design interview. Interview: Senior SRE, Nebius Token Factory (GPU inference platform). Rounds: (R1) Linux, networking, Python scripting + practical Linux console/troubleshooting; (R2) scripting/DevOps/Kubernetes troubleshooting; (R3) system design (distributed system, capacity estimation, availability); (R4) 90-minute deep dive on own project + team lead. Interview date 9 Dec 2026; study starts 25 Nov.

Output: one file per chapter: planning/nebius_plan/map/<volume>-<chapter>.md, for example `01-05.md` for chapter 1.5 (use two-digit volume, two-digit chapter). Write each file right after reading that chapter. Format exactly:

```
# <chapter number and title>
Words: <approx> | Read time: <minutes> | File: <docs path>
One-line purpose: ...
Beginner friendly: yes/partly/no (and the chapter that should come first, if not)
Nebius rounds served: R1/R2/R3/R4 (list)
Chapter verdict: MUST-READ-FULL / READ-SECTIONS (list them) / SKIM-FOR-RECALL / SKIP, with one-sentence reason

| # | Section heading (exact text, include subsections when they matter) | What it teaches (one plain sentence, from the text) | Level (basic/intermediate/advanced) | Interview use (what question or task it prepares for) | Priority (MUST/SHOULD/OPTIONAL/SKIP) | Min |
```
Rules: list every ## section and every ### subsection that carries a distinct skill (merge tiny ones). Minutes = words in that section / 150 (reading with notes). Priority is for THIS reader and interview, not for the book in general: MUST = likely asked or needed to understand a MUST; SHOULD = strengthens answers; OPTIONAL = nice to have; SKIP = off-target (e.g. HPC, InfiniBand, Redfish, vendor marketing, advanced kernel internals). Be honest: if a section is dense/advanced for a beginner, say so in the Level column and name what to read before it. Add after the table: "Hands-on to do:" (2-4 concrete commands or exercises from the chapter's labs the reader should actually run) and "Likely interview questions from this chapter:" (3-6 real questions in the interviewer's voice).
Do not edit docs. Do not invent content that is not in the chapter. At the end reply in under 40 words: files written.
