# Voice rewrite ledger: Part 7 chapters 7.1, 7.2, 7.3 (batch a)

Base: HEAD 0ab0931. Only the three chapter files were edited. Nothing committed. EXTERNAL_EDITS.md not touched (per run instruction).

## Word counts (`wc -w` on the whole file, front matter included)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 01-bmcs-ipmi-and-out-of-band-management.md | 9044 | 11537 | +27.6% |
| 02-redfish-concepts-service-root-resources-collections-odata.md | 7036 | 9265 | +31.7% |
| 03-the-redfish-protocol-http-methods-headers-status-codes-query-parameter.md | 7264 | 9283 | +27.8% |

Locked parts (checkpoints, Sources, code blocks, Mermaid, data tables, front matter, headings) were copied unchanged. Growth is in prose only.

## Gates (run by hand, output below)

rewrite_guard.py HEAD WORKTREE (final run per file):
- 01: `ok ... words 8212->10705 new numbers 0 lost numbers 0 new code spans 0 lost 0 residue 1->0`
- 02: `ok ... words 6554->8783 new numbers 0 lost numbers 0 new code spans 3 lost 3 residue 0->0`
- 03: `ok ... words 6666->8685 new numbers 0 lost numbers 0 new code spans 7 lost 4 residue 0->0`
- Hard failures: 0 on all three.

Span check (set comparison of backticked spans, the guard count has pairing artifacts):
- 01: no new spans, no lost spans.
- 02: no new spans, no lost spans (after restoring `PT10S`, `PT1H30M`, `Mbps`, `@Redfish.AllowableValues`, `@Redfish.AllowableNumbers`, `@Message.ExtendedInfo`, `405 Method Not Allowed`).
- 03: no new spans, no lost spans (new plain-text replacements for `#`, `3`, `finally`, `return`, `P`, `On`/`Off`, `Gbps`, `405` were turned into prose).

chain_gate.py: 01 = 0.0, 02 = 0.0, 03 = 0.1. All at or below the 0.2 target.

Build and Mermaid: NOT run (run instruction said no npm build and no full Mermaid). Mermaid blocks are byte-identical to HEAD.

## Dropped or changed items (explained)

- 03: the internal labels "Table 4" (status codes) and "Table 5.1" (query parameters) were replaced by "the table below" and "Section 5.1". These are borrowed table labels, not facts. The DSP0266 citations ("Table 3", "Table 15", "Table 13") are kept because they are spec references.
- 01, 02, 03: the "Prerequisites and outcomes" bullet lists were rewritten as plain paragraphs. The code spans and DSP0266 clause numbers from those bullets were carried into the paragraph (verified by set comparison).
- 01: "Part 2" (new cross-reference) was reworded to "the networking basics earlier in this handbook" so no new number appears.
- 01: "the book says" residue in two places changed to the full title *Supercomputers for Linux SysAdmins*. The attribution is the one the original already made.
- 01: the status row no longer says "untested / not verified" in bold. It now reads "have not been tried on a live physical BMC". The Exercises intro carries the single "not run" / "untested" sentence.
- 02, 03: the same honest-status pattern (status row plus one sentence above Exercises). In 03 the Exercises sentence says "unconfirmed" instead of "untested" to keep one honest word per place.

## Needs source (explanations added that are general knowledge, not from the chapter's books or DSP0266)

Verify before publishing, or accept as general background:
- 01: TLS (encryption layer for HTTPS) plain definition; UDP has no per-packet confirmation (RMCP+ session built on top); serial notation `115200 8N1` meaning (8 data bits, no parity, 1 stop bit); `agetty` as the login-prompt program; kernel oops as the kernel's own error report; VLAN and trunk definitions; hypervisor definition in the cloud comparison; STONITH expansion ("shoot the other node in the head"); rainbow-table definition; RMA definition.
- 02: `jq` description as a command-line JSON reader; ephemeral port definition; ICANN and IANA roles in OEM identifiers; UPnP and multicast description of SSDP; "hypermedia" explanation (generic); mock-server definition.
- 03: OOM killer description (Linux process that shuts down memory users when RAM runs out); HTTP status-code families (first digit meaning) and idempotent/safe definitions per RFC 9110 (not DSP0266); strong vs weak ETag meaning ("bytes identical" vs "equivalent") per RFC 9110 §8.8.1 (not DSP0266); JSON Pointer `#` root.

No new numbers were added to any chapter (guard: "new numbers 0" on all three). No invented book or volume attribution.

## Self-check (standing rules)

- No "you will be able to" / outcome checklists left (the 01 and 02 "outcomes" lists became paragraphs; 02 "By the end" sentence reworded).
- Every section opens with a situation (checked by reading openings of sections 1-7 and subsections 1.1, 2.1, 3, 4.1-4.3, 5.1-5.3, 6.1, 6.2, 7.1, 7.2 in each file). Openers that were not a situation at first were reworded (01 section 4.2 and 7.1, 02 section 7.1 and 7.2, 03 section 7). Subsection 2.1 of 01 and 2.2 of 02 still open with a short framing sentence before their table. Left as is; they are reference-table lead-ins.
- Exercises: 6 each (same count). Each keeps its original commands and facts. Multi-part exercises were split into one question per sentence (01 Ex 1 and 3, 02 Ex 2, 03 Ex 1 and 5). Commands were not changed.
- Lab steps: the chapter labs (02 section 6, 03 section 6) keep their commands and outputs verbatim. No separate "lab step list" exists in 01 beyond the `oob_sim.py` and `oob_cred_lab.py` commands, which are kept verbatim.
- Checkpoints: 20 each, unchanged text and form.
- Sources and review notes: unchanged text.
- Exclamation marks: none in prose. Raw `<` appears only in the `<details>` / `<summary>` markup, which is locked.
- Semicolon chains: the only "; the/every" hit is inside a locked table cell (03 section 1 methods table).

## Unresolved

1. Build (`npm run build`) and `node tools/check_mermaid.mjs` were not run (out of scope for this run). Mermaid bytes are unchanged, so no Mermaid regression is expected.
2. 01 Section 2.1 and 02 Section 2.2 open with a framing sentence rather than a lived situation. A reviewer may want one more line of situation there.
3. The "Needs source" list above has general-knowledge explanations. None of them touches a DSP0266 clause or a number from the chapter. A reviewer should still check the RFC 9110 points if the handbook wants citations.
4. Other part-07 chapters (04, 05, 06) show as modified in `git status`. They were edited by the other agent in parallel. This run did not touch them.
