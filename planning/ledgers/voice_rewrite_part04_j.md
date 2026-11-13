# Voice rewrite ledger: Part 4 chapters 10-13 (pass j)

Scope: docs/part-04-automation/10 to 13. Full warm-teacher deepening, section by section. No commits.

## Results (rewrite_guard, HEAD to worktree, words)

| Chapter | Before | After | Change | Guard |
|---|---|---|---|---|
| 10 Debugging Ansible playbooks | 6609 | 11027 | +67% | ok, residue 0, new numbers 0 |
| 11 Ansible roles and collections | 5489 | 8401 | +53% | ok, residue 0, new numbers 0 (one "540" example removed) |
| 12 Ansible Vault and secrets management | 6427 | 8877 | +38% | ok, residue 0, new numbers 0 |
| 13 Testing Ansible | 6356 | 8755 | +38% | ok, residue 0, new numbers 0 |

chain_gate passed for all four chapters.

## Open items for owner

- Ch 10 and ch 11 overshoot the +25-40% band. The content was never trimmed, so the owner decides whether to accept or restage. Ch 12 and 13 sit in band.
- Ch 11 lost 16 inline code spans, mostly where the lab and exercise lists were rewritten as situations. Commands are kept; some decorative spans became plain words. Review if span fidelity matters.
- Checkpoint questions were left in their original form and count (not deepened).
- Sources and review notes were left unchanged.
- Status rows still say "labs **untested**" once per chapter (kept as honest status).

## Standing rules applied

- Exercises rewritten as one situation plus one question per sentence, no (a)/(b) nesting.
- Removed borrowed labels: "(Examples 14-4 and 14-5)" in ch 13, "the book" wording in ch 13.
- "untested here" absent from all four chapters.
- No exclamation marks in prose; code spans kept for commands and names.
- No new numbers added in any chapter (guard reports 0 new numbers except one removed example).
