# Voice rewrite ledger: R9 (Part 5 chapters 01, 08, 10, 12, 14, 20, 21, 23, 28, 30, 33)

## All eleven chapters
- Exercises rewritten: one situation per exercise, short sentences, at most two numbers per sentence, no (a)(b) piles, no nested paren stacks. Solution content is unchanged in substance. Exercise counts grew (6 to 7-10) because compound items were split.
- "untested here" process wording replaced by "have not been run against live hardware" (lab intros, inline comments, Sources notes).
- Gem-book abbreviations KUR, PK, NK, KPG, NPA replaced by full titles everywhere (including headings text in 08 section 4 and checkpoint questions in 08, plus Sources notes).
- "The book" / "the book's example" leaks replaced by the named title (Production Kubernetes, Kubernetes: Up and Running) in 01, 10, 12, 21, 23, 28.
- Stock words ("classic", "essential") replaced in 01, 10, 12, 23, 30.
- Acronyms defined at first use: PLEG (already), FDB, VNI, DSR, ToR in 14; APF in 30; NFD in 33; RPO and RTO in 20. PSAT, IRSA were already defined in 21.
- Openers: 10 rewritten around a user report; 21 split into shorter paragraphs. Other openers already concrete.
- Gates: chain_gate 0.0-0.1 per 1000 for all; language_audit lists no row (no warnings) for these files; checkpoint question counts untouched; no prose exclamation marks.

## Fact checks
- 05.28 istiod: CONFIRMED the claim was outdated. Istio blog (istiod, 2020) says istiod consolidates Pilot, Galley, Citadel and the sidecar injector into one binary; the current architecture page describes istiod as one component. Fixed two passages (section 1 summary and section 3 istiod subsection) to describe one program with three jobs, with Pilot/Citadel/Galley as pre-1.5 history. Note added to Sources.
- 05.21 OIDC .well-known: CONFIRMED the chapter was wrong. Kubernetes docs (configure-service-account) state the API server serves /.well-known/openid-configuration and /openid/v1/jwks, stable since 1.21. Rewrote the IRSA paragraph: the API server serves them, but AWS needs a publicly reachable copy, so a static bucket is the common setup. Note added to Sources. The mention of 1.21 and the endpoints comes from the fetched docs. "The usual setup copies the documents to a public location" follows Production Kubernetes' description; I did not verify EKS internals.

## Not checked
- All numbers in Sources "not verified on live hardware" lists were left as is.
- Production Kubernetes claims (kiam/kube2iam flaws, 1024-bit RSA key in the webhook example) not re-checked against the book. A 1024-bit key is weak by current standards; the chapter reports it as the book's example.
- Section bodies beyond exercises, openers and leak fixes were not line-by-line reread for term stacks; chapters 14, 23, 30 still have dense API-name paragraphs in body sections and deserve a second pass.

## Neighbouring chapters
- Not inspected.
