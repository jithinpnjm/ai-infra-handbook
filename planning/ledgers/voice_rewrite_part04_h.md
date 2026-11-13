# Voice rewrite part 04, batch h (chapters 04, 05, 06)

Scope: deepen the warm-teacher voice in `docs/part-04-automation/04-*`, `05-*`, `06-*`. Target +25-40 percent over the text as it stood before this pass. Not committed.

## Gate results (run after the last edit to each file)

| Chapter | Guard words (HEAD base to worktree) | New numbers | Hard failures | Chain gate | Checkpoints | `untested here` |
|---|---|---|---|---|---|---|
| 04 yaml-and-jinja2 | 7882 to 11228 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |
| 05 inventory | 6402 to 9490 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |
| 06 playbooks | 6994 to 10046 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |

Growth against the pre-pass worktree (measured by hand from the guard's pre-edit baseline): roughly +30 to +40 percent for 06 (7600 to 10046). The HEAD baseline for 04 and 05 is not the pre-pass worktree, so their percentages are estimates.

## What changed

- Each chapter opens its expanded sections with a lived situation (a Friday change, a re-cabled rack, a 2 AM partial failure, a firmware flash).
- Worked walkthroughs of the existing examples (YAML tree, anchor merge, Jinja loop, `group_by` and `add_host` play, vagrant.py, sinfo script, serial batches, the canary play).
- Terms defined at first use (shebang, loop, declarative, golden file, golden-file test, dict2items, pipefail, async).
- Announcements of learning goals removed: 06 "Below you will see..." and "Read this section as..."; 04 and 05 openers kept as headings only.
- 05 section 2: a blank line was added before the pattern table so it renders as a table (was glued to the paragraph above).
- 04 "Walk through" duplicate paragraph on templates merged into a single sentence set.
- Exercises rewritten in all three chapters: one situation, one question per sentence, no (a)(b) nesting. Each keeps the function, file or module names it referenced.

## Items to check

- Needs source (explanatory, not in the chapter's Sources): Makefile recipe lines need a real tab (04, section 3 whitespace paragraph); `add_host` records the host in memory without connecting (05, section 4); `yaml.safe_load` builds only plain dictionaries, lists, strings and numbers (04, section 1 "Never call yaml.load").
- 05, `rstrip("*")` removes the default-partition star that `sinfo` appends (explanation of existing code).
- 06, check mode lines about `skipped` counts in the recap are a reading tip, not a new claim about module behaviour; verify with a live run if the owner wants it stated as fact.
- Checkpoint answers were not expanded. The form and count are fixed, and the rules ask for 2-5 sentences only for parts 16-18.
- Code-span guard column shows lost spans against HEAD (04: 13, 05: 1, 06: 1). Most come from the pre-pass worktree, not this pass. Spans lost in this pass were restored in the exercises (for example `expand_inventory_range()`, `ansible.builtin.group_by`, `gcp_compute`, `diff: false`, `no_log: true`, `strategy: linear`).
- Not run in this pass (outside the scope set by the parent): `node tools/check_mermaid.mjs`, `npm run build`, `python3 tools/language_audit.py`, and the book-first study pass from RULES section 1 (only section 1 was read, as instructed).
- Not committed. Owner go-ahead needed per RULES section 2.6.
