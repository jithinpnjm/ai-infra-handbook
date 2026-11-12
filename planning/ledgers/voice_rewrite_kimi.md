# Voice rewrite ledger (Kimi)

Scope: Part 1 beginner-readability pass requested by the author: make chapters read like a
human teacher wrote them without losing any content. Prior attempts (Qwen, Nemotron) cut
content; this pass preserves every fact, number, command, table, diagram, exercise and
question, and only reshapes the prose.

**Author guidance (2026-11-12):** if the warm teacher voice needs more words, use them.
There is no word-count cap on voice rewrites. Zero content loss remains the only hard
content constraint.

## 1.1 The Linux big picture (2026-11-12)

- Rewrote all narrative prose in a human teacher voice: sections open on concrete
  situations (Monday-morning incident, four teams sharing a GPU server), terms are
  defined in plain words at first use, one idea per paragraph.
- Extended existing analogies instead of adding new facts: office building (kernel =
  property manager, system call = front desk) reused in user-space and system-call
  sections; paused board game for "state"; upstream river for the RHEL/Fedora/CentOS
  lineage.
- Removed robotic filler sentences in checkpoint answers (Q5, Q6, Q7, Q8, Q15, Q17);
  de-duplicated the DGX OS / Ubuntu LTS repetition in Q15; turned the Part C item 7
  answer giveaway into a "Hint:".
- Untouched on purpose: all Mermaid diagrams, code blocks, tables, the 6 exercises,
  lab commands, `(untested here)` markers, Sources section (provenance).

Checks after the rewrite:

- `tools/loss_check.py` vs `git show 0f258b4:<file>`: **0 terms lost (of 36), 0 numbers
  lost (of 53), 0 source citations lost**.
- `tools/validate_chapter.py 1.1`: **VERDICT: OK**, 12/12 PASS; readability all `ok`
  (avg sentence 15.2 words, 3.4 code terms/100 words, 1.6 numbers/100 words, 2.0% long
  sentences, 0.1 parentheses/sentence).
- `tools/restore/chain_gate.py`: 0.6 semicolon chains per 1000 words (limit 1.5).
- 20 `<details>/<summary>` checkpoint questions intact; no exclamation marks in prose.
- Words: 9,933 -> 10,907 (validator count). `planning/STATUS.md` updated.

Claims confirmed/corrected with sources: none needed (no facts changed, none added,
none removed). Claims not checkable: none. Neighbouring chapters noticed but not fixed:
none (Part 1 chapters 1.2 onward have the same mechanical tone; they are the next
candidates after the author approves this voice).

## 1.2 The command line (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017` using the
  1.1 gold-standard prompt; Kimi supervised and independently re-ran all gates.
- Voice treatment: overnight-failure opening, terminal/shell/command learners' confusion
  story, per-section concrete openers; robotic filler removed. Structure untouched.
- Supervision verdict: independent `loss_check` 0 of 61 terms / 0 of 44 numbers / 0 sources
  lost; `validate_chapter.py 1.2` VERDICT: OK (avg sentence 13.1 words); lab 26/26 pass;
  20 checkpoint questions intact; chain gate 0.1/1000. One WARN stands: code-formatted
  terms 8.1 per 100 words (was 8.9), inherent to a shell-command teaching chapter; the
  plan forbids stripping real command backticks to game this metric. Accepted.
- Words: 12,134 -> 13,305 (validator count). `planning/STATUS.md` updated.

## 1.5 Working remotely (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a direct prose read.
- Voice treatment: bastion/login/compute node pinned down in plain words, first-connection
  fingerprint prompt as the section 1 opener, host-key warning taught as "a question to
  answer, not an error to click past".
- Supervision verdict: `loss_check` 0 of 43 terms / 0 of 65 numbers / 0 sources lost;
  `validate_chapter.py 1.5` VERDICT: OK (avg sentence 13.2 words); chain gate 0.0/1000;
  20 questions; lab 25/25. Code-density WARN 5.8 (was 6.2) stands; command chapter,
  accepted per policy.
- Words: 7,823 -> 8,608 (validator count). `planning/STATUS.md` updated.

## 1.3 Files and the directory hierarchy (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a direct prose read.
- Voice treatment: opens on three picture-puzzles (full disk with free space, dangling
  `latest` checkpoint link, 10-minute directory listing); sections given terminal-story
  openers; inode taught as a record card, hard link as a second label, symlink as a note;
  illustrated only, no facts added.
- Supervision verdict: `loss_check` 0 of 98 terms / 0 of 57 numbers / 0 sources lost;
  `validate_chapter.py 1.3` VERDICT: OK (avg sentence 13.3 words); chain gate 0.0/1000;
  20 questions; lab 20/20. Code-density WARN 7.6 (was 8.4) stands; command chapter,
  accepted per policy.
- Words: 8,328 -> 10,080 (validator count). `planning/STATUS.md` updated.

## 1.4 Text-processing essentials (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a direct prose read.
- Voice treatment: 3 a.m. incident opening told as a scene, regex taught with a
  dress-pattern analogy, BRE/ERE given a decision rule, seven failure stories made
  symptom-first.
- Supervision verdict: `loss_check` 0 of 21 terms / 0 of 71 numbers / 0 sources lost;
  `validate_chapter.py 1.4` VERDICT: OK; chain gate 0.0/1000; 20 questions; lab 25/25.
  Code-density WARN 8.9 (was 10.1) stands; the most command-dense chapter so far,
  accepted per policy.
- Words: 6,636 -> 7,168 (validator count). `planning/STATUS.md` updated.
- PRE-EXISTING errors noticed, NOT fixed (out of voice scope; fix in a content pass with
  the author's ok): "The fifth example is worth memorising" describes the sixth command;
  "Three small improvements are worth adopting right away" actually introduces four items.

## 1.6 Users, groups, permissions (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/zai-org/GLM-5.3-Flash`; Kimi supervised with
  independent gate runs and a direct prose read (users/groups, setuid, cluster identity).
- Voice treatment: "first week on a cluster team" opening with five picture-failures;
  alice UID 1042 vs 1043 mismatch story kept as the heart of section 8; setuid danger
  paragraphs de-duplicated with all claims kept; permission non-cumulative check order and
  ACL mask explained in plain words.
- Supervision verdict: `loss_check` 0 of 74 terms / 0 of 91 numbers / 0 sources lost;
  chain gate 0.5/1000; 20 questions; lab 25/25. Code-density WARN 6.7 accepted per policy.
- Coverage bookkeeping fix (pre-existing, verified identical on HEAD): `validate_chapter`
  printed `REVIEW: relevant books uncited` for `terraform-up-and-running-3rd-edition`
  (spurious heading match). Recorded it as read/not-relevant in `planning/ledgers/1-06.md`
  Corpus search; validator now prints VERDICT: OK. Also fixed earlier stale word count in
  STATUS (11,924 -> 13,146 validates the rework pass that landed before this rewrite).
- Words: 13,146 -> 13,613 (validator count). `planning/STATUS.md` updated.

## 1.20 Build a container by hand (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a direct prose read.
- Voice treatment: lab steps framed by what the reader will see ("a process looks around
  and finds a smaller world"); chroot/namespace/cgroup/capability defined at first use;
  closes "a different / is not the same thing as a container".
- Supervision verdict: `loss_check` 0 of 22 terms / 0 of 51 numbers / 0 sources lost;
  chain gate 0.0/1000; 20 questions; lab 15/15. Code-density WARN 9.8 (was 11.6)
  accepted per policy.
- Coverage bookkeeping fix (pre-existing, verified identical on HEAD): recorded
  `network-programmability-and-automation-2nd-edition` Ch 10/14 as read/not-relevant in
  `planning/ledgers/1-20.md`; validator now prints VERDICT: OK.
- Words: 3,678 -> 4,375 (validator count). `planning/STATUS.md` updated.

## 1.30 Network file sharing and remote access (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a direct prose read.
- Voice treatment: delta transfer explained as blocks in plain words; X11 client/server
  direction given the memorable correction "the server serves the screen, not the data";
  weekend-dataset and dial-up GUI openers.
- Supervision verdict: `loss_check` 0 of 61 terms / 0 of 47 numbers / 0 sources lost;
  `validate_chapter.py 1.30` VERDICT: OK natively; chain gate 0.2/1000; 20 questions;
  lab 15/15. Code-density WARN 5.9 accepted per policy.
- Words: 8,639 (stale in STATUS) -> 11,757 (validator count). `planning/STATUS.md`
  updated.

## 1.15 systemd (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: every daemon section gets an incident opener (restarting service,
  wrong node, Sunday trim); target taught as "a flag on a hill"; unit files read as
  three conversations; enable/start/mask trio given lead sentences.
- Supervision verdict: `loss_check` 0 of 449 terms / 0 of 82 numbers / 0 sources lost;
  `validate_chapter.py 1.15` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 21/21.
  Code-density WARN 11.0 (was 11.7) stands; heaviest command reference so far, accepted.
- Left as-is (pre-existing): a `...` fragment inside the target `Wants=` sentence;
  author may fix in a content pass.
- Words: 10,524 -> 12,941 (validator count). `planning/STATUS.md` updated.

## 1.27 Cloud computing internals (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs and a baseline-diff spot check.
- Voice treatment: crawling-cloud-job opener, kitchen analogy for IaaS/PaaS/SaaS,
  apartment-building analogy for multitenancy; readability all `ok` (3.3 code terms/100w).
- BONUS REPAIR, verified against `git show HEAD:` and `git show 0f258b4:`: the committed
  file had silently dropped the baseline's cloud stage years (2006, 2015, 2017, 2019);
  the agent restored them in the baseline's own wording. loss_check now 0/52/0/63.
- Supervision verdict: VERDICT: OK natively; chain gate 0.1/1000; 20 questions; lab 14/14.
- Words: 8,630 (stale in STATUS) -> 10,875 (validator count). `planning/STATUS.md` updated.

## 1.9 Shell scripting (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: deploy-script-removes-wrong-directory and backup-copies-nothing-for-
  months stories drive quoting and exit codes; strict mode taught as fail-loudly; all
  39 protected blocks byte-identical.
- Supervision verdict: `loss_check` 0 of 38 terms / 0 of 85 numbers / 0 sources lost;
  `validate_chapter.py 1.9` VERDICT: OK; chain gate 0.0/1000; 20 questions; lab 24/24.
  Code-density WARN 10.0 (was 10.8) accepted per policy.
- Words: 11,237 -> 11,627 (validator count). `planning/STATUS.md` updated.

## 1.29 Remote administration reference (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: 2 a.m. locked-out scene; hardened-sshd-locks-out-the-admin story;
  every reference table kept untouched, each with a human doorway.
- Supervision verdict: `loss_check` 0 of 85 terms / 0 of 59 numbers / 0 sources lost;
  `validate_chapter.py 1.29` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 15/15.
- TWO FIXES BY SUPERVISOR during review: corrected an agent-introduced wrong cross-
  reference (`as section 9 shows` -> `section 10` for IPMI), and corrected a pre-existing
  Sources line `16 passed` -> `15 passed` to match actual lab output.
- Words: 8,876 -> 10,350 (validator count). `planning/STATUS.md` updated.

## 1.13 LVM, RAID and NVMe (2026-11-12, GLM failover + supervision)

- Drafted by `general` subagent on `nebius/zai-org/GLM-5.3-Flash` after the DeepSeek
  quota death (its run left the file untouched); Kimi supervised with independent gates.
- Voice treatment: Friday-evening opener; RAID levels taught with one question (how does
  the array survive a dead drive, and what does that cost?) before the table; NVMe-oF
  terms (target/host/NQN) defined in plain words; PV/VG/LV at first use.
- Supervision verdict: `loss_check` 0 of 115 terms / 0 of 88 numbers / 0 sources lost;
  `validate_chapter.py 1.13` VERDICT: OK natively (agent ran the original-file
  comparison as instructed); chain gate 0.2/1000; 20 questions; lab 21/21.
- Words: 11,253 -> 13,279 (validator count). `planning/STATUS.md` updated.

## 1.12 Disks, partitions and filesystems (2026-11-12, GLM failover + supervision)

- DeepSeek-Flash run hit the provider token quota and left partial edits; supervisor
  reverted the file and re-dispatched on `nebius/zai-org/GLM-5.3-Flash`.
- Voice treatment: new-NVMe drive, mkfs-on-wrong-device moment, power cut; partitions
  and UUID/label/inode defined at first use; British spellings aligned to house style.
- Supervision verdict: `loss_check` 0 of 119 terms / 0 of 113 numbers / 0 sources lost;
  `validate_chapter.py 1.12` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 21/21.
  Code-density WARN 6.5 (was 6.7) accepted per policy.
- Noted pre-existing slip, left untouched by request policy: lab intro says "four things"
  but lists five checks (content pass, not voice).
- Words: 14,589 -> 17,691 (validator count). `planning/STATUS.md` updated.

## 1.11 How a program runs (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: "fails before its first log line" opener, stage-crew picture for the
  loader, promise-versus-delivery for demand paging, file-exists-but-not-found musl puzzle.
- Supervision verdict: `loss_check` 0 of 130 terms / 0 of 82 numbers / 0 sources lost;
  `validate_chapter.py 1.11` VERDICT: OK; chain gate 0.4/1000; 20 questions; lab 21/21.
  Code-density WARN 11.5 (was 12.0) accepted per policy.
- Words: 10,549 -> 12,459 (validator count). `planning/STATUS.md` updated.

## 1.18 CPU scheduling and cgroups (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: week-long job suddenly crawling; cache-shelf and factory-line
  pictures; throttling as a fuel allowance; weight taught as proportions, not a cap;
  one agent-flagged self-contradiction in section 2 smoothed without touching facts.
- Supervision verdict: `loss_check` 0 of 185 terms / 0 of 86 numbers / 0 sources lost;
  `validate_chapter.py 1.18` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 20/20.
  Code-density WARN 6.5 (was 7.0) accepted per policy.
- Words: 9,468 -> 12,484 (validator count). `planning/STATUS.md` updated.

## 1.19 Namespaces (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: "the kernel has no container object" hook; two services hunting the
  same port 80; patient row-by-row walk of all eight namespace types; veth as a cable
  with two ends; use-versus-see framing for cgroups/namespaces.
- Supervision verdict: `loss_check` 0 of 107 terms / 0 of 70 numbers / 0 sources lost;
  `validate_chapter.py 1.19` VERDICT: OK; chain gate 0.0/1000; 20 questions; lab 19/19.
  Code-density WARN 7.4 accepted per policy.
- Words: 8,485 -> 10,217 (validator count). `planning/STATUS.md` updated.

## 1.7 Packages and software installation (2026-11-12, GLM failover + supervision)

- DeepSeek-Flash run hit the provider token quota after partial edits; supervisor
  reverted the file and re-dispatched on `nebius/zai-org/GLM-5.3-Flash`.
- Voice treatment: demo-day scene (worked Friday, driver gone Monday); carried analogy
  of storeroom unpacker / shopper / inventory for rpm vs apt vs the package database;
  hold taught before its commands; agent also self-checked loss vs the pre-edit file.
- Supervision verdict: `loss_check` 0 of 176 terms / 0 of 62 numbers / 0 sources lost;
  `validate_chapter.py 1.7` VERDICT: OK natively; chain gate 0.4/1000; 20 questions;
  lab 23/23. Code-density WARN 6.0 (was 6.2) accepted per policy.
- Words: 15,590 -> 17,197 (validator count). `planning/STATUS.md` updated.

## 1.22 Kernel modules, DKMS and sysctl (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: driver chain as four matching links; DKMS opens on the kernel-update
  failure with a furniture-cut-to-fit analogy; Secure Boot as "works next door, not here";
  sysctl as two stories (lost tuning, silent file).
- Supervision verdict: `loss_check` 0 of 154 terms / 0 of 70 numbers / 0 sources lost;
  chain gate 0.1/1000; 20 questions; lab 19/19. Code-density WARN 7.2 accepted per policy.
- Coverage bookkeeping fix (pre-existing, agent verified on the untouched original):
  recorded `terraform-up-and-running-3rd-edition` Ch 4 and
  `computer-networking-problems-and-solutions` Ch 24 as read/not-relevant in
  `planning/ledgers/1-22.md`; validator now prints VERDICT: OK.
- Words: 7,596 -> 9,254 (validator count). `planning/STATUS.md` updated.

## 1.28 Tuning a Linux node (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: capstone framing tying back to every earlier chapter; procurement
  story (two identical nodes, one slow); dataloader on the wrong socket; three things
  that look like a slow GPU.
- Supervision verdict: `loss_check` 0 of 116 terms / 0 of 84 numbers / 0 sources lost;
  `validate_chapter.py 1.28` VERDICT: OK natively; chain gate 0.2/1000; 20 questions;
  lab 15/15. Code-density WARN 5.6 (was 6.0) accepted per policy.
- Words: 9,701 -> 12,464 (validator count). `planning/STATUS.md` updated.

## 1.25 Benchmarking correctly (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: two engineers getting different numbers; passive vs active told as
  two engineers; worked examples A-E told as stories with all figures preserved;
  readability all `ok` (3.5 code terms/100 words).
- Supervision verdict: `loss_check` 0 of 36 terms / 0 of 105 numbers / 0 sources lost;
  `validate_chapter.py 1.25` VERDICT: OK natively; chain gate 0.3/1000; 20 questions;
  lab 15/15.
- Pre-existing slip noted for a future content pass: "Follow nine rules" then only
  rules 7-9 are named (same policy as the 1.4 counting slips).
- Words: 9,875 -> 12,709 (validator count). `planning/STATUS.md` updated.

## 1.16 Logging, time and cron (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: 3 a.m. misbehaving node; logrotate's open-inode trap told plainly;
  two clocks disagreeing and munge rejecting jobs; inherited-crontab opener.
- Supervision verdict: `loss_check` 0 of 113 terms / 0 of 90 numbers / 0 sources lost;
  `validate_chapter.py 1.16` VERDICT: OK natively on both versions; chain gate 0.0/1000;
  20 questions; lab 21/21. Code-density WARN 8.2 (was 8.8) accepted per policy.
- Words: 8,141 -> 9,810 (validator count). `planning/STATUS.md` updated.

## 1.26 KVM, QEMU and libvirt (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: IOMMU as a bouncer; twice-forwarded letter for guest memory; the
  "use virtio" story as I/O opener; boots-and-crawls title rewrite.
- Honesty call worth noting: the agent softened "classic ways an afternoon disappears"
  because the frequency claim was not in any source; exactly the drafting discipline the
  plan demands.
- Supervision verdict: `loss_check` 0 of 86 terms / 0 of 72 numbers / 0 sources lost;
  `validate_chapter.py 1.26` VERDICT: OK natively; chain gate 0.3/1000; 20 questions;
  lab 16/16. Code-density WARN 4.6 (was 4.9) accepted per policy.
- Words: 8,425 -> 11,145 (validator count). `planning/STATUS.md` updated.

## 1.21 Linux security (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: capabilities as one key, not the whole ring; PAM as a shared login
  desk; DAC/MAC parcel-label image; SELinux reboot-denial and container-escape scenes.
- Supervision verdict: `loss_check` 0 of 184 terms / 0 of 78 numbers / 0 sources lost;
  `validate_chapter.py 1.21` VERDICT: OK natively; chain gate 0.1/1000; 20 questions;
  lab 19/19. Code-density WARN 7.7 (was 8.1) accepted per policy.
- Words: 8,980 -> 10,680 (validator count). `planning/STATUS.md` updated.

## 1.8 Processes and signals (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: 2 a.m. "thing eating the node"; mode switch/interrupts/preemption
  each given oxygen; zombies and load average split into teachable chunks; job control
  opened on a dropped VPN session.
- Supervision verdict: `loss_check` 0 of 141 terms / 0 of 101 numbers / 0 sources lost;
  `validate_chapter.py 1.8` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 24/24.
  Code-density WARN 7.4 (was 7.8) accepted per policy.
- Words: 13,885 -> 16,589 (validator count). `planning/STATUS.md` updated.

## 1.17 Memory management (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: exit-code-137 opener with healthy `nvidia-smi`; NUMA taught via a
  job slowing after moving socket (wrong-warehouse image); buddy allocator as merging
  parking spaces; hugetlb pool as reserved rooms; OOM as overnight disappearance.
- Supervision verdict: `loss_check` 0 of 148 terms / 0 of 95 numbers / 0 sources lost;
  `validate_chapter.py 1.17` VERDICT: OK; chain gate 0.2/1000; 20 questions; lab 21/21.
  Code-density WARN 6.2 (was 6.9) accepted per policy.
- Words: 9,936 -> 12,462 (validator count). `planning/STATUS.md` updated.

## 1.24 Observability tools (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: slow job with calm GPU dashboards; three-lens framing (perf samples,
  Ftrace reads call flow, BPF runs programs); odometer for counters, security camera for
  sampling; flame-graph-ends-the-argument scene.
- Supervision verdict: `loss_check` 0 of 186 terms / 0 of 89 numbers / 0 sources lost;
  `validate_chapter.py 1.24` VERDICT: OK natively; chain gate 0.2/1000; 20 questions;
  lab 15/15. Code-density WARN 8.1 (was 8.7) accepted per policy.
- Words: 11,835 -> 13,239 (validator count). `planning/STATUS.md` updated.

## 1.10 Devices, udev, sysfs and procfs (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: on-call scene (7 of 8 GPUs); `/dev` as doorway, `/sys` as blueprint,
  `/proc` as instrument panel, udev as the clerk; major/minor as building/room.
- Supervision verdict: `loss_check` 0 of 250 terms / 0 of 93 numbers / 0 sources lost;
  `validate_chapter.py 1.10` VERDICT: OK natively; chain gate 0.5/1000; 20 questions;
  lab 23/23. Code-density WARN 9.7 (was 10.6) accepted per policy.
- Words: 9,935 -> 11,303 (validator count). `planning/STATUS.md` updated.

## 1.14 Boot: firmware, GRUB, kernel, initramfs (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs.
- Voice treatment: 3 a.m. black-screen opening; seven boot stages as hand-offs; initramfs
  as "a system waiting for one missing piece"; PXE rack of new GPU nodes.
- Supervision verdict: `loss_check` 0 of 208 terms / 0 of 109 numbers / 0 sources lost;
  `validate_chapter.py 1.14` VERDICT: OK natively; chain gate 0.1/1000; 20 questions;
  lab 23/23. Code-density WARN 7.5 (was 7.9) accepted per policy.
- Words: 11,008 -> 13,820 (validator count). `planning/STATUS.md` updated.

## 1.23 Performance methodology (2026-11-12, subagent + supervision)

- Drafted by `general` subagent on `nebius/deepseek-ai/DeepSeek-V4.1-Flash-1017`; Kimi
  supervised with independent gate runs AND a numeric audit of the agent's one judgement
  call (below).
- Voice treatment: Monday-meeting three-guesses scene, later called back; USE as a loop;
  five whys told as an incident; "honest blanks beat guesses".
- JUDGEMENT CALL VERIFIED BY SUPERVISOR: baseline `0f258b4` says M/D/1 response `1.6 s`
  and HEAD says `1.75 s` at 60% (formula `r = s(2-rho)/(2(1-rho))`, so 1.75 s is the
  reviewed-correct value; the rework pass had already fixed it). The agent kept 1.75 s
  and added the labelled derived point "the same curve passes 1.6 s at about 55%"
  (55% gives 1.611 s; audit confirmed). Nothing restored to the old wrong figure.
- Supervision verdict: `loss_check` 0 of 36 terms / 0 of 83 numbers / 0 sources lost;
  `validate_chapter.py 1.23` VERDICT: OK (readability all `ok`, 2.0 code terms/100w);
  chain gate 0.1/1000; 20 questions; lab 15/15.
- Words: 10,953 -> 14,784 (validator count). `planning/STATUS.md` updated.

## Model note: Kimi K3 run abandoned

A parallel test of full `Kimi-K3` as a drafting subagent on 1.6 was cancelled by the
author on cost grounds (about 10-20x the flash models). Its ~17-line partial edit to
chapter 1.6 was reverted before the GLM-Flash pass; the subagent confirmed ABORTED with
no completed edits. Policy from here: flash-class models draft, Kimi (full) supervises.
