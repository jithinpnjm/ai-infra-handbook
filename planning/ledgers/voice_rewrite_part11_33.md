# Voice rewrite ledger: 11.33 NVKE in depth, part 2

File: `docs/part-11-gpu-kubernetes/33-nvke-in-depth-part-2-installation-nvkr-and-cluster-lifecycle.md`
Nothing committed. Other chapters untouched.

## Words

| Measure | Before | After | Change |
|---|---|---|---|
| rewrite_guard word count | 6485 | 9108 | +40.5 percent |
| Non-fence words (plain split) | 6576 | 9199 | +39.9 percent |

Note: the +40.5 percent figure is just above the 25 to 40 percent band. The growth came from explanation of each runbook and each table, not from new facts. Trimming it would violate rule 1 ("never trim"), so it stays. Flag for the owner if the band is strict.

## Gates

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. Residue 2 to 2.
- Literal backticked-span Counter check, HEAD vs worktree outside fences: lost {} and new {}. Several spans were added by mistake during drafting and then removed; two originally backticked spans (`tmux` and `clusterctl`, plus `k8s.io` and `/readyz`) were restored.
- Code fences: byte-identical before and after.
- `python3 tools/restore/chain_gate.py <file>`: 0.0 per 1000 words.
- `node tools/check_mermaid.mjs` over all docs: 776 diagrams, 0 failed.
- Checkpoints: 20 before, 20 after, text verbatim.
- Not run: `npm run build` (excluded by the task).

## What changed

- Front matter, heading text and order unchanged.
- Outcomes list converted to a plain paragraph.
- Each section opens with a situation: the pilot on day one, the change request, the security question, the failing machine, the tenant's ticket, the Monday cluster request.
- Explanation added for: tmux, the seed cluster, the StorageClass and CSI, DHCP reservation, BGP and VIP, the port table reading guide, the NVKR lanes and digests, the Definition, the iPXE flow, FDE and GRUB, cloud-init, the server-side dry run, the site spec, the trust domain, kind, Helm charts, NetworkPolicy, rendering, BMC and Redfish, CAPNICo kinds and stall reasons, annotations, break-glass, cordon and eviction, the upgrade rules as questions, the planner outputs read as three stories, shortfall and quorum arithmetic, NVSentinel, the runbook for delete.
- Bullets in section 7.3 rewritten as questions with answers. Facts unchanged.
- Kept verbatim: code, Mermaid, tables, Sources and review notes, Verification log, checkpoints.

## Needs source

- Section 3.1: the description of a QCOW2 image and an EFI imager (general background).
- Section 4.2: the description of a thumbprint of the TPM endorsement key (general background; the field name `tpmEkThumbprint` is in the source).
- Section 5.2: "The patch lets the Cluster API controllers authenticate with SPIFFE identities" is inferred from the script name `apply-capi-spiffe-exec-auth.sh`. The script was not read in this pass.
- Section 5.2: "authenticate to GitHub so the anonymous limit does not get in the way" is advice based on the 60-request figure in the source.
- Section 7.4: "a break-fix policy ... may involve the tenant's approval" is my suggestion, not from the source.
- Section 7.5: the reason deleting Cluster API objects by hand can strand machines is inference from the finalizer behaviour described in 11.32.
- Section 8: the lab reads "pending count" as nodes asked for but not present (reading of the metric name).

## Unresolved

- Exercise 3 worked solution keeps the original wording "since 1.34 is not below 1.37 minus 3". It is correct but awkward. Left as-is because worked solutions are part of the original text.
- The original chapter references `c32_*` code files. They were not opened in this pass.
- EXTERNAL_EDITS.md was not edited, per the task instruction.
- Word growth is above the 40 percent edge by 0.5 points (see Words note).
