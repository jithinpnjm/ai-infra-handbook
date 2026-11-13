# Rewrite spec: Part 19 chapters 19.2–19.15 (shared contract for rewrite agents)

Repo: `/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook` (work here).

## Read in this order before writing

1. Your current chapter: `docs/part-19-capstone/NN-<slug>.md` (keep the frontmatter `id`, `sidebar_*`; keep `status: "drafted"`).
2. **`docs/part-19-capstone/01-capstone-a-slurm-gpu-cluster.md` — the rewritten 19.1 is the gold standard for voice, structure, and depth. Match it.** Do not read or modify 19.1 further.
3. `planning/MASTER_REWRITE_PLAN.md` sections 1 and 3 (voice rules, template, acceptance checks).
4. Your mapped sources (listed in your task). Read the primary volume chapters in full; skim the handbook integration chapters you cross-reference.

## Voice and structure (non-negotiable)

- ~7,000–9,500 words. Depth over compression.
- Every numbered `##` section opens with a short concrete production-failure or on-call story (2–4 sentences, plain language, no meta-chatter like "according to Chapter X").
- Every major section ends with a bold **Decision rule:** (one sentence) and a **In one minute:** summary (2–4 sentences).
- One idea per paragraph, 3–5 sentences per paragraph, ~15–20 word average sentence, at most 2 numbers per sentence, no parentheses inside explanatory sentences.
- **No ` ```text ` blocks containing prose.** Commands/config in real fenced blocks with backticks.
- At least one readable mermaid diagram (node labels ≤ 130 chars, detail in a table underneath).
- Template sections, in order: frontmatter → metadata table → `## Why this matters for AI infrastructure` → `## Prerequisites and outcomes` → numbered `## N.` teaching sections → `## N+1. Hands-on lab` (steps + "What to record" + explicit **untested** note) → `## Exercises` (6, each with a real solution sketch) → `## Checkpoint questions (20)` (exactly 20 `<details><summary>` items) → `## Sources and review notes` (sources cited by book name + chapter; `### Cross-references to other handbook chapters`; `### Migrated from `nvidia-devops`` listing the exact file paths; `### Explicitly labelled inferences`; `### Not verified on live hardware`).
- No exclamation marks in prose.
- "Run here": the shared lab is `code/part19/capstone_lab.py` (structural checks); mention the lowercase word `capstone` in the body so the lab matcher finds the chapter.

## Accuracy bar (the author's 19.1 review rejected the first rewrite for these — do not repeat any of them)

1. **Man-page placement**: every config parameter must appear in the file where the actual documentation puts it (e.g. Slurm cgroup-containment parameters live in `cgroup.conf`, not `slurm.conf`). When you write a config file, verify each parameter against the mapped source or the mirrored official docs under `/Users/jithinpjoseph/Documents/GitHub/nvidia-devops/tools/nvidia-ingest/data/md/`.
2. **Config completeness**: never write a parameter that does nothing without its sibling (e.g. `JobAcctGatherFrequency` needs `JobAcctGatherType`). If a setting is optional, say so.
3. **Internal consistency**: node names, counts, partitions, GPU models, and versions must agree between the topology diagram, the config blocks, the prose, and the lab steps. Re-read the whole chapter for this before finishing.
4. **No shaky claims**: if you cannot find a parameter/fact in your sources, do not write it; either source it or label it an explicit inference.
5. **No self-contradictions in stories** (e.g. nodes "idle" while dashboards "saturated" in the same scene).
6. Secrets in config examples: mark ownership/permissions (e.g. "mode 600, owned by root or SlurmUser") and never invent fake passwords that look real.

## Lab contract (enforced by `code/part19/capstone_lab.py`)

- `status` frontmatter drafted; exactly 20 `<summary>`; `## Exercises`; `## Sources and review notes`; the word `untested` or `not verified`; one mermaid (or ≥5 table rows); mermaid nodes ≤ 130 chars; no `!` in prose; the string `nvidia-devops` appears in the chapter.

## Artifacts you must update (all in this repo)

1. `planning/ledgers/19-NN.md` — real ledger: §1 source inventory (files actually read), §2 corpus search (run `python3 tools/check_coverage.py 19.NN`; record every "UNRECORDED" book with a one-line "read, nothing new" or "cited" decision), §3 number-by-number provenance table (every number in the chapter → source, or "inference — labelled in chapter"), §4 source contradictions found and how resolved, §5 not-verified-on-live-hardware list.
2. `planning/coverage/chapters/19-NN.md` — if the chapter's `structure.txt` row cites a gem-book code with chapter numbers (e.g. `EAS 12`), run `python3 tools/coverage/chapter_cov.py 19.NN` and resolve every CHECK row (covered / moved <chapter> / skipped <reason> / gap-doc) until "0 need a decision". If there is no gem-book code in the sources field, the file stays a minimal header with 0 rows — that is fine.
3. The `19.NN` row in `planning/structure.txt` — fix the sources column if it is wrong or too thin (keep the line format `NN | Title | X | sources | N | 1`). Use codes: gem-book codes as in other rows (see `tools/coverage/map_sources.py` CODES), and `VNN`/`VLN` for nvidia-devops ZTH/legacy volumes with chapter numbers.
4. If you change a nvidia-devops file's home chapter in `planning/MIGRATION_MAP.md` (wrong row for your chapter), fix only that row.

## Acceptance checks (run before reporting; repeat until clean)

```
python3 tools/validate_chapter.py 19.NN      # 12/12 PASS and zero WARN lines in readability
python3 tools/check_provenance.py 19.NN      # "NOT FOUND ANYWHERE CITED: 0" (numbers in stories that are labelled inferences are OK if the ledger justifies them)
node tools/check_mermaid.mjs part-19-capstone  # 0 failed
python3 tools/check_coverage.py 19.NN        # VERDICT: OK (record any uncited mapped files in the ledger)
```

**Parallel-work note:** `capstone_lab.py` checks all 15 Part 19 chapters, and sibling chapters are being rewritten concurrently. If the only failure is in a chapter that is NOT yours (e.g. `19.7 has 0 checkpoint questions`), that is transient — note it in your report and move on. Do not "fix" other chapters.

## Hard rules

- Do NOT `git commit` (the coordinator commits).
- Do NOT touch `docs/part-19-capstone/01-*`, `planning/ledgers/19-01.md`, `planning/coverage/chapters/19-01.md`, or `planning/STATUS.md` (another agent owns 19.1).
- Do NOT touch sibling 19.x chapter files or their ledgers/coverage rows (other agents own them).
- Do NOT rewrite `code/part19/capstone_lab.py`.

## Report back (concise)

Word count; primary sources used; number of numeric facts checked and any NOT FOUND items; the structure.txt row before/after; acceptance-check results; anything you could not source (so the coordinator can label it).
