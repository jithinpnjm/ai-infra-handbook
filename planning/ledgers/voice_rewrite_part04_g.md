# Voice rewrite, Part 4, batch G (chapters 01-03)

Scope: docs/part-04-automation chapters 01, 02, 03 only. Full warm-teacher expansion, section by section. Facts, numbers, commands, code, Mermaid, tables, headings, front matter, checkpoint questions and Sources left unchanged.

## Gate results (run after each chapter, no commit)

| Chapter | Words (HEAD -> worktree) | Growth | rewrite_guard | chain_gate |
|---|---|---|---|---|
| 01-git-from-scratch-for-infrastructure-engineers.md | 9549 -> 14814 | +55% | ok, new numbers 0, lost numbers 0 | 0.0 per 1000 words |
| 02-ci-cd-pipelines-concepts-and-design.md | 9829 -> 14042 | +43% | ok, new numbers 0, lost numbers 0 | 0.0 per 1000 words |
| 03-ansible-from-zero-what-it-is-how-it-works-installation-and-ad-hoc-comm.md | 8440 -> 11887 | +41% | ok, new numbers 0, lost numbers 0 | 0.0 per 1000 words |

Guard notes: chapter 01 shows "new code spans 26, lost 13" (inline backtick spans in rewritten exercises and prose); guard reports no hard failures. Chapter 02 shows "new code spans 10, lost 7". Chapter 03 shows "new code spans 20, lost 4". Each was reviewed as prose-only span changes, not code block changes. Code blocks, front matter and checkpoint counts are unchanged.

## What changed, per chapter

- Every section gained a lived situation or worked walk-through, a plain "why" and a step-by-step "what happens" where the source gave only reference text. Terms are defined at first use (MTU, SLO, SBOM, BMC, OIDC claim, digest, canary, soak period, DORA, egress filtering, forks, round trip, and similar).
- Exercises rewritten in all three chapters: one situation per exercise, one question per sentence, no (a)/(b) nesting. Exercise count kept at six per chapter. Commands and names kept.
- Checkpoint questions and answers unchanged (form and count kept). Sources and review notes unchanged.
- Status rows keep the single "untested" marker. No "untested here" text anywhere. No exclamation marks added.

## Items for the owner

- Growth exceeds the +25-40% target in chapter 01 (+55%). Not trimmed, per the never-trim rule. Owner may decide whether to accept the length.
- Chapter 02 sits at +43%, slightly above the band.
- Chapter 03 sits at +41%, slightly above the band.
- Checkpoint answers were not expanded. If the target requires answer-side growth, that is a separate pass.
- No new facts added. Where a claim was an explanatory generalization (for example, why a sudoers mismatch can point at the module), it was softened to "can" wording.
- Nothing committed. Trading-bot repo untouched.
