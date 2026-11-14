# Voice rewrite ledger: 11.34 NVKE in depth, part 3

File: `docs/part-11-gpu-kubernetes/34-nvke-in-depth-part-3-operations-security-failure-modes-and-comparison.md`
Nothing committed. Other chapters untouched.

## Words

| Measure | Before | After | Change |
|---|---|---|---|
| rewrite_guard word count | 5826 | 7338 | +25.9 percent |
| Non-fence words (plain split) | 5920 | 7432 | +25.5 percent |

Note: +25.9 percent is at the lower edge of the band. Growth is in the situations, the reading guides and the definitions. No facts were added.

## Gates

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. Residue 3 to 3. The three hits are honest-status phrases ("I did not test a restore", "I confirmed", "I did not tune") that the original already used. A fourth phrase added during drafting was reworded.
- Literal backticked-span Counter check, HEAD vs worktree outside fences: lost {} and new {}. Two originally backticked words (`exp` and `sub`) were restored in the token sentence.
- Code fences: byte-identical before and after (Mermaid flowchart, the promtool rule file, the promtool output).
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words.
- `node tools/check_mermaid.mjs` over all docs: 776 diagrams, 0 failed.
- Checkpoints: 20 before, 20 after, text verbatim.
- Not run: `npm run build` (excluded by the task).

## What changed

- Front matter, heading text and order unchanged.
- Outcomes list converted to a plain paragraph.
- Each section opens with a situation: the 02:10 pager, the security reviewer, the alert about a kubelet certificate, the backup question, the security review, the failing node, the pending machine, the interview.
- Added explanation: the T1 and T2 analogy, why a renewal lock matters, renewal versus monitoring, leaf certificates, the CSR and kubelet certificate, the role of the three authentication modes, the JWKS and token claims in plain words, the defence-in-depth reading of the mitigations, the failure table read as two rows that need a human, the metric table read as questions, the Prometheus and promtool roles, the comparison's sourcing column, what a statement of intent means, the budget table as one glance, the interview order.
- Kept verbatim: code, Mermaid, tables, Sources and review notes, Verification log, checkpoints.

## Needs source

- Section 2.1: the sentence that the controller refuses to start when renewal settings contradict credential monitoring (kept from source; the 45-day figure is in the original).
- Section 4.3 item 8: "a compromise of the agent is a compromise of the node" is inference from "privileged root-level service" in agent/docs/SECURITY.md. The inference is not stated in the source.
- Section 4.3 item 2: the statement that TLS stops a token from being read on the wire (general background).
- Section 5: the explanation of a blackbox exporter and of promtool checking syntax only (general Prometheus background; the promtool behaviour is also the subject of exercise 4 in section 9).
- Section 3.2: the description of a logical dump as SQL statements (general PostgreSQL background).

## Unresolved

- The stated "Explicitly labelled inferences" list was not changed. It still names three items; section 3.2 and section 4.3 carry their own inference tags.
- The mitigations and the alert thresholds remain author recommendations, as tagged in the original.
- EXTERNAL_EDITS.md was not edited, per the task instruction.
- Pre-existing wording kept: "Step" headings and the "Sources and review notes" section unchanged.
