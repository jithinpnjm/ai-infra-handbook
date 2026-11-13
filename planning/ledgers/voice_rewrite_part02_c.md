# Voice rewrite ledger: Part 2 chapters 2.26-2.30 (agent C, deep pass)

Method: insertion pass on the current worktree files (the light polish from earlier stays). Each chapter got new paragraphs placed after or before existing paragraphs, anchored on a unique line. No existing sentence was deleted. Code blocks, tables, Mermaid, front matter, headings, checkpoint blocks, Sources, status rows and the "untested" wording are unchanged. New paragraphs are situation, plain why, step-by-step "what actually happens", analogy or small worked example. Worked examples reuse numbers already in the chapter (guard: 0 new numbers in every chapter). Two invented numbers in 2.30 were replaced with wording.

Gates (`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`, `python3 tools/restore/chain_gate.py <file>`):

| Chapter | Words HEAD to now | Guard hard failures | New / lost numbers | New / lost code spans | Chain gate |
|---|---|---|---|---|---|
| 2.26 | 8864 to 12002 | 0 | 0 / 0 | 11 / 2 (lost = "untested here" label plus light-polish flag spans) | 0.0 |
| 2.27 | 5934 to 8400 | 0 | 0 / 0 | 4 / 4 (lost = "untested here" label only, others from the light polish) | 0.0 |
| 2.28 | 9711 to 12286 | 0 | 0 / 0 | 3 / 1 (lost = "untested here") | 0.2 |
| 2.29 | 9238 to 11573 | 0 | 0 / 0 | 0 / 1 (lost = "untested here") | 0.0 |
| 2.30 | 8717 to 11506 | 0 | 0 / 0 | 0 / 1 (lost = "untested here") | 0.0 |

Exclamation marks, code blocks and checkpoint counts unchanged. Status wording ("untested" / "not run") still present in each chapter.

## Known gaps (not done in this pass)
- 2.27: Lab 2 experiments 3 to 6, Lab 4 items 2 to 6, Lab 5 items, Lab 6 items 2 to 5, Lab 7 harness text and the evidence table have one added paragraph or none. Each lab step still needs a "what you should see and why" paragraph.
- 2.28: the Python library table and the Netmiko paragraphs, the RESTCONF and YANG PATCH sections, and the SDN examples (Fibbing, PCEP, I2RS, OpenFlow) got at most one paragraph each. The control-plane examples need a worked example.
- 2.29: the Ansible playbook and Nornir script areas, the Terraform paragraphs and the GitHub Actions workflow have only opening and closing paragraphs added. The architecture components (SoT, automation engine, telemetry) need one walkthrough each.
- 2.30: the case-study fixes (what to change, in what order) are untouched beyond the mechanism paragraphs. The AI-fabric symptom table and the exercises are unchanged.
- Interview and exercise sections are unchanged in all five chapters.

## Facts to double-check (mechanisms explained in new text, from general knowledge, not from a source)
- 2.26: the reply path explanation (tap sees both directions on the host); "fifteen" removed on purpose; the verifier description of eBPF.
- 2.30 Case 6: dampening description (penalty, suppression after the optic recovers). Case 13: the parallel A and AAAA race mechanism (conntrack race). Case 8: the pause-storm spread. These follow the case text but were not checked against a vendor or RFC source.
- 2.28: CAP split example; BGP-as-SDN statement that injected routes last only while the session is up (standard BGP behaviour).

## Coordination
- Did not touch 2.18 or 2.23 to 2.25 (other agent).
- Nothing committed. No Mermaid or npm build run in this pass (code and Mermaid blocks are byte-identical per the guard).
