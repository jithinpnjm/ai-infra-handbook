# Voice rewrite, Part 6 chapters 6.14, 6.15, 6.16 (batch f)

Scope: docs/part-06-hpc-slurm/14-slurm-operations-prolog-epilog-health-checks-drain-reason-codes-troubl.md, 15-slurm-high-availability-upgrades-and-scaling.md, 16-slurm-on-kubernetes-slinky-and-soperator.md. Uncommitted. Only these three files were edited. EXTERNAL_EDITS.md was not edited (lead instruction). Front matter, headings, tables, Mermaid blocks, code blocks, checkpoint questions and answers, and Sources sections are unchanged.

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 6.14 Slurm operations | 8097 | 10698 | +32.1% |
| 6.15 Slurm HA, upgrades and scaling | 6482 | 9119 | +40.7% |
| 6.16 Slurm on Kubernetes | 5849 | 7541 | +28.9% |

## Gates (run from the repo root, output seen)

`python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
- 14: 0 hard failures; new numbers 0; lost numbers 0; words 7697 to 10298 (guard count, prose only). New code spans 11, lost 7. The 7 "lost" are pairing artifacts of the regex. A set diff of inline code spans (HEAD vs worktree, checkpoint and Sources included) shows 0 lost. Residue 9 to 8: the 5 remaining "(untested here)" tags sit inside the reservation code block (see Unresolved).
- 15: 0 hard failures; new numbers 0; lost numbers 0; code spans new 0, lost 0; residue 0 to 0.
- 16: 0 hard failures; new numbers 0; lost numbers 0; code spans new 0, lost 0; residue 0 to 0.

`python3 tools/restore/chain_gate.py <file>`:
- 14: 0.0 per 1000 words
- 15: 0.0 per 1000 words
- 16: 0.1 per 1000 words

`node tools/check_mermaid.mjs` and `npm run build`: not run (lead instruction: no npm build or full Mermaid). Mermaid blocks are byte-identical to HEAD.

## What changed

- Every section opens with a situation: a job that hangs on one bad GPU, a shared node where the last job left temp files, a scheduler that dies on a Monday, a jail edit that every node sees at once, and so on.
- "Prerequisites and outcomes" in all three chapters: the bullet lists of "you will be able to" items became one plain paragraph per chapter. The heading is kept.
- Exercises: 6.14 six, 6.15 six, 6.16 twelve. Counts unchanged. Multi-part items were split into one question per sentence, and nested (a)(b) lists were turned into sentences. 6.16 exercise 7 to 9 are single items that carry several plain questions.
- Lab: the step lists in all three chapters keep the same count (6.14: 8 steps, 6.15: 7 steps, 6.16: 5 steps) and the same commands.
- Honest status: each status row is unchanged (it still says "untested" or "not run"). One plain sentence sits above each lab: "These steps were not run..." (6.15, 6.16) and "The commands below were not run on a live cluster" (6.14, reservation block).
- The "(untested here)" tag was removed from prose in 6.14 (the reservation paragraph). The Sources sections were not touched.
- Bullets in 6.14 section 5 (sacct and sreport samples) each open with a question.
- Bold: at most one bold idea per section in new prose. Existing bold in the status rows and the 6.1 table and the 6.16 slurm-operator rule sentence was kept as in the original.
- No exclamation marks, no raw `<` or `{` in prose.
- Checkpoint and Sources were copied from HEAD byte-for-byte.

## Needs source (explanation added, not in the original text)

6.14:
- LBNL is Lawrence Berkeley National Laboratory, which publishes NHC.
- DCGM is NVIDIA's Data Center GPU Manager.
- An Xid is the error code the NVIDIA driver writes to the kernel log.
- `|| true` treats a failed command as a success. (Shell behaviour, general knowledge.)
- A cgroup lets Slurm track every process a job started.
- Burn-in is a hard run that brings early hardware failures to the surface.
- The drain-or-down rule of thumb in section 3 (drain when running work can finish safely).
- Munge rejects messages whose timestamps are too far apart.
- An inode is a file record; running out stops new files.
- TRES is Slurm's name for a trackable resource.
- A stub is a fake program that returns fixed output.

6.15:
- STONITH expansion ("shoot the other node in the head") and the lease description.
- Galera is a multi-primary replication layer for MySQL-family databases.
- RAID as the reason for a reliable state file system (wording from the man page is kept; the RAID explanation is ours).
- SRV record definition (DNS service discovery).
- EPEL is Extra Packages for Enterprise Linux.
- InnoDB as the MySQL storage engine that keeps working data in memory.
- SYN cookies as a kernel method to absorb a connection flood.
- ulimit as the per-process resource limit.
- TLS as the transport encryption for the REST API.
- JWT expansion (JSON Web Token).
- Wall time versus CPU time (general Slurm usage).

6.16:
- GitOps (cluster desired state in Git, reconciled by a tool).
- Gang scheduling (all parts of a job start together or not at all).
- Neocloud (cloud provider built around GPU capacity).
- CNI (container network plug-in).
- Helm (Kubernetes package manager) and Terraform (infrastructure as code).
- Kubebuilder, ConfigMap and Secret definitions.
- SSSD as the Linux identity bridge to LDAP or Active Directory.
- Multus as a meta-plugin that gives a pod more than one network interface.
- PodDisruptionBudget and finalizer definitions.
- emptyDir with `medium: Memory` as a RAM-backed scratch volume.
- NUMA definition; checkpoint definition; namespace definition.
- Front-end and scheduler split in section 4 (Run:ai, Kueue, Volcano) is kept from the original wording.

## Unresolved

- 6.14 reservation code block: the five `# (untested here) — N.` comment lines are inside a code block. The guard requires code blocks to stay byte-identical, so the tags were left in place. Removing them is a one-line-per-comment change if you want the reader text clean; it needs an owner decision because it edits code.
- 6.14 Sources section still says "(`untested here`)" in the last bullet, and 6.15 and 6.16 Sources do the same. Sources were out of scope.
- 6.15 length: +40.7 percent, a little over the 40 percent guide. It was trimmed once; the extra is explanation, not padding. Trim further if you want the band strict.
- 6.15 section 7.1 keeps original claims that have no source in the chapter: "In nine out of ten control-plane slowdowns..." and the `MinJobAge` 300 s to 60 s suggestion. Kept as written, not checked.
- 6.15 "Each release is supported for about 18 months" kept as written, not checked.
- 6.16 section 4 and the rest of the chapter keep the original "general knowledge, unverified" framing; no new facts about SUNK were added.
- Build and Mermaid were not run (lead instruction).
