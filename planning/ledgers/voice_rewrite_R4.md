# Voice rewrite ledger: R4 (Part 9 chapters 01, 05, 06, 07, 08, 09, 12, 14)

Gates run per chapter: chain_gate (0.0 to 0.1 per 1000 words), language_audit (no warning rows), checkpoint summary count unchanged (20 each), no exclamation marks.

## 01 DGX system families
Rewrote: opening (two concrete failures), two-models bullets, scope note, section openers 1/2/3, Whitebox section (invented name and Formula One metaphor removed; heading now plain; outcome, tip, checkpoint 15 reworded), "my inference" leaks, six exercises split into one question each.
Confirmed: none needed beyond chapter facts. Not checked: unstated vendor figures in tables (left unchanged).

## 05 NVL72 racks
Rewrote: opener (the 1.8T MoE case), 8-GPU wall section (office-building analogy removed), "Therefore" opener, BCM firmware opener, scope note, exercises, provenance notes.
Decision: the "more than thirty times / 50 ms" marketing sentence is now attributed to AI Systems Performance Engineering as "roughly 30 times"; the table keeps the lab ratio 44.12x and says the book summarizes as roughly 30x. The "more than 5,000 cables" correction note rewritten as a plain statement.
Could not check: 3.4 and 150 tokens/s per GPU figures beyond the cited book.

## 06 SuperPOD concepts
Rewrote: opener, AI factory analogy, physical twin / three rules (First/Second/Third shape replaced), storage System 1/System 2 (split into short sentences, RDMA, POSIX defined, partner names kept in one sentence), Mission Control five layers moved into a table, TCO opener, exercises.
Decision: linear per-SU storage scaling labelled as the chapter's own extrapolation.

## 07 DGX B200 data center
Rewrote: opener (PDU interleave story), Power/Cooling/Space section (rubber triangle removed), "mandatory before a single crate" and "massive air volume" removed (air volume now given as 2,145 CFM per node, 4,290 and 8,580 per rack, all in the chapter's own table), exercises, provenance item.
Checked: 2,145 CFM = 150 CFM/kW x 14.3 kW, confirmed. "Over two thousand cables" = 1,020 + 1,024 = 2,044 from chapter 9.6 table, confirmed.
Softened: "half-circuit symmetry" claim. The source table lists two nodes for the 2x415V 32A pair with 15.1 kW stranded; the reason is not in the source, so the text now says so and offers the whole-nodes-per-circuit reading as the chapter's own.

## 08 GB300 SuperPOD RA
Rewrote: six "X feel this" openers (sections 1, 3, 4, 5, 6 and intro) replaced with concrete situations; "secret", "massive", "solves this problem", "months to weeks" removed (the source states no deployment time); exercises; "my inference" lines.

## 09 Networks in a SuperPOD
Rewrote: opener, airport analogy removed, five "feel this" openers, entropy and RDMA defined, In-Band opener, OOB endpoint bullet list turned into a component/port table, command and failure intros, exercises.

## 12 Software stack
Rewrote: opener and the five-layer product list (one plain sentence per layer, products in the Section 1 table), orchestra analogy, driver/container, distributed, Kubernetes and observability openers, ZeRO "my inference" line, exercises. "Fifty-million-dollar" figure dropped (not sourced).

## 14 Cloud GPU platforms
Rewrote: opener, scope note, SR-IOV paragraph, archetype note, all section openers, exercises.
Softened: "cut training throughput by half or more" and "tens of microseconds of latency" removed; neither figure is in the cited sources.

## Not fixed (noticed)
- Chapter 07 sources table still stacks many backticked constants in one row. Several Sources and review-notes sections still use "inference" wording in the chapter's own voice; left in place as provenance.
- Chapter 05 code-output block contains the abbreviation "ASP" inside lab output text (code block untouched).
- Chapter 01 checkpoint questions use a `<details>` newline `<summary>**N. ...**` form, not the single-line form; left as is.
