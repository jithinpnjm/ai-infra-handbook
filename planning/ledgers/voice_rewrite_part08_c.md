# Voice rewrite ledger: Part 8, chapters 8.7 to 8.9 (run c)

Scope: `docs/part-08-bcm/07-power-bmc-and-hardware-management-in-bcm.md`, `08-workload-managers-under-bcm-slurm-setup.md`, `09-kubernetes-under-bcm-deployment-and-gpu-enablement.md`. Front matter, headings, tables, Mermaid, code blocks, checkpoints (20 each) and Sources and review notes are unchanged. Checkpoint and Sources text was spliced byte-for-byte from HEAD. `EXTERNAL_EDITS.md` was not edited (per instruction).

## Words (wc -w, whole file)

| File | Before | After | Growth | Guard body words (before to after) |
|---|---|---|---|---|
| 8.7 | 6302 | 8293 | +31.6 percent | 6094 to 8085 (+32.7 percent) |
| 8.8 | 6365 | 8144 | +28.0 percent | 6161 to 7940 (+28.9 percent) |
| 8.9 | 7844 | 10319 | +31.5 percent | 7634 to 10109 (+32.4 percent) |

## Gates (run after the last edit)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`:
  - 8.7: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. One new span (`10.148`) was reworded to plain text.
  - 8.8: 0 hard failures. New numbers 0, lost numbers 0, new code spans 0, lost 0. One new span (`$(id -u)`) was reworded to plain text.
  - 8.9: 0 hard failures. New numbers 0, lost numbers 0. The guard reports new code spans 3 and lost 2 (`Git`, `Helm`, `OCI` appear as new; `, ` and `. The wizard can register ` as lost). This is a pairing artifact of the guard's own regex on the original line "register `Git`, `Helm` or `OCI`". An exact comparison (fenced blocks removed, all spans as a set and as counts) shows no added and no lost spans. Every new span was reworded to plain text or removed.
- Exact span check (set and count, fenced blocks removed) on all three: no new spans, no lost spans, except the 8.9 artifact described above.
- `python3 tools/restore/chain_gate.py <file>`:
  - 8.7: 0.7. The body has 0 semicolon chains. The remaining hits are in the locked Sources tail (checkpoint and Sources text is unchanged from HEAD).
  - 8.8: 0.2.
  - 8.9: 0.2.
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed". The checker covers the repo, not only these three files.
- `npm run build`: not run (the lead said no npm build).
- Numbers: every number in the new text already existed in the original. Guard "new numbers" is 0 for all three.

## Honest status

- Each chapter keeps the status row (locked table, "cluster commands **untested** on live BCM").
- One plain sentence above the exercises in each chapter:
  - 8.7: "The commands in this chapter were not run on a live BCM system, so treat them as practice on paper or in the lab."
  - 8.8: "The cluster steps were not run on a live system, so treat the commands as practice."
  - 8.9: "The steps in this chapter were not run on a live cluster, so treat them as practice."
- Removed from body: "(untested)" in 8.7 exercise 2, 8.8 exercise 3 and the 8.8 section 10 sentence about the manual's example, and "not yet tested" in 8.9 exercise 4.

## Residue and voice fixes

- 8.8 section 1: "in the manual I read" changed to "in the manual's version list".
- Prerequisites outcome lists ("you should be able to" bullets) in all three rewritten as plain paragraphs. Headings kept.
- Section openers: each body section now opens with a situation (a dead node at 3 a.m., a rack after maintenance, a GPU job with no GPUs, a hung node, a Friday upgrade, an edge site on a slow link). Section 8.9 section 3 and 8.9 section 4 opened with a statement; both now open with a situation.
- Exercises: same counts (6, 6, 6). Multi-ask exercises split into short sentences, one question each. Numbers and commands are unchanged. 8.9 exercise 3 keeps its two fixes and the trade-off of each.
- Interview angles: same five bullets per chapter. Only the explanations around the answers were added.
- 8.9 section 2: "Run them in this order, because each check builds on the one before it" replaces an unsupported claim.
- Unsupported sentences removed during the pass: a claim that overlapping ranges are the most common cause of networking trouble (8.9 section 3.1), a claim that a password or user-ID mismatch causes BMC authentication failures (8.7 section 4), and a claim about why NetQ needs the CMDaemon port move (8.9 section 5).
- No "I", "my", "the book says", "Volume N", "untested here" or "(untested)" remains in the body of the three chapters.

## Needs source (general explanations added; no new vendor facts)

These are general definitions and reasoning added around the manual's facts. Check them against a reference before publication.

8.7:
- BMC, BIOS, IPMI, PDU, DHCP, DC and AC power, Wake-on-LAN and MAC address, inrush current, thread pool, PSU, rack-scale systems, SHA-256 fingerprint and hash, alias interface, POST, COM1 and COM2, VT100 and ANSI, minicom, conman, JSON, PXE, DOS image, out-of-band access, microcontroller, NVL72 as a rack-scale design, MQTT, transformer and breaker, standby rail, leak sensor.
- Redfish described as a standard, web-based interface; NVLink as NVIDIA's GPU interconnect; MPS-like descriptions are in 8.8 only.
- Reasons added: the PDU outlet cannot go dark while a twin node needs it; power on in batches so each wave is counted before it runs; redirection during POST helps watch start-up checks; the identify light workflow; "write down why you disabled leak detection".

8.8:
- PAM, prolog and epilog, `chroot`, SPANK, Squashfs, NCCL, cgroup description, job step, slot, munge, MPS, GRES, `sbcast`, Wh, PID, HA-related descriptions for the `slurmd` and `slurmctld` roles.
- Reasons added: a shared cache race when two nodes unpack the same image; cloning a category first so new nodes start from the same settings; why `usernodelogin` is a category setting; why the secondary head should not run the tool while passive; why prejob failures need a person before undrain.
- Scenario openers (2 a.m. head failure; overnight stuck queue; login node missing from submit list) are invented teaching situations, not reported incidents.

8.9:
- Kubernetes, kubelet, scheduler, control plane, static pods, kubeadm, containerd, etcd quorum, idempotent, MTU, Helm, Harbor pull secrets, StorageClass, Typha, Kyverno, DaemonSet, taint and toleration, HIP, NUMA and inter-socket link, CRD, sidecar, base64 as encoding, MinIO, NIM, Argo CD, NetQ, Shorewall, SNI, ARP failover, man-in-the-middle, NVIDIA AI Enterprise certified (described as "tested with the stack"), OnDelete strategy, DNS and firewall pre-flight description.
- Reasons added: running etcd outside the cluster keeps the state available while Kubernetes is rebuilt; a moved control plane costs rework; a self-signed CA does not scale because every user must trust it; a Kyverno engine with no policies protects nothing; a bad pod CIDR is hard to grow later.
- Part 5 terms: pod, node, control plane, kubelet, containerd and Gateway wording follow the common terms used in Part 5. The Part 5 chapters were not re-read line by line for this run.

## Unresolved

1. 8.8 version list is internally inconsistent in the original: section 1 gives Slurm 25.05 and 25.11, while section 10 and checkpoint 1 give 25.05, 25.11 and 26.05. Kept as in the original; owner to decide the correct list.
2. 8.7 chain gate is 0.7 because of semicolon chains in the locked Sources tail. The body is at 0. Not changed because the tail is locked.
3. 8.9 guard span artifact (see gates). Exact comparison is clean.
4. Guard "untested" check: the status row keeps the word "untested" (locked table). The body's honest sentence is "not run". Both are intended.
5. Not run: `npm run build` (per the lead's instruction).
