# Voice rewrite ledger: Part 18, chapters 18.1 to 18.4 (pass a)

Scope: `docs/part-18-security/01` to `04`. Front matter, headings, tables, code fences, Mermaid, checkpoints (20 per chapter) and the Sources and review notes section are byte-identical to HEAD. Only body prose changed. Nothing committed. EXTERNAL_EDITS.md not touched (step 6 of the instructions was skipped as instructed).

## Word counts (`wc -w`, full file)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 18.1 Threat modeling | 6628 | 8951 | +35.0% |
| 18.2 Hardware and firmware trust | 3415 | 4585 | +34.3% |
| 18.3 Containers and supply chain | 7817 | 10709 | +37.0% |
| 18.4 Kubernetes access control | 3696 | 5071 | +37.2% |

Growth is measured on full-file `wc -w`, as the instructions require. The guard's prose-only count (code and tables removed) shows larger percentages, for example 18.4 at 3217 to 4592 words. That count is not the rule metric. All four chapters sit inside the +25 to +40 band on `wc -w`.

## Gates (run on the final files)

- `tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all four. New numbers 0, lost numbers 0 on all four. New code spans: 0, 0, 0, 1 (18.4 adds the typed command `kubectl get` in the NetworkPolicy closing paragraph; it is a command, so kept).
- `tools/restore/chain_gate.py <file>`: 0.0 per 1000 words on all four (target 0.2 or lower).
- Span check (`{}` result required): `{}` on all four.
- Locked-block diff against HEAD: fences, table lines, checkpoint blocks and Sources identical on all four.
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed" (repo-wide tool, run once after all four chapters).
- `npm run build`: not run (instructions said no npm build for this pass).

## Rule compliance notes

- Every `##` and `###` section opens with a situation sentence. Where the first body item was a list (Prerequisites bullets, Controls list, lab prerequisites, exercises), a situation sentence was placed above the list.
- Outcomes lists in 18.1, 18.2, 18.3 and 18.4 were rewritten as a plain paragraph. No "you will be able to" or "should be able to" remains in prose (the grep for both returns nothing in the body).
- Honest status: one sentence above each lab. 18.1 "untested in this repository", 18.2 "were not run on a live cluster", 18.3 "untested" in the lab intro, 18.4 "It was not run on a live GKE cluster here." The 18.3 closing line "This lab has not been run..." in 8.8 was removed to keep one status note per chapter.
- Bold: 7.x Symptom/Diagnosis/Fix labels are now plain text (one bold idea per section rule). The bold lead-ins that remain are the original ones.
- Raw `<` or `{` in prose: none added. The only hits are inside locked tables (18.1 "< 90 days", 18.3 SLO and alert cells).
- Exclamation marks: none.
- Semicolon chains: chain gate 0.0.
- Gem books: none named in added text. Original attributions (Production Kubernetes chapters, Engineering AI Systems Chapter 9, NVIDIA Zero-to-Hero volumes) kept as written.
- Checkpoints: unchanged (form, count 20, answers identical).
- Math `$...$`: none in these four chapters. Dollar amounts appear only in locked code blocks and checkpoint answers.

## Needs source (general explanations added in prose, not from the original text)

These are plain definitions or teaching claims added during the rewrite. None adds a number. Each would need a citation if the handbook requires one.

- 18.1: the rate-limit reasoning that a new key starts with a fresh allowance (section 3.2); the claim that a copied file costs more than its storage (section 2.1 teaching line); the advice to keep threat model meeting notes in the same repo (section 6.1).
- 18.2: definition of a DPU ("a network card with its own processor") and of the BMC as "a small computer on the board that manages the server from outside its operating system"; extending a PCR as "hash of the old value combined with the new measurement" (section 1.1); a nonce as "a random value that only the verifier knows in advance" (section 1.2); the badge-check analogy for SPDM (section 2.1); the canary rationale "some firmware problems only show up under real load" (section 4.2).
- 18.3: OIDC defined as "the login standard that CI systems already use to prove who a job is" (section 1.2); the "key holder" and "rotation" advice (section 1.1); Kyverno rules described as "Kubernetes objects" (section 2.2); the SBOM "borrows from manufacturing" remark (section 3.1); the scanner-disagreement claim, that two scanners can report different counts because they read different sources (section 4.2); the pinned-file maintenance advice (section 5.2); the claim that a policy in warn mode looks almost identical to enforce mode (section 7.3); the OCI definition ("the group that maintains the standard", section 9.1); signal and reaping definitions (section 9.4); `/etc/passwd` explanation (section 9.4); defense in depth definition (section 9.6).
- 18.4: CEL defined as the Common Expression Language (section 3.3); ServiceAccount defined as "the identity a pod uses when it talks to the Kubernetes API" (section 1.1); the default ServiceAccount "shared by every pod in the namespace that does not name another one" (section 2); the three Pod Security levels as "three doors of increasing trust" analogy (section 3.1); the statement that the cluster network is open by default (section 4); the claim that a policy object ignored by the network plugin "looks correct in kubectl get" (section 4).

## Unresolved (not changed)

- 18.2 checkpoint 6 "What does SPDM let one component do to another?" reads as a definition question. Left unchanged per the checkpoint rule. The answer is supported by the chapter.
- 18.4 known issue from `planning/ledgers/checkpoint_rewrite_F.md`, kept as-is: the Pod Security labels in the namespace example target `team-data-science`, while the ValidatingAdmissionPolicy binding targets `mlops`.
- 18.4 lab step 2 uses `code/part18/rbac_rolebinding.yaml`, which the chapter does not show. Kept.
- 18.4 anti-pattern rows in the NetworkPolicy table ("Egress to 0.0.0.0/0", "Missing policyTypes") are loosely stated in the original. Table is locked; not changed.
- 18.3 Gatekeeper skeleton calls an undefined `cosign_verify`. The prose now says it is a skeleton, not a working check. The Kyverno rule checks a label, not a signature. Both flagged in prose; the YAML is locked.
- 18.1 example dates in the locked lab code (`2024-04-15`, `2024-07-15`) and in the threat template (`2024-03-15`) predate today's date. Locked code, flagged here only.
- 18.1 and 18.3 mention example budget and dollar figures (`$100k-$1M`, `$3-5k per H100`). These are the original's placeholders and remain flagged as examples.
- 18.2 "Redfish update service" and the simulated firmware versions in the lab are the original's; the Sources "Corrections made in this rework" section (locked) already records the removed commands.
- 18.3 section 9.2 "gold image" bullets were rewritten from the original's bullets into question-and-answer form. Same three requirements, same facts.
