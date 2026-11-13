# Part 7 code-span restoration (ledger f)
1. Scope: 01, 02, 03, 14 in docs/part-07-redfish-bmc/; restored inline code spans lost in the 2315acc warm rewrite.
2. 01: the flattened objectives list (orig lines 40-45) was the source of ~25 lost spans; rewrote the intro paragraph to carry them as backticked terms.
3. 02: restored `generic` in the lab question; 03: restored GET/PUT/DELETE/OPTIONS, `ETag`/`If-Match`; 14: restored `plan` in four spots, `bmc`, `mc` (ipmitool alias sentence).
4. Check result: lost-span check prints {} for all four; rewrite_guard 2315acc WORKTREE shows 0 hard failures; no code blocks, headings, numbers, checkpoints or Sources changed.
5. Not committed. Part 8 files untouched.
