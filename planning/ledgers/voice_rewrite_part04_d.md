# Voice rewrite, Part 4 chapters 22-27 (batch d)

Scope: docs/part-04-automation/22 to 27 only. Fixed content kept: front matter, status rows, headings, code blocks, Mermaid, tables, checkpoint count and form, Sources (marker text changed only). No commit.

## Gate results (rewrite_guard HEAD WORKTREE, chain_gate)

| Chapter | Words before | Words after | Growth | Guard hard failures | Chain gate |
|---|---|---|---|---|---|
| 22 terraform secrets and providers | 6566 | 9003 | +37% | 0 | 0.0 |
| 23 production-grade terraform | 7451 | 10098 | +35% | 0 | 0.0 |
| 24 terraform GCP and Nebius | 6420 | 8890 | +38% | 0 | 0.0 |
| 25 terraform k8s, helm, OpenTofu | 6032 | 7884 | +31% | 0 | 0.0 |
| 26 GitOps Argo CD and Flux | 9382 | 11744 | +25% | 0 | 0.1 |
| 27 lab GPU cluster | 5518 | 7235 | +31% | 0 | 0.0 |

Guard soft notes: "new code spans" and "lost code spans" are non-zero in some chapters because prose backtick spans were added or reflowed. Not hard failures. Chapter 24 flagged three new numbers (0.1, 07, 9000) during the first pass; all were removed, and the rerun shows 0 new numbers.

## Honesty marker

- "untested here" removed from prose in chapters 22, 24, 25, 26 and 27 (lab lead-ins), and from the Sources notes in all six. Each lab now says once, above the lab, that the commands have not been run on live hardware. Status rows keep the word "untested" as before.
- No code comments carried the marker in these six files.

## Exercises

Restated as one situation and one question per sentence. No (a)/(b) nesting remains in the six files. Exercise counts unchanged (22: 6, 23: 6, 24: 6, 25: 6, 26: 6, 27: 6).

## Open items

- Chapter 26 Section 2 "Two status fields": one added paragraph is explanatory only.
- Chapters 22 to 27 still contain some sentences that pack two related facts with semicolons; left as-is because they are fixed facts.
- Text "Table 6-1" and "Table 8-2" references remain inside Sources and checkpoint text only (fixed content).
- Not run: `node tools/check_mermaid.mjs`, `npm run build`, `python3 tools/language_audit.py`. The batch instructions named only guard and chain_gate per chapter.
