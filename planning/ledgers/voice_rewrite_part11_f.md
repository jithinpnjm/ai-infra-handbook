# Voice rewrite, Part 11 batch F (chapters 11.16, 11.17, 11.18)

Scope: `docs/part-11-gpu-kubernetes/16-kai-gang-scheduling-and-topology-aware-placement.md`, `17-kai-gpu-sharing-and-fractions.md`, `18-kai-operations-and-troubleshooting.md`. Nothing committed. `EXTERNAL_EDITS.md` not edited (per owner instruction). Other chapters untouched.

Method: body (from "## Why this matters" to "## Checkpoint questions") rewritten section by section. Code fences, data tables, Mermaid blocks, front matter, title and metadata table, checkpoint questions and answers, and "Sources and review notes" are carried over byte-for-byte from HEAD. Prose and exercises are new.

## Word counts (`wc -w` on the whole file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 11.16 KAI gang scheduling and topology-aware placement | 8015 | 10137 | +26.5% |
| 11.17 KAI GPU sharing and fractions | 7914 | 9993 | +26.3% |
| 11.18 KAI operations and troubleshooting | 8257 | 10409 | +26.1% |

## Gates (run, output seen)

- Inline code span check (repo-relative, prose only): `{}` for all three files.
- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures for all three.
  - 11.16: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 11.17: new numbers 2 (`100,000` and `50,000`), lost numbers 0, new code spans 0, lost 0. Both figures already appear in the unchanged worked-example block (`50,000 MiB each (100,000 MiB > 81,920 MiB)`). They are restated in one prose sentence, not new facts.
  - 11.18: new numbers 1 (`11.15`), lost 0, new code spans 0, lost 0. This is the cross-reference added for the Queue-units sentence (see Fact fix below).
- `python3 tools/restore/chain_gate.py <file>`: 11.16 = 0.0, 11.17 = 0.1, 11.18 = 0.0 (all at or under the 0.2 target).
- `node tools/check_mermaid.mjs`: checked 776 diagrams, 0 failed (repo-wide run; includes the three chapters).
- `npm run build`: not run (owner instruction for this batch: "No npm build").

## Fact fix: KAI Queue units

- 11.18, "Mapping Layer 4 and Layer 5 failures" section: added one paragraph stating Queue quota units as in 11.15 (`code/part11` note in 11.15: "Queue units: gpu in devices, cpu in millicores, memory in MB"). The paragraph says GPUs count as whole devices, CPU in millicores, memory in MB, and cross-references Chapter 11.15.
- 11.16 and 11.17 contain no Queue quota unit statements; nothing to change there.

## Residue and style checks (body only)

- "(tested here)" removed from Step 1 headings in all three chapters.
- "(untested here)" removed from body prose. It survives only inside the locked "Sources and review notes" tail (not editable under the rules).
- One honest status sentence per chapter, in "Venue and scope": the commands were not run on live hardware (11.16, 11.17, 11.18).
- No "you will be able", no outcome checklists (Outcomes sections rewritten as one plain paragraph under the locked "### Outcomes" heading), no "Volume N", "the book says", raw `<` or `{` in prose, or exclamation marks.
- Exercises: six per chapter, same counts. Multi-part exercises split into one-question sentences. Commands, function names and numbers kept.
- Gem books named only where the original attributed (Generative AI on Kubernetes Ch. 7; AI Systems Performance Engineering Ch. 19 in 11.16). No attribution added.

## Needs source (general explanations added in prose; no new project facts)

These sentences explain a term or give advice. They are not claims from a cited source. A reviewer should confirm them or cut them.

- 11.16: definitions of gang, rendezvous barrier, topology, NUMA island, collective, RDMA, sysfs, FLOP, transformer layer, CapEx and OpEx, binary-tree hop cost.
- 11.16: the "start with preferred constraints, then promote" habit, and the "threshold too tight or too loose" remark in the drift section (advice, not measured).
- 11.16: the "Friday firmware update, Monday slow job" walk-through is labelled as a typical example, not a reported incident.
- 11.17: a card at "a few percent utilization for a whole month" (illustration only, no figure given).
- 11.17: annotation values are quoted strings and the scheduler converts them (advice on quoting).
- 11.17: MIG profile IDs can differ between driver and GPU families, so copy them from the host list (advice; check against NVIDIA MIG docs before publishing).
- 11.17: a pending KAI Pod reports its reason in scheduler events rather than as a broken container (matches the 11.18 description of `FailedScheduling`/Queue events; confirm against the KAI version in use).
- 11.18: definitions of CRD, PromQL, SLI, SLO, Game Day, tabletop exercise, key-value cache, leader election, swap, and label cardinality.
- 11.18: "lower layers hold facts that disappear fastest" (follows the chapter's own statement that restarts wipe logs and driver state).

## Unresolved

- The locked tails (Checkpoint questions and Sources and review notes) are unchanged. They still contain older phrasing such as "(untested here)" and "Volume" references. Per the rules they were not edited.
- Exercise and checkpoint answer text in the tails still uses the older wording; no checkpoint content was altered.
- `npm run build` not run (owner instruction).
- Growth is +26.1% to +26.5%. This clears the +25% floor but sits below the +30% aim. Further growth would need prose beyond what the source material supports; the next pass could add worked examples only if the owner wants more length.
