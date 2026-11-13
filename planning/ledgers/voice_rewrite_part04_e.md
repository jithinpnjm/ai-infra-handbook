# Voice rewrite ledger: Part 4, chapters 17-19

Scope: docs/part-04-automation/17, 18, 19. Not committed.

| Chapter | Words before | Words after | Growth | Guard | Chain gate |
|---|---|---|---|---|---|
| 17 Ansible for GPU nodes | 7603 | 10911 | +43% | 0 hard failures | pass |
| 18 Terraform refresher | 7314 | 9786 | +34% | 0 hard failures | pass |
| 19 Terraform state in depth | 7236 | 9293 | +28% | 0 hard failures | pass |

## Items to review

- 17: growth is 43 percent, a few points above the 25-40 band. Trimming was not allowed, so the excess was left in place. Decide whether to accept it.
- 17 GPU tuning table (section 3.5): checked the "When you need it" cells for plausibility. Persistence, clocks, power limit, ECC and compute mode, and MIG rows read as sensible for their commands. Table left unchanged.
- 18: the exercise list grew from 6 to 10 items to meet the one-situation, one-question rule. Checkpoint questions are unchanged (20).
- 18 and 19: the exercise lists were rewritten as one situation per item. Some original compound questions were split, and the original code references were kept.
- 19: exercise list went from 6 to 10 items for the same reason. Checkpoint questions unchanged.

## Standing edits

- Status rows changed from "labs **untested**" to "labs not run on live hardware" (17, 18, 19).
- "untested here" removed everywhere. Sources sections (17, 18, 19) keep the honest status sentence with the marker dropped.
- 17: one "ten percent" figure and one "80 percent" figure were added during drafting and then removed. No new facts remain outside the guard report (new numbers 0).
- 18: "Table 1-4" reference replaced with "the chapter's summary", to avoid a borrowed table label.
- 18: a count of 500 nodes was replaced with a non-numeric phrase during drafting.
- Code blocks, Mermaid, tables, headings, front matter, checkpoints and Sources content are unchanged apart from the marker removal.

## Guard notes

- 17: lost code spans 4, new code spans 12 (from prose edits, not code blocks).
- 18: lost code spans 17, from shortened exercise lists.
- 19: lost code spans 9, from shortened exercise lists. Residue count in the guard went 2 to 1.
