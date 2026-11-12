# Rework ledger: W7

Chapters: 3.1, 3.3, 3.11, 4.3, 6.24, 6.30, 8.14, 8.16. Chapters 3.12 to 3.17 were not touched (owner keeps them).
Gates for all eight: chain_gate under 1.5, `<summary>` count unchanged (20 each), no exclamation marks in prose (3.1 keeps "Hack!/Bad!" strings inside code output), no `$` math left in prose, check_code_files part03 and part06 pass. language_audit rows remaining: 3.1 has 3 warnings (long sentences, backtick density), 3.3 has 2 warnings. I did not record the before counts, so I cannot say whether they fell.

## 4.3 Ansible from zero
- Added the NOPASSWD scope caveat: dedicated automation account, no interactive login with key-only SSH from the control node, audited use; fallback `%ansible ALL=(ALL) ALL` with Vault.
- Removed "Up and Running" attributions from body, headings and two question stems; Vagrant heading tag removed; "untested here" removed.
- Watch list: NOPASSWD advice fixed (caveat added).

## 6.24 Users, LDAP, SSSD, quotas
- Deleted NIS/NIS+ setup (8 steps, start-up commands, securenets); replaced by a short "for the record" paragraph. Deleted slapd.conf/bdb/nss_ldap/pam_ldap recipe and MigrationTools walkthrough; replaced by "Standing up the directory" (cn=config, mdb, base entry LDIF, ldapadd/ldapsearch check). Deleted ext3/rquotad quota path; quotas now point to Lustre, XFS project quotas.
- Reworded checkpoint questions 4, 6 and 13 (NIS, migration, classic quotas) to match; exercise 4 reworked; book chapter references removed from body, exercises and checkpoint.
- Claims: "OpenLDAP no longer uses bdb/hdb, uses mdb, slapd.conf deprecated" is from general knowledge of OpenLDAP 2.5 and later, not re-fetched: unresolved against a cited source (noted in Sources). `enable_nss_slurm` semantics unchanged and still listed as unverified.
- Not done: Weka quota coverage the Opus note mentioned (no source to cite).

## 6.30 Facility basics
- Reduced the apcupsd.conf, EEPROM, UPSTYPE table, haltall and ambtemp.sh listings to prose (staged shutdown stages kept, matches ups_shutdown_sim.py). Removed "AI Factory vol. 21", "ADC book", "the books say" and the adopter anecdotes; removed the AALC error commentary (one plain expansion kept). Pointed to 9.11 as the deep dive. LaTeX removed from exercises and checkpoint. Dollar amounts written in words to keep `$` balanced.
- Checkpoint questions 7 and 9 reworded (UPSTYPE table and SNMP OIDs removed). Exercise 5 no longer asks for the OIDs.
- Claims: DGX H100 6 x 3.3 kW with 4+2 and 10.2 kW max, CFM = 3.16 x W / dT(F) (7,163 CFM for 81.6 kW and 36 F) already correct by recomputation (facility_calc_lab passes). DGX B200 figures are carried from the earlier chapter, not re-fetched.

## 3.1 Python core
- Replaced the REPL, IDLE, IDE, smartphone, clicking-icons and Appendix A material (about 350 lines of book tutorial) with a compact section on the REPL, scripts, importing, launching programs and debugging, using a `hostinfo.py` and `settings.py` example. Removed `LP` tags from exercises and questions, "In the book's example" and "(untested here)" comments. Python versions section trimmed.
- 3.12 to 3.17 coverage untouched. Not done: no separate appendix was created; the removed trivia was deleted instead of moved.

## 3.3 Idiomatic Python
- Replaced FrenchDeck/spades_high with a node inventory (`NodeInventory`, `Node`, `drain_order`) in `code/part03/python_idiomatic_data_model.py` and its lab (8 of 8 pass). Replaced dial codes, metro areas, symbols, Bus and BingoCage prose examples with ports, sites, racks and a round-robin picker. Removed all "Fluent Python"/"Learning Python"/Example N-N references and LaTeX.
- Not done: the Order/promotion discount engine, `StrKeyDict0` and the permutation examples remain in code and prose (book examples), because replacing them needs more code and lab rewrites.

## 3.11 Python under the hood
- Replaced the three Learning Python decorator case studies, the CardHolder, osconfeed and Example references with infrastructure naming. Replaced two long book-transcript sections (helper functions/metaclasses, decorating every method) with one compact section and a class-decorator plus metaclass sketch. Cut the metaclass catalogue (about 900 lines) to one section: definition, two-tree lookup rules, `FieldsMeta`, guidance. Added a pydantic validator case beside the FastAPI one. Checkpoint 11 and exercise 4 still match the retained two-tree content.
- Unresolved: pydantic version 2 `field_validator` sketch is from general knowledge, not checked against current pydantic docs. The `__slots__` memory figure was softened to "measure it".
- Neighbour note: 3.11 lab description still mentions `CardHolder` isolation; code file unchanged.

## 8.14 Air-gapped installation
- Rewrote 9.1 (bold Zone 1/2/3 lists) as three prose paragraphs and kept the staging-host matching rule. Shortened 9.2 to avoid repeating section 6. Fixed the missing section number (Interview angles is now 10). Removed manual section numbers and "(Appendix B/C)" from headings; "the manual" voice replaced by "NVIDIA"; first-person "My own choices" in Sources replaced.
- No watch-list rows. Version facts (Kubernetes 1.34.7, BCM 11.33) not re-verified.

## 8.16 Mission Control
- Moved the version-specific bugs (BCM 11.33 Run:ai wizard single-run issue, BCM 11.34.0 Dry Run defect) to a dated "Known issues and scope, as of November 2026" box; removed them from table, mistakes list and checkpoint 11 stem. First-person inferences ("my inference") rewritten as handbook inferences. "the manual's AJR example" made neutral.
- Scope re-verification: only a web search was run; results (Mission Control 2.3 documentation) support the Autonomous Recovery Engine with hardware recovery installed through `cm-mission-control-setup` and Slurm-integrated job recovery, and say platform support changes by release. Full pages were not read, so this is recorded in the chapter as search-level confirmation only. Unresolved: exact platform matrix per version.
