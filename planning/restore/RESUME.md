# RESUME (written Fri Oct 30 23:46:10 CET 2026)

The session hit the token limit during the autonomous run. Resume with these steps.

## State
- Voice rewrite DONE (changed vs original): 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19, 1.20, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.30, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19, 2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 2.27, 2.28, 2.29, 2.30, 2.31, 2.32, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 4.14, 4.15, 4.16, 4.17, 4.18, 4.19, 4.20, 4.21, 4.22, 4.23, 4.24, 4.25, 4.26, 4.27, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13, 5.14, 5.15, 5.16, 5.17, 5.19
- Voice prepped but NOT done (rerun these; the agents may have been killed): 5.18, 5.20, 5.21, 5.22, 5.23, 5.24, 5.25, 5.26, 5.27, 5.28, 5.29, 5.30, 5.31, 5.32, 5.33, 5.34, 5.35, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 6.15, 6.16, 6.17, 6.18, 6.19, 6.20, 6.21, 6.22, 6.23, 6.24, 6.25, 6.26, 6.27, 6.28, 6.29, 6.30, 6.31
- Part 4 voice: prompts prepped for 4.1-4.27 (planning/restore/V4.N_prompt.md). Parts 5-15 not prepped: run `python3 tools/restore/prep_voice.py P.C ...`.
- Python restoration (new chapters 3.12-3.17), units per chapter in order (planning/restore/PY_GROUPS.json): {"12": ["U022", "U031", "U026", "U027", "U033", "U029"], "13": ["U028", "U024", "U025", "U037"], "14": ["U035", "U030", "U023", "U043", "U032"], "15": ["U040", "U039", "U041", "U038"], "16": ["U047", "U048", "U044", "U050", "U049"], "17": ["U042", "U054", "U036", "U051", "U056"]}.
  Done units: U022 U031 U026 (3.12), U028 U024 U025 (3.13), U035 U030 U023 (3.14), U040 U039 U041 (3.15), U047 U048 U044 (3.16), U042 U054 U036 (3.17). Running when stopped: U027 U029 (3.12), U043 (3.14), U038 (3.15), U051 (3.17). Left after those: 3.13 U037; 3.14 U032; 3.16 U050 U049; 3.17 U056; 3.12 U033.
- Other restoration queue: 114 units in QUEUE.json; ~35 non-Python units still open (ASP ch1-3,5,7,8; K8s Up&Running; Production K8s; Supercomputers; remaining at 15-30%). Waived: see planning/restore/WAIVERS.md.
- Open Python code fix: 3.15 had 8 blocks with lost indentation; a repair agent was launched. Re-check: `python3 tools/restore/pycheck.py docs/part-03-python/15-modules-and-packages-in-depth.md /tmp/empty.md` (touch /tmp/empty.md first).

## Tools
- tools/restore/prep_voice.py, voice_gate.py, batch_check.sh (verify voice chapters), prep_restore.py, gate.py (verify restoration units), sections.py, pycheck.py, mdx_guard.py, overlaps.py.
- Agent cap: 20 concurrent. Launch Haiku agents with the prompt files; verify each with batch_check.sh / gate.py; run `node tools/check_mermaid.mjs`, `python3 tools/restore/mdx_guard.py`, `npm run build` before each commit. Commit with: git -c user.name=Jithin -c user.email=jithinpnjm23@gmail.com commit (add Co-Authored-By trailer).

## Decisions made by owner
- Python material is needed (JD requirement): restored into new chapters 3.12-3.17.
- AI Factory topics (blockchain, cognitive computing, security, data quality, comms/ML) are waived.
- Max pace; Haiku does all writing, Claude validates.

## Latest update
- Python restoration done since the first note: U027 (3.12), U051 (3.17). Still open: U029 U033 (3.12), U037 (3.13), U043 U032 (3.14), U050 U049 (3.16), U056 (3.17). If an agent died mid-unit, re-run `python3 tools/restore/prep_restore.py Uxxx` (it re-backs up the current file) and relaunch; check `python3 tools/restore/gate.py Uxxx` first, since a unit may already pass.
- Agents that were running when tokens ran out are dead; their finished work is in the files already, unfinished voice rewrites are NOT applied (the chapter file changes only at the final join step), so just relaunch those chapters.
- Scheduled wake-up: 04:31 on 31 Oct (session-only cron). If the session was closed, say 'resume' and read this file.

## Update (Oct 31 morning)
- Python restoration COMPLETE for 3.12-3.17 (all 29 units). Next for Part 3: voice-gate/polish the new chapters 3.12-3.17 (no original to compare; run readability check only).
- Open non-Python restoration: see QUEUE.json minus units with passing gate (ASP ch2,3,5,7,8; K8s Up&Running; Production K8s; Supercomputers; low-percent units).

## Update (Oct 31, rate limit again, resets 09:40)
- Part 5 prepped (prompts planning/restore/V5.N_prompt.md for all 35). Parts 6-15 not prepped: run tools/restore/prep_voice.py P.C ...
- Agent cap is 20 concurrent. Use batch_check.sh on done chapters then build+commit.

## Update (Oct 31 midday)
- Parts 1-4 voice DONE. Part 5 mostly done; Part 6 prepped (V6.N_prompt.md) and started. Parts 7-15 not prepped: run tools/restore/prep_voice.py P.C ...
- To resume cut-off agents: SendMessage to the agent id (work dirs are in scratchpad v/<P.C>), or relaunch with the V<P.C>_prompt.md prompt. Verify with tools/restore/batch_check.sh; build + mdx_guard + check_mermaid before each commit.

## Owner decision (Oct 31 midday): RESTORATION FIRST
- Voice agents were stopped on purpose. Restoration runs before further voice work; voice resumes afterwards (re-run prep_voice.py for each unfinished chapter so chapter_old.md is re-snapshotted from the restored text).
- Restoration order: Tier A (planning/restore/TIERA.json: ASP + AI-fabric units), then Tier B (Supercomputers, Production K8s), then Tier C (How Linux Works, K8s Up&Running). Python restoration is complete.
- TODO after U003 finishes: U011 leftover (Supercomputers ch.28 "One-Two-Three Instructions", Xorg/xorg.conf section, ~4 paragraphs) belongs in 1.30 (remote graphical access: X11, VNC). Run a small restoration agent on docs/part-01-linux/30-*.md for that section only.

## Update (Oct 31 afternoon, rate limit until 15:20)
- Tier A restoration COMPLETE (all 15 units). Tier B/C mostly done. Cut off by the rate limit mid-unit (work so far saved in files): U012, U069, U008 (resume with SendMessage to the agent, or re-run `python3 tools/restore/prep_restore.py Uxxx` then relaunch; check `python3 tools/restore/gate.py Uxxx` first). May also be cut: U076, U005, U003, U002, U015, U018.
- Still unstarted: U059, U077, U013 (Production K8s), U066, U072, U073, U078, U083, U086, U062 (K8s Up&Running), U010, U001, U006, U004 (How Linux Works). Check `ls planning/restore/backup` for which units have been started.
- After restoration finishes: resume the voice pass (Part 5: 5.21 5.22 5.24 5.26 5.27 5.30 5.31 5.32 5.34 5.35; Part 6 onward; Parts 7-15 need prep_voice.py). Re-run prep_voice.py for each chapter first.
- Waivers: planning/restore/WAIVERS.md.

## Update (Oct 31 evening): RESTORATION COMPLETE
- All 114 queued units done or waived (WAIVERS.md). Re-audit (GEM_BOOKS_MASTER.md): non-Python books 108 of 113 chapters <= 40% missing; the 5 above 40% are book intro/copyright text or waived AI Factory topics. Learning Python rows in the master are stale (they still map to 3.1); the per-unit gates measured the real coverage in 3.12-3.17.
- NEXT: resume the VOICE pass. Pending voice chapters: Part 5: 5.21 5.22 5.24 5.26 5.27 5.30 5.31 5.32 5.34 5.35; Part 6: all 31 (6.1-6.6 were started and stopped); Parts 7-15 all (prep with tools/restore/prep_voice.py). Also run a readability/voice pass over the new Python chapters 3.12-3.17 and 3.1.
- Always re-run prep_voice.py right before launching a chapter so chapter_old.md is re-snapshotted from the restored text.
