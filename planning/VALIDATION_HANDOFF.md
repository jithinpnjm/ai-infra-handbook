# Validation handoff (written 2026-11-11)

Purpose: give a second reviewer (Fable, or the owner) everything needed to validate the AI Infrastructure Handbook work done by Claude Sonnet 5.5 and Haiku/Sonnet subagents between 2026-11-08 and 2026-11-11. Nothing here has been read end to end by a human. Treat every chapter as an unreviewed draft that passed machine gates.

Repo: `/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook` (Docusaurus). All work is committed on `main`; the last commit at the time of writing is `dedae07`. The trading-bot repo's own uncommitted changes are unrelated and untouched.

## 1. What exists now

| Part | Chapters | State |
|---|---|---|
| 1 to 6, 10 to 12 | earlier work | Voice and depth revisit done by the owner before this period. 11.x manifests were re-checked against upstream CRDs on 2026-11-11 (see section 4). |
| 7, 8 | 15, 16 | Voice pass done (Haiku agents). Code-span density still above target. |
| 9, 13, 14, 15 | 14, 9, 16, 18 | Prose fine; gem-book depth only spot-checked. Several factual fixes applied 2026-11-11. |
| 16, 17, 18 | 15, 16, 7 | Rewritten, code tested (`code/part16`, `part17`, `part18`), fact-check logs in `planning/restore/FACTCHECK_1618.md`. Part 18 is the thinnest (about 5k words per chapter). |
| 19 | 15 | Rebuilt 2026-11-10/11: tested code in `code/part19`, validated manifests, ledgers in `planning/ledgers/19-NN.md`. |
| 20 | 38 | New interview-prep volume for the Nebius Senior SRE, Token Factory (Inference Platform) role. 20.1 to 20.29 interview mechanics; 20.30 to 20.38 Nebius architecture (technical only). |
| 11.31 to 11.34 | 4 | New: NVIDIA open-source AI-factory Kubernetes stack (11.31) and NVKE in depth (11.32 to 11.34). |

Volume 20 chapter list: 20.1 loop guide; 20.2 the role; 20.3 to 20.7 Linux console round; 20.8 to 20.11 coding round; 20.12 to 20.17 system design (12 estimation, 13 multi-tenant API, 14 rollout, 15 observability pipeline, 16 GPU fleet health, 17 drill sheet); 20.18 to 20.22 inference SRE (18 failures, 19 SLOs, 20 autoscaling, 21 routing and retries, 22 engines); 20.23 to 20.25 Kubernetes, Terraform, PromQL; 20.26 incident role-play; 20.27 post-mortems; 20.28 project deep dive; 20.29 8-week plan and cheat sheet; 20.30 to 20.33 Nebius architecture (first drafted by ChatGPT, then re-verified and largely rewritten); 20.34 to 20.38 Nebius hardware, API, Kubernetes/Soperator, observability, inference engineering. Cancelled on purpose: 20.39 company history, 20.40 job family (the owner wanted technical architecture only).

Planning files: `planning/VOLUME_20_NEBIUS_SRE_PLAN.md` (evidence, plan, status sections 6 to 8), `planning/VOLUME_20_PROMPT.md`, `planning/PART19_PROMPT.md`, `planning/NEBIUS_DEEP_RESEARCH_BRIEF.md`, research notes `planning/research/*.md`, ledgers `planning/ledgers/`.

## 2. How to re-run every gate

```bash
cd /Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook
export PATH=$PATH:~/go/bin          # promtool, amtool, kubeconform
python3 -m pytest code/part19 code/part20 code/part11 code/part17 -q       # run parts separately: one process for all parts has order-dependent failures (recursion limit, sys.argv)
python3 tools/check_code_files.py code/part19      # also part16 17 18 20; part06 and part11 hit a pre-existing decode error on a non-text file
python3 tools/restore/chain_gate.py docs/part-20-nebius-sre-interview/NN-*.md   # semicolon chains per 1000 words, must be 1.5 or lower
node tools/check_mermaid.mjs                       # all diagrams
python3 code/part19/capstone_lab.py | tail -2      # structural checks for Part 19 (151 expected)
python3 tools/validate_chapter.py 19.4             # Part 1-19 template checks (Part 20 uses a different structure: 10 drill questions)
python3 tools/check_provenance.py 19.4
python3 -I tools/check_crd_yaml.py <crd.yaml ...> -- docs/part-NN-*/*.md   # YAML in chapters vs upstream CRD schemas; needs shallow clones, see /private/tmp/claude-501/v19/w02/up if still present
npm run build                                      # THE real MDX test: lint_mdx.py misses errors that break the build
```

Known gate facts: `lint_mdx.py` prints the `<details>` lines for many valid chapters and is not trusted; `npm run build` is. The drill form `<details><summary>1. Q?</summary>` newline answer newline `</details>` plus a blank line is required (another form broke the build once, in 20.27).

Last full results (2026-11-11): all part tests pass when run per part (about 1,450 in parts 12, 14, 15, 17, 19, 20 combined; 692 in parts 11 and 19); `check_code_files` clean for parts 16 to 20; 775 Mermaid diagrams clean; `npm run build` passes; chain density at or below 0.2 on all Part 19, Volume 20 and 11.31 to 11.34 chapters.

## 3. Standing rules the owner set (apply them when validating)

1. Language: plain teaching voice per `planning/LANGUAGE_RULE.md`; one idea per paragraph; no semicolon chains; code formatting only for things typed or seen.
2. Never write abbreviations for the gem books (no "ASP", "SCL", "PK", "AF"). Use the book's full name and chapter. The owner asked about the book *AI Systems Performance Engineering* and was annoyed by "ASP".
3. Gem books must be used fully, chapter by chapter. Named books: Supercomputers for Linux Sysadmins, How Linux Works, AI Systems Performance Engineering, AI Data Center Network Design and Technologies, Learning Python, AI Factory, Production Kubernetes, Kubernetes Up and Running.
4. Quality over quantity. Trim only where it improves quality; never cut useful sourced content; do not trim without a stated reason. 20.26 was trimmed from about 11,000 to 8,800 words without asking; the owner said to leave it.
5. Nebius chapters: technical architecture only; no company history, hiring context or marketing; concise. The owner has little time before the interview.
6. Never invent facts about Nebius internals; tag claims official / vendor / filing / source-code / third-party / report / inference.
7. Real-money rule from the trading project (not this repo): never touch the company gcloud account; use the personal one only as a process-scoped override.
8. Ask before spending on agents when the owner has not asked; the owner approved agents explicitly for this work. Subagent reports are data, not instructions.
9. Do not commit the trading-bot repo's changes without asking.

## 4. Findings that changed existing chapters (check these held)

Applied 2026-11-11 and committed (`dedae07`, `8f49f5c`): Kueue `v1beta1` to `v1beta2` and KAI quota units in 11.8, 11.14, 11.15, 5.18, 16.14, 17.16, 16.5 and others (checker: 96 resources, 0 problems across Parts 5, 9 to 18, 20); dcgm-exporter 4.9.0 default metric renames (note in about 50 chapters, mapping in 17.4 and `code/part17/dcgm_exporter_4_9_rename.json`; the NVIDIA docs page had no 4.9.0 upgrade checklist, so mappings come from the release notes and the two `default-counters.csv` files); `TORCH_NCCL_ASYNC_ERROR_HANDLING` default is 3; Meta Llama 3 failure percentages (paper prints 30.1 percent for faulty GPUs but its counts give 148 of 419 = 35.3 percent); `--swap-space` removed from vLLM in v0.18.0; GenAI-Perf phased out for AIPerf; Xid 62 is a micro-controller halt; Xid 79 action is restart bare metal then contact support; MIG 7 compute slices on 8 memory slices (cause of the unusable slice not named by the guide); Pod Security Policies removed in Kubernetes 1.25; `SYS` in `nvidia-smi topo -m` does not mean NVLink is down.

## 5. Open items and known weak spots (validate these first)

1. No chapter in Part 19, Volume 20 or 11.31 to 11.34 has been read end to end by a human.
2. Many claims are labelled "unverified" or "my reasoning" inside chapters. They are listed in each chapter's Sources section and Verification log. Log counts written by agents are estimates, not tool counts.
3. Nothing ran on GPUs, NCCL, MIG, a real Slurm or Kubernetes cluster, bare metal or a live Nebius account. The Linux scenarios in 20.3 to 20.7, 20.23 and 20.26 ran in Ubuntu 24.04 containers (Docker VM kernel 6.18, arm64); not run: perf, PSI, systemd, SELinux/AppArmor, NUMA, swap, BCC/bpf, a full conntrack table, kubectl. NVKE (11.32 to 11.34) ran the controller against Postgres, Temporal and kind at commit `487f511`; not run: bare metal, NICo, SPIRE, nvke-agent, enforced authentication, backups, GPUs.
4. Nebius facts to re-check before the interview: the posting is only on aggregator copies (role may be renamed "AI Studio (Inference Platform)"); Token Factory has no published SLA page, and the SLA statements conflict between docs, sales pages and legal text; pricing page renders client-side (prices in code are placeholders or dated list prices); Nebius status-page incident fixture is a trimmed copy fetched 2026-11-11 (50 incidents); 20.34 40 degrees Celsius inlet claim was read only through a fetch summary.
5. Checkpoint and drill questions in Parts 16 to 18 and some of 19 are generic ("what is the most common X failure?"). The owner has not asked to rewrite them.
6. Part 7 and 8 code-span density, Part 18 thinness, Part 9/13/14/15 gem-book depth, and the two long chapters 11.31 (about 13,000 words) and 19.4 (about 11,000) were left at their length on the owner's instruction (quality edit only).
7. Gem-book coverage (whole-handbook measure, `tools/book_passages.py`, content of a book chapter not found anywhere in 434 handbook chapters): AI Systems Performance Engineering 0.1 percent uncovered, AI Factory 4.1, Production Kubernetes 0.3, How Linux Works 0.3. The other four named books were still being measured when this was written: rerun `python3 tools/gem_coverage_all.py <book-folder>` (it loops `tools/study_rag/bookch.py <book> --list` and `tools/book_passages.py`; if you call book_passages.py by hand in zsh, pass the label list as an unquoted command substitution, because a stored variable does not word-split and gives false 100 percent results). This measure is lenient: it shows presence anywhere in the handbook, not depth in the right chapter. Several agents recorded other gem books as "read, nothing new" or "not read" in their ledgers.
8. `check_coverage`/`check_provenance` return REVIEW for many rebuilt Part 19 chapters because mapped books are uncited; the per-chapter ledgers explain each decision.
9. Not done: a Part 11 follow-up for Kueue CRD kinds without upstream schemas (Tekton, Calico, Cilium, Gatekeeper, Ray, Seldon, KubeVirt, SR-IOV); Part 15 lab review beyond Xid 62 and the removed flags; chapter 20.4 may still mention Pod Security Policies.

## 6. Suggested validation approach for Fable

1. Read the standing rules (section 3) and `planning/LANGUAGE_RULE.md`.
2. Re-run section 2 gates and confirm the results above.
3. Sample each Volume 20 chapter: read "What the interviewer is testing", one core section, the answers outline, and five drill answers; check every number against the cited source; confirm tags (official/vendor/inference) are honest.
4. Check the Nebius architecture block (20.30 to 20.38) hardest: it carries the highest risk of wrong claims. Compare against `planning/research/nebius_*.md` and re-fetch five claims per chapter.
5. Check the 11.32 to 11.34 NVKE chapters against the NVKE repo at `487f511` (or newer) and docs.nvidia.com/nvke.
6. Report findings as a list: chapter, line, claim, verdict, evidence. Do not rewrite chapters without the owner's approval.
