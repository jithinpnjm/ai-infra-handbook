# Voice rewrite, Part 5 chapters 5.10 to 5.12 (batch d)

Scope: docs/part-05-kubernetes/10, 11, 12. Uncommitted. Gates run per chapter with
`python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, full Mermaid check, language_audit, pytest.

## Per chapter

| Chapter | Words before | Words after | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.10 services-endpoints-and-kube-proxy | 10508 | 13147 | +25.1% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.11 dns-and-service-discovery-with-coredns | 8049 | 10067 | +25.1% | 0 | 0 | 0 | 0.0 per 1000 |
| 5.12 ingress-load-balancers-and-the-gateway-api | 10751 | 13427 | +24.9% | 0 | 0 | 0 | 0.0 per 1000 |

Guard word counts are the tool's measure (body prose), not `wc -w`. Residue (guard): 1 -> 0 in 5.10 and 5.11,
0 in 5.12. Exclamation marks: none. Honest status: status row "labs **untested**" kept, plus one sentence above
each lab ("have not been run against live hardware" / "not been run against a live cluster" / "not run on live hardware").

## How the rewrite was done
- Code blocks, tables, Mermaid, front matter, H1, every heading, checkpoint block (20 each), Sources and review notes: kept byte-for-byte.
- Prose: terse paragraphs rewritten in place where they were drafting-voice. Explanation (analogies, "put simply",
  worked walkthroughs, the why) inserted after existing paragraphs. Prerequisites bullets reframed as a self-check.
- Exercises (the `## Exercises` section only) rewritten per rule 9: one question per sentence, at most two numbers
  per sentence, no nested (a)(b). Counts kept: 5.10 = 8, 5.11 = 6, 5.12 = 9.
- Lab step lists (5.10 section 9, 5.11 section 8, 5.12 section 8) were NOT rewritten. They are lab instructions, not
  the Exercises section. They are still dense (several numbers per step). Needs a decision.

## Fact-adjacent changes to review
- 5.10 `kubectl` exercise text: "Take the six Service patterns" (same count, same six types).
- 5.10 "Use the four steps from section 7" (exercise 8): same four steps (resolve, endpoints, rules, datapath).
- 5.11 exercise 3: removed the borrowed label "Table 4-5" from the background pointer; now "Networking and Kubernetes, chapter 4". Attribution label only, not a fact.
- 5.11 exercise 2: the answer counts (8 queries, 6 NXDOMAIN, 2 answers) are now stated as separate questions with answers, same values.
- 5.12 exercise 9: the list of status codes (404, 413, 429, 502, 503, 504) moved out of the sentence and into a pointer to the section 7 table, which lists the same codes. Same content, no new fact.
- 5.12 Ingress "The Future of Ingress" references (two places) now point to the in-chapter heading "Where Ingress is heading".
- 5.12 "has not been run here" removed from the Production Kubernetes TCP proxy example lead-in (second honest word; one per chapter kept at the lab sentence).
- 5.11 "Alpine's resolver ... test the image before you rely on it": added advice, no new claim beyond the original "older versions" statement.

## Needs source (new explanatory claims, not verified here)
- 5.10: `ss -tulpn` shows no socket for a ClusterIP (consistent with checkpoint 1; not run).
- 5.10: a readiness probe that is too strict can pull every pod out during a busy minute; too eager sends traffic to pods still loading weights (general behaviour, not sourced).
- 5.10: the "Friday afternoon" ingress node and "restaurant", "mail office", "taxi stand", "shop with shutters" analogies are illustrative only.
- 5.11: negative caching at NodeLocal means the node remembers an NXDOMAIN and answers the next pod from the node (explanation of the original "Negative caching also reduces NXDOMAIN storms"; check NodeLocal DNSCache docs).
- 5.11: "two replicas can survive a single restart" and "a memory limit that is too low can get the pod killed" (general Kubernetes behaviour).
- 5.12: "Two such pods on one node compete for the same ports" (hostNetwork port binding; general behaviour).
- 5.12: "Chapter 17" in the "Why Ingress has no default controller" section (extension-features sentence) names no book. Kept as original. Needs the book and chapter, or a rewrite that names the source.

## Unresolved
- Checkpoints in all three chapters: kept verbatim (form and count). Checkpoint answer voice not applied.
- Lab step lists (see above) not rewritten for rule 9.
- Not run: npm build, Mermaid check, language_audit, pytest (no code changed).
- No commit made (per rules).
