# Voice rewrite ledger: R10

Gates at the end: chain_gate 0.0 to 0.5 per 1000 words on all 14 files; language_audit lists no warnings for any of them; checkpoint count is 20 in each chapter that had 20; no exclamation marks in prose. Part 16, 17 and 18 Checkpoint sections were not edited.

## Per chapter

- **8.3 bcm/03**: replaced the helper-command term stack (nodeoverview and others) with two lead commands plus a table; collapsed the triple-repeated MIG overallocation example into one worked case plus one sentence; rewrote exercise 4; removed ledger paths from Sources.
- **8.11 bcm/11**: removed "my arithmetic" and bold run-in labels; rewrote the three bold-numbered steps in 9.1 as plain steps; Sources "My own choices" line renamed; first-person note about the Xid mapping made impersonal. Flapping arithmetic (120 s sampling cannot give 5 crossings in 300 s) re-checked: confirmed.
- **3.6 python/06**: exercises rewritten from six packed items into eleven single-situation items; "classic" removed.
- **3.10 python/10**: exercises rewritten from six into thirteen single-situation items; figures unchanged.
- **2.29 net/29**: exercises rewritten into ten; the `compute_idempotent_config_diff` exercise was checked against the code.
- **2.18 net/18**: removed leaked "The source describes this as about an hour" and replaced with "close to an hour". Arithmetic confirmed: 99.99% is 52.6 min/yr, 99.9% is 8.8 h, 99.999% is 5.3 min. Exercises split into eleven.
- **2.32 net/32**: the /20 plus /14 claim was wrong as worded. Confirmed with the chapter's own arithmetic (section 9 answer 13): 1,024 nodes comes from the /14 pod range cut into /24 per node, 4,096 Services comes from the /20 Services range; the /20 node subnet gives 4,092 usable IPs and is not the limit. Fixed the lab paragraph and exercise 5. Exercises rewritten into nine.
- **18.5 security/05**: six look-alike exercises replaced with six distinct ones (node admission check, MIG profile choice, mode choice, Prometheus alert, Pending pod diagnosis, incident order). Section 7 failure modes changed from six Symptom/Diagnosis/Fix label blocks to varied paragraphs. Corrections: the MIG layout block listed 5g+4g+2x3g+4x1g (19 slices, impossible); replaced with valid examples (seven 1g.10gb, or one 3g.40gb plus three 1g.10gb) and removed "IOMMU enforced" from the MIG isolation line. Added notes that `-cgi` profile IDs vary and come from `nvidia-smi mig -lgip`, that `mig-1g.5gb` is a 40 GB card name, that the vGPU enable command is untested, that perf event names vary, and that the IOMMU is not on by default everywhere. Fixed the time-slicing sentence that contradicted its table (memory not shared vs "None" isolation). Replaced "TPM" backing store with BIOS and kernel settings.
- **7.1 redfish/01**: removed leaked volume paths from the body (kept in Sources, now tied to the sections they support); defined I2C/SMBus/UART in place of the bus stack; "We implemented/tested" left as is (plain statements); exercises 3 to 6 shortened to one situation each.
- **16.7 mlops/07**: removed "Earlier drafts" note. Seldon: the YAML put retriever and generator as two `predictors` (alternatives, not a chain). Rewrote `code/part16/seldon_graph.yaml` and the chapter block to one predictor with a retriever graph node and a generator child, custom containers with placeholder images; removed unverified `modelUri` in graph; text now explains that multiple predictors are alternatives. Scaling row of the ownership table made consistent (model team writes values, platform team sets limits). Not validated against a live cluster.
- **16.9 mlops/09**: system prompt as "most effective jailbreak defence" softened to "first layer, not enough alone". Corrected the claims that the safety filter is LLM-as-judge and the jailbreak classifier is trained on a held-out set; the code is a rule-based stand-in, now stated. Rewrote the muddled regression-set paragraph in 5.3.
- **19.3 capstone/03**: removed "earlier draft" and "old draft" narration from body and two checkpoint items; converted "my reasoning" and "I did not run" to plain statements. Corrections log in Sources left as is.
- **19.8 capstone/08**: "the guide" (about 20 uses) changed to "the MIG User Guide"; removed "earlier draft" in the Kueue paragraph; "my reasoning/design" replaced by impersonal wording.
- **19.11 capstone/11**: all first-person asides ("I do not know why", "my sum", "I did not hide") replaced; interview-table cells made impersonal; one checkpoint question reworded. Numbers untouched.

## Could not check
- Seldon manifest against a live cluster; vGPU enable command; perf IOMMU event names; nvidia-smi MIG placement of 3g.40gb plus three 1g.10gb on A100 80GB (stated in exercise 2 of 18.5 with advice to confirm with `nvidia-smi mig -lgip`).
- Chapters were rewritten at the flagged spots and exercises; the full body of the long chapters (bcm/03, python/06, python/10, net/18, net/29, 19/03) was not read line by line.

## Errors in neighbouring chapters (not fixed)
- 18.5 Checkpoint answer 6 (and similar) still says "The chapter suggests quarterly" (another worker owns Part 18 checkpoints).
- 16.7 Checkpoint section was not checked for Seldon predictor wording.
