# Checkpoint rewrite report: agent D (17.05 to 17.10)

All six chapters: 20 questions each, replaced all 20 (old questions were definition/recall; none kept). No question dropped for lack of support. chain_gate 0.0 to 0.1 per 1000 words. details count 20 each.

## Notes per chapter (errors seen, not fixed)
- 17.05: Old Q20 and lab say 5 s vs 30 s targets inconsistently (example values). Profile cardinality section mixes storage size with label cardinality. Dashboard series (pytorch_profiler_*, nccl_*) have no exporter in the chapter.
- 17.06: Section 6.4 title says the readiness probe restarts the pod, but readiness only removes it from the load balancer; liveness restarts. Old checkpoint Q5 (inhibition) described the direction backwards. Runbook YAML uses runbook_url, lab 17.07 jq uses runbookURL.
- 17.07: GPU hang signal (SM clock > 0 with no kernel) is self-contradictory as a hang detector. Lab step 9.5 says "inject synthetic ECC error" but only reads counters. GPU OOM severity is Warning in 1.1 table and Critical in 4.1 table.
- 17.08: Attention example: 6.87e10 / 3.36e7 is exactly 2048, chapter says 2045 (rounding). Bytes formula omits seq_len squared while FLOPs include it. Dashboard cost rate 3.20 per GPU hour conflicts with $32/hour for 8 GPUs (4.00). Section 7.5 compares a next-quarter forecast (156) with current usage (100).
- 17.09: NET-014 says NCCL_DEBUG is INFO in production, while 17.05 and 17.07 advise WARN because INFO is very verbose. NET-018 "NCCL_IB_TIMEOUT is set to 600 seconds" should be checked against NCCL docs (value is likely not seconds). Chapter itself notes 207 items vs the 175 in the formula (verified 207 by grep).
- 17.10: Rollback example runs apt-get install inside kubectl exec on the node, not realistic. Lab step 5 says canary but applies directly (chapter admits). Trigger signal dcgm_ecc_dbe_total does not match DCGM metric naming used elsewhere. Window table row "Weekday 2-4 AM High" overlaps the Tuesday and Wednesday rows. Long generic software-engineering passages (Lehman laws etc.) are not tied to the cluster.
- Shared scratch dir /private/tmp/claude-501/s was overwritten by another agent (splice.py); I moved to /private/tmp/claude-501/dagent. No chapter damage.
