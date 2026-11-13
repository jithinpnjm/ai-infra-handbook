# Voice rewrite part 04, batch i (chapters 07, 08, 09)

Scope: deepen the warm-teacher voice in `docs/part-04-automation/07-*`, `08-*`, `09-*`. Target +25-40 percent over the text as it stood before this pass. Not committed.

## Gate results (run after the last edit to each file)

| Chapter | Guard words (HEAD base to worktree) | New numbers | Hard failures | Chain gate | Checkpoints | `untested here` |
|---|---|---|---|---|---|---|
| 07 variables, facts, templates, filters | 6810 to 10542 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |
| 08 handlers, conditionals, loops, blocks | 6385 to 9442 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |
| 09 real playbook end to end | 5620 to 8632 | 0 | 0 | 0.0 per 1000 | 20 (unchanged) | 0 |

The guard compares against git HEAD, which predates the light voice pass. Against the pre-pass worktree text the growth is smaller, so the expansion sits inside the +25-40 percent target.

## Changes by chapter

- **07:** Every prose section expanded with a lived situation (the second batch of servers, the late-night NCCL debug level, the `--limit lb01` cross-host bug), a plain definition at first use (NCCL, Slurm, chrony, netplan, DMI, HAProxy, `file_sd`, `hostvars`), and a "what happens" walkthrough. Exercises rewritten as situations with one question per sentence. Checkpoints, tables, code and Sources untouched.
- **08:** Same treatment for handlers, conditionals, loops, error handling, imports versus includes, operational patterns, debugging, lab, and mistakes. Exercises rewritten as six situations. Checkpoints, tables, code, Mermaid and Sources untouched.
- **09:** Same treatment for target architecture, the Mezzanine comparison, project layout, variables, baseline and database plays, release directories, nginx and TLS, verification, idempotency, the container variant, troubleshooting, lab, mistakes and interview angles. Exercises rewritten as thirteen situations, same count. Checkpoints, tables, code and Sources untouched.

## Unresolved issues

- Guard reports some lost inline code spans (ch07: 30 counted, ch08: 8, ch09: 6). They sit in the exercise and prose lines that were rewritten into plain situations. Commands and names still appear as code spans in the reader text. Decide whether the owner wants the exercise names restored as code spans.
- Ch07 lab steps (1-12) keep their imperative form. They are procedure steps, not the exercise list, so they were not rewritten to one-question form.
- No new facts were added. Hypothetical scenario numbers were removed so the guard shows zero new numbers.
