# Voice rewrite ledger: R5

Chapters: part-11 05, 11, 18, 19, 22, 28 (full pass on opener, stock phrases, exercises); 02, 24, 09, 13 (targeted fixes). 11.31 to 11.34 untouched. 11.19 "open source as of 2026-10-13" note kept.

Gates: chain_gate 0.0 to 0.1 per 1000 words on all ten; language_audit shows no warning row for any of them; `<details>` count 20 in each of the six full chapters (unchanged); no exclamation marks added.

## Per chapter
- 05: rewrote the upgrade opener (Secure Boot story), Helm values-governance sentence, "blind" phrase, upgrade-risk paragraph, six-surface lead-in, six exercises (one situation each). Removed validation-date sentence from Corrections.
- 11: rewrote opener (one dropped frame), manual-network paragraph, kernel-upgrade opener, SNMP sentence (30 s counter vs microsecond burst), six exercises.
- 18: rewrote the "Resist / must never" paragraphs (says restart destroys logs, events, driver state; first safe step is freeze rollouts + healthy peer), change-surface paragraph, time-sliced SLI sentence, exercises 2 to 6.
- 19: rewrote opener, Run:ai-is-not-sharing paragraph, closing paragraph, "Golden Rule" lead sentence, fairness time scales (opens with the lab flooding the queue), "Let's", six exercises. Headings unchanged.
- 22: split the IOMMU item into "slice of the card / can still reach any host memory", removed "ransomware outage" rhetoric, "scorched-earth", bold-claim list items, six exercises.
- 28: replaced "zero x86 CPU tax" (twice) with the 400 Gbps software-encryption explanation, removed "massive", figure-reference filler, exercises 1 to 4 and 6.
- 02: removed validation-pass sentence from Corrections.
- 24: removed validation-pass sentence; folded the "corrected 2026-11-11" note into plain sentence with source.
- 09: replaced the off-topic prompt-engineering paragraph with one tied to the decision to launch a TrainJob (kept the KV-cache cost fact; dropped the prompt-injection aside, which is off topic here).
- 13: the 60% and 85% figures trace to the author's Volume 23 chapter 7 notes only. Rewrote the two body paragraphs to say so and that the notes give no measurement conditions; removed "or higher" claim.

## Claims
Confirmed against chapter's own sources: none re-checked against external sources. Could not check: origin and measurement method of 60%/85% (Volume 23 notes not available as a primary source); 11.19 exercise on six AI Factory layers now lists layers from chapter text, unverified ordering dropped.

## Neighbour issues, not fixed
- 02, 09, 11, 13, 18, 19 Sources sections still carry "validation pass 2026-10-25" lines (left, since provenance belongs there).
- 13 table rows and checkpoint Q2 still state 60% vs 85% without the "illustrative" caveat.
- 11.28 "Prerequisites" says 11.22 covers Zero-Trust Security; 11.22 is SR-IOV (security is a section there). Not changed.
