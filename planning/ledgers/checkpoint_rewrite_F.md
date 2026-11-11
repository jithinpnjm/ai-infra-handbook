# Checkpoint rewrite report: F (Part 18, chapters 18.1 to 18.7)

All seven chapters: 20 questions before, 20 after. All 20 were replaced in each chapter (none kept: the old ones were definition or "most common failure" questions). No question dropped for lack of support. chain_gate 0.0 per 1000 words on all seven. Mix per chapter: 6 scenario, 5 mechanism, 4 trade-off, 3 numbers, 2 debugging-order.

Errors noticed elsewhere (not fixed):
- 18.1: sample FW/asset counts are placeholders only; Mitigated example threat dated 2024 (fine). Lab dates use 2024.
- 18.2: Mermaid flowchart in 5.1 uses node V twice (Vendor release and Vendor next release). "Five seconds" target in 8.8 versus "30 seconds" limit is loosely worded. ipmitool "attestation verify" is flagged illustrative in the chapter.
- 18.3: Gatekeeper policy calls undefined cosign_verify, Kyverno rule only checks a label (both already admitted in the chapter text). Lab step 8.3 installs Gatekeeper but the policy is a skeleton.
- 18.4: Pod Security labels target team-data-science while the ValidatingAdmissionPolicy binding targets mlops. Lab step 2 references code/part18/rbac_rolebinding.yaml, not shown in chapter. Anti-pattern rows 4.3 "No policyTypes allows all traffic" and "Empty podSelector with allow" are loosely stated.
- 18.5: Cost block is internally inconsistent: 50-200 nodes x 8 GPUs x $3-5/hour is about $1.2k to $8k per hour, not the stated $10-30k. MIG layout lists 1+1+2+4 = 8 instances but says 7. Pod example requests mig-1g.5gb while the A100 80GB layout lists 1g.10gb. Section 4.1 says memory is not shared between tenants under time-slicing, but the 4.2 table says memory isolation is None. IOMMU "backing store: TPM" is odd.
- 18.6: Verifier sketch checks only 3 of the 5 chain links. Section numbering of "How it fails" is 6 (others use 7). doca_service list is illustrative.
- 18.7: Lab step 5 writes `gsutil retention set gs://audit-log-bucket 90d`, argument order reversed versus 3.3 (`90d` then bucket). Section 4.1 lists signed and replicated as properties but the code only appends and hashes. 7.4 says object lock while GCS calls it retention policy and Bucket Lock.
