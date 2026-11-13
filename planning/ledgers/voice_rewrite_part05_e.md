# Voice rewrite, Part 5 chapters 5.13 to 5.15 (batch e)

Scope: docs/part-05-kubernetes/13, 14, 15. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.13 pod networking | 7518 | 9484 | +26.1% | 0 | 2 (`1550`, `8.8`) | 0 | 0.0 per 1000 |
| 5.14 overlay vs routed | 7926 | 9868 | +24.5% | 0 | 1 (`1500`) | 0 | 0.0 per 1000 |
| 5.15 NetworkPolicy | 8221 | 10305 | +25.4% | 0 | 0 | 0 | 0.1 per 1000 |

Guard word counts are the tool's measure. Mermaid, code blocks, tables, front matter, headings, checkpoint
blocks (20 each, verbatim) and Sources sections are unchanged.

## New numbers (explained, not new facts)

- 5.13 `1550`: the MTU walkthrough restates checkpoint 8 ("1,550 bytes" outer packet from a 1500 pod on a VXLAN path).
- 5.13 `8.8`: the `(5.8)` cross-reference to the pod-sandbox chapter, plus `8.8.8.8` from the existing script (already in the code block).
- 5.14 `1500`: the decision-table walkthrough uses a hypothetical 1500-byte fabric MTU. Illustrative only.
- 5.14 `28` and `8972`: the jumbo-ping arithmetic (9000 minus 20 IPv4 minus 8 ICMP) reuses the 5.13 section 7 method.

## Changes that matter

- Honest status: status row ("labs **untested**") kept. One sentence above each lab block ("not run on live hardware" wording). The "(untested here)" reader-text phrases were removed from 5.13 and 5.15 body text. The Sources sections keep their "untested here" lists per the rule.
- Learning-goal announcements removed: "By the end of this chapter, you will be able to" (5.14) and "By the end you should be able to" (5.15); "When you finish, you should be able to" (5.13). Replaced with self-check framing, as in 5.1.
- Rule 9 applied to every exercise and lab list: one question or one instruction per sentence, nested (a)(b) removed. Item counts kept: 5.13 lab 10, exercises 6; 5.14 lab 12, exercises 7; 5.15 lab 13, exercises 6.
- Checkpoint questions and answers kept verbatim (form and count). Checkpoint answer voice NOT rewritten, same as batches a to c.
- No exclamation marks added. No semicolon chains added.
- Attribution: gem book titles written in full in body prose (*Networking and Kubernetes*, *Production Kubernetes*, *Kubernetes: Up and Running* where used).

## Explanation added (no new facts)

- Walkthroughs of existing scripts and manifests: the 5.13 bridge script (one ping, pod-to-pod and pod-to-internet), the 5.13 CNI JSON pipeline, the 5.14 Helm profiles by flag, the 5.14 Cilium BGP manifest read top-down, the 5.15 kuard default-deny test (what the timeout means), the 5.15 Calico GlobalNetworkPolicy order, the 5.15 Cilium FQDN dependency chain.
- Analogies: apartment-to-courier box (overlay), guest list (NetworkPolicy additivity), airport checkpoints (netfilter and conntrack), security badge vs street address (Cilium identity), group chat vs moderator (route reflectors), heartbeat and substitute teacher (BFD and graceful restart), supermarket lanes (ECMP), security desk (policy CPU).

## Needs source (claims present in the original or added as general explanation; not re-verified here)

- 5.13 "RDMA hands the NIC a request and lets the card move data directly" (general description; consistent with checkpoint 10).
- 5.13 "The `mtu` of 1450 ... the value the chapter's MTU arithmetic gives" (internal consistency only).
- 5.14 ECMP "each flow stays in one lane, so its packets arrive in order" (general hashing behaviour; not sourced).
- 5.14 fail-open / fail-closed description (general; the chapter says the default depends on configuration).
- 5.14 "throughput per core" row explanation (interpretation of the table, not measured here).
- 5.15 "Kubernetes: Up and Running (3rd edition, Chapter 19)" kuard walkthrough: original claim, kept.
- 5.15 Cilium `toFQDNs` dependency ("remove the DNS rule and the FQDN rule stops working"): general behaviour per the checkpoint 14 text; not run.
- Original "Needs source" items from batches a to d (checkpoint 20 Blue-Green wording in 5.14, Calico `cali40s` naming, Cilium `bpf-map-dynamic-size-ratio`) are untouched and still need a source check.

## Unresolved

- Checkpoint questions and answers not voice-rewritten (kept verbatim, as in batches a to c).
- Chapter growth: 5.14 is at +24.5 percent, just under the +25 target. A further paragraph would clear it if the owner wants the number exact.
- Not run: npm build, Mermaid check, language_audit, pytest (no code changed).
- No commit made (per rules).
