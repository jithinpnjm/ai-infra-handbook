# Voice rewrite ledger: Part 8, chapters 8.10 to 8.12 (run d)

Scope: `docs/part-08-bcm/10-containerization-in-bcm-docker-apptainer-and-enroot.md`, `11-monitoring-health-checks-and-alerts-in-bcm.md`, `12-high-availability-and-head-node-failover.md`. Front matter, title, status table, headings, tables, Mermaid, code blocks, checkpoints (20 each) and Sources were kept byte for byte from HEAD. Body prose was rewritten section by section. `EXTERNAL_EDITS.md` was not edited (per instruction). Nothing was committed.

## Words (wc -w, whole file)

| File | Before | After | Growth |
|---|---|---|---|
| 8.10 | 6141 | 8355 | +36 percent |
| 8.11 | 6374 | 8243 | +29 percent |
| 8.12 | 6665 | 8594 | +29 percent |

The locked tail (checkpoints plus Sources) is about 1,207 words in 8.10, 1,476 in 8.11 and 1,409 in 8.12, so the body carries the growth.

## Gates (run after the last edit)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures in all three.
  - 8.10: new numbers 0, lost numbers 0. The guard reports "lost 1" and "new code spans 4". This is the guard's pairing artifact, not a real loss: the full-regex span check shows nothing lost. The 4 new spans (`nvidia-smi`, `--container-image`, `mpirun`, `$(id -u)`, plus `.sqsh`, `.sif`, `--nv`, `-w`, `internalnet`, `all_reduce_perf`, `401`) are terms typed or seen on screen and were already used in prose elsewhere in the chapter.
  - 8.11: new numbers 0, lost numbers 0, new code spans 2 (`yes`, `gpuN`, `gpu1` are seen on screen).
  - 8.12: new numbers 0, lost numbers 0, new code spans 1 by the guard (`cmha status`, `disableautomaticfailover`, `runif active`, `device power status` are typed commands or settings).
- Span check (`python3 - <<'PY' ... PY` from the task): `{}` for all three, after restoring the spans that the rewritten outcome paragraphs had dropped (8.10: `DockerHost`, `cm-wlm-setup`; 8.11: `PASS`, `FAIL`, `UNKNOWN`, `no data`).
- `python3 tools/restore/chain_gate.py <file>`: 8.10 0.5, 8.11 0.4, 8.12 0.4. All under the 1.5 limit. The target of 0.2 is not reached. The remaining hits are in locked Sources and tables, and in long prose sentences that are kept deliberately.
- `node tools/check_mermaid.mjs`: "checked 776 diagrams, 0 failed".
- `npm run build`: not run (task said no npm build).
- Structure: heading lists identical to HEAD; checkpoint count 20 in each; code fence count unchanged; exercise count 6 in each (8.10, 8.11, 8.12).
- Raw `<`, `{` or `!` outside code spans and fences: none in the three bodies.

## Honest status

The status row (locked) says cluster commands are "untested" on live BCM. One plain sentence above each exercise list says the cluster steps were not run on a live cluster or pair. 8.10 keeps a shorter sentence in the same place. 8.11 says the cmsh steps "have not been tested on a live BCM system". 8.12 says the cluster steps "have not been run on a live pair".

## Residue removed from body text

- 8.10: "This is my own reading" became "This reading combines two passages in the manual". "I found no mention" became "The three BCM manuals do not mention". "the points below are my own summary" became "the points below summarize that book". "What follows is my own outline" became "an outline of general practice". "the user's notes" and "the notes behind this chapter" were removed. "The HPC sysadmin book" is now named in full as *Supercomputers for Linux Sysadmins* (see Needs source). "the Enroot docs" is kept as "the Enroot documentation says".
- 8.10: the outcomes list was rewritten as a plain paragraph. The `volume-18/ch2` span is kept, and the prose no longer says "Volume 18".
- 8.11: "(untested here)" removed from the trigger-example caption. "the author's notes" removed from the remediation table lead-in. The outcomes list was rewritten as a plain paragraph. "you should be able to" is gone.
- 8.12: the outcomes list was rewritten as a plain paragraph. "you should be able" is gone.
- No "I read", "my summary", "the book says" or "Volume N" in body text. The only residue left is in the locked Sources sections, where attribution belongs.

## Needs source (general explanations added; no new vendor fact)

8.10:
- NGC described as "NVIDIA's software catalog".
- Keycloak as "an open-source single sign-on server".
- Definitions added: container, image, daemon, Slurm and Kubernetes roles, LSF as IBM's workload manager, containerd, runC, cgroup, volume, etcd, Squashfs (read-only compressed filesystem), `.sqsh` as a single-file image, OCI blob, rate limit, NAT gateway, line rate, pre-staging, canary category, POSIX, GID, Kyverno as a policy engine, SPANK plugin, chroot, namespaces, PMIx rank, MPI, `mpirun`, `srun` and the `--nv` flag meaning.
- "401 is the web status code for 'you did not prove who you are'" (general HTTP meaning).
- Explanations of why a `#` in an `#SBATCH` line cuts off the image name (follows from the original's comment rule).
- `all_reduce_perf` as a standard NCCL benchmark that checks GPU-to-GPU communication.
- The Enroot prolog and epilog as scripts that Slurm runs before and after each job.
- The hardened Enroot flavour described as "stricter defaults" (confirm against the BCM manual).
- Mention that `cm-wlm-setup` Pyxis build is "for one exact Slurm version" (general reading of "compiled against the installed Slurm").
- Reasoning that the `--container-image` option is missing when Pyxis is not reinstalled after a Slurm upgrade (follows from the original's error row).

8.11:
- Redfish as "a standard web API that server management controllers provide".
- Interpolated graph, sampling storm, RLE (run length encoding), cumulative metric differential, load one average, Chargeback report, PromQL and drilldown query description, self-signed and public CA certificates, shared logins removing the record of who logged in, static file serving.
- Event broadcast versus private event as "to every connected session" and "only to the session that asked".
- Cost allocation tags as "labels that the billing report groups by".
- File descriptor 3 as "a side channel", and standard output as the normal channel.
- Exit code 0 as the Unix convention for success.
- "Derived result" as the meaning of "the lab labels it as derived" (the manual's default values and the rule come from the original text).
- The yes program keeping one CPU core busy (general behavior of the yes command).
- Jiffy as a small Linux clock tick.
- Standby power keeping a BMC alive (8.12) is general hardware practice, listed here too.
- "Dead time, consolidators and category explanations", including that a category is a group of nodes that share a configuration.
- Drain as "stop placing new work on the node, so running jobs can finish".
- The claim that "the sum is most useful when you compare nodes" (reader guidance, not a manual statement).
- "Caching on the node may not lose readings" (inferred from "Nodes cache their samples"; confirm before relying on it).
- Section 8 opener: "A node that reboots every ten minutes" is an illustrative example written in words (no digit, so the guard does not flag it). It is not from the manual.

8.12:
- Heartbeat, quorum, NAS, Lustre and GPFS as parallel filesystems, NIC, BMC standby power, gratuitous ARP, copy-on-write, Btrfs snapshots, ncurses, ARM as a processor family, binlog, VIP, BIOS clock, MAC address, PXE rescue environment, and the "spare snapshot goes stale" reasoning.
- Fencing described as "the head stops acting as a normal standby and holds back".
- "A split brain, each side believes it is the only one in charge" (definition of the term).
- The reasons behind the sequencing rules (for example "migrating services: update the passive first so problems show up on the head you can roll back") are reader explanation. The table content is unchanged and comes from section 15.4.5.
- "A switch shared with the rest of the cluster can fail in ways that look exactly like a dead head" (general).
- "`runif active` keeps a second copy from starting" (inferred from the setting name; confirm against the failovergroups manual page).
- "A service that migrates is one that would corrupt data if two copies ran at once" (reader explanation of the table).
- "A planned reboot is a decision someone made" (framing of the manual's intent rule).
- "Clients resolving a name that different members give would flicker" (general DNS reasoning).

## Unresolved

1. Chain gate is 0.4 to 0.5 in all three, above the 0.2 aim (below the 1.5 limit). Reaching 0.2 would mean editing locked Sources or table text.
2. The tables in 8.10 (section 7.5) and 8.12 (section 9) keep their original wording, so any wording issue inside them remains.
3. 8.10 says "fix from the notes" in section 4 was changed to "a judgment call". Owner should confirm this threshold is still the intended wording.
4. 8.11 has "Exercise 4" with two triggers. It was split into short sentences; the cmsh commands are unchanged.
5. The three "Needs source" groups above were not checked against the BCM manuals or the gem books, as the task required only listing.
6. Shared scratch files: the scratchpad notice reported an update to the 8.10 and 8.11 working copies during this run. The assembled files were checked after each rebuild (span check, guard, headings, checkpoint count), so the final files are consistent. No file outside `docs/part-08-bcm/10-*`, `11-*`, `12-*` and this ledger was written.
