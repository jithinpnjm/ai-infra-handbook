# OPUS_REPORT_1: editorial review of Parts 0 to 9 (220 chapters)

Reviewer set N=1. Inputs: digest_1.md (all 220 chapters), 12 chapters read in full (0.1, 1.22, 2.19, 3.6, 4.19, 5.9, 5.32, 6.12, 6.31, 7.10, 8.12, 9.5), spot reads of 3.16, and repository-wide counts over docs/part-00 to part-09. Counts quoted below come from grep over those folders on 2026-11-12.

Headline findings, in order of importance:

1. Chapters 3.12 to 3.17 (178,000 words, about 1,860 code blocks) are close paraphrases of *Learning Python*, with the book's own example numbers ("Example 28-7", `person_7.py`), its cross-references ("see Chapters 9, 28, and 37") and its typo (`myditctionary`). They contain zero mentions of GPU, Slurm, Kubernetes or cluster. This is a copyright exposure and a reader trap. Cut them.
2. Source leakage is the book's biggest voice defect, and the 4-paragraph samples could not see its scale: "the book" 485 hits in 77 chapters, internal repo paths such as `volume-10/...` or "Volume 21 Chapter 6" 445 hits in 100 chapters, "the notes"/"the user's notes" 100 hits in 30 chapters, book example numbers ("Example 20-6") 268 hits in 26 chapters, and source abbreviations in backticks (`HLW`, `TUR`, `AUR`, `LP`, `SCL`, `DAI`, `ASP`, `KUR`, `NPA`) 215 hits in 62 chapters. A reader meets the drafting process instead of an author.
3. Two voices are spliced together in Part 9, in the capstone 6.31, in 7.10 section 8.1, in 8.14 and in parts of 9.5: a plain book-summary voice and a bold-heavy generator voice ("workload physics", "inert silicon", "Senior Systems Architect Answer", "In one minute" boxes, LaTeX arrows in tables). Part 9 sentences average 20 to 22 words against 13 to 15 elsewhere.
4. Technical depth in Parts 1, 2, 4, 5, 6, 7 and 8 is genuinely good. Several chapters (4.19, 5.32, 8.12, 2.19, 1.22) would earn respect from a senior SRE. The problems are packaging, repetition and a short list of concrete errors (section 6).
5. Every chapter carries a body, "Interview angles", 6 exercises and 20 checkpoint Q&As (190 chapters have "Checkpoint questions (20)"). The checkpoint answers mostly restate body paragraphs. Chapters are 6,000 to 17,000 words, which is too long for a beginner to finish in one sitting.

---

## 1. Verdict per part

**Part 0 (Orientation, 3 chapters).** 0.1 is the only real chapter and it is the wrong one: about 85 percent is a summary of an *AI Factory* business book chapter on smart manufacturing, SCADA pyramids, data-driven policymaking and the triple bottom line, with "the book" 19 times. It conflates Iansiti and Lakhani's business "AI factory" with NVIDIA's data-center AI factory, which is the sense the rest of the handbook uses. 0.2 and 0.3 are 450-word stubs that do their job but give no tour. The part fails its one purpose: a beginner finishes it without a picture of a GPU node, a training job, an inference request, or what an SRE does in this world. Gap: a one-chapter guided tour (a training job from `sbatch` to all-reduce, an inference request from load balancer to KV cache) that every later part can point back to.

**Part 1 (Linux, 30 chapters).** Strong, practical, correct, and well anchored in GPU-node failures; openings were already rewritten to "Picture a node that..." and they work. Depth is senior grade in 1.10, 1.13, 1.15, 1.17, 1.18, 1.22, 1.28. Problems: length (1.7 at 16.5k, 1.8 at 15.8k, 1.12 at 17.2k words), source leakage in headings ("`HLW` Section 11.1.1" in 1.9), legacy material kept because the source book had it (SysV inittab in 1.14, vi/Emacs bibliographic detail in 1.5, PuTTY and X11 in 1.30), and Gregg-summary chapters (1.23, 1.26, 1.27) that read as book précis ("Gregg's Config A"). 1.29 openly declares itself a "reference and depth companion" to 1.5, which is duplication. Exercises are exam-generator style. Interview gaps: little on eBPF-based production tooling beyond bpftrace basics, nothing on kernel live patching or crash-dump (kdump) workflow at fleet scale.

**Part 2 (Networking, 32 chapters).** The most complete part for an infrastructure engineer, and the AI-fabric chapters (2.18, 2.19, 2.24, 2.31) are strong. Risk areas: scope creep inherited from *Computer Networking Problems and Solutions* (circuit switching and ATM in 2.2, RIP and EIGRP in 2.14, segment routing and SD-WAN in 2.17, biometrics and "two main types of vulnerability" in 2.21, AWS and Azure primers in 2.32), and exercises that cite that book by chapter number, which the reader does not have. 2.16 contains prose transcriptions of a figure ("SA1 connects to SB2 and SC1...") that nobody can read without the figure. Redundancy: namespaces, veth and bridges are built by hand in 1.20, 2.25, 2.27 and 5.13. Gap: InfiniBand itself (subnet manager, LIDs, credit-based flow control) is deferred to Part 12, but RoCE is taught deeply here; a beginner gets lossless Ethernet before knowing what it imitates.

**Part 3 (Python, 17 chapters).** Two different books glued together. 3.1 to 3.11 are infrastructure-flavoured and useful, though 3.3, 3.4, 3.6 and 3.11 carry heavy *Fluent Python* example transcription (FrenchDeck, spinner scripts, "40.81s" timings from the author's laptop, `POP20_CC`). 3.12 to 3.17 are a re-told *Learning Python*: no exercises, no infra context, tkinter callbacks, `codecs` for Python 2 compatibility, a `Person` class built in seven steps. They duplicate 3.1 to 3.5 and 3.11. Accessibility ramp is poor: 3.1 is 17k words with 103 code blocks and opens the part. Gap: nothing on Python performance profiling for data loaders (py-spy is mentioned only in 3.6), packaging of CUDA wheels is touched in 3.2 but not the `uv`/lockfile workflow most teams now use.

**Part 4 (Automation, 27 chapters).** Technically solid and current (Terraform 1.10 native S3 locking, `removed` blocks, OpenTofu state encryption, AAP 2.5 API path). Fifteen Ansible chapters is a lot relative to the rest of the book, and several are Ansible-book walk-throughs (4.9 deploys a Django/Mezzanine app from *Ansible: Up and Running*). Headings carry `AUR`, `TUR`, `NPA` tags. One risky piece of advice: 4.3 recommends full `NOPASSWD: ALL` sudo for the automation group without a scoping caveat. Terraform chapters are AWS-flavoured examples (webserver-cluster, MySQL 3306) in a handbook whose labs are GCP and Nebius. Gap: Nebius Terraform provider specifics are thin (4.24), and no chapter shows a real CI pipeline running plan/apply with OIDC end to end.

**Part 5 (Kubernetes, 35 chapters).** Deep and mostly correct; the GPU-specific chapters (5.9, 5.18, 5.32, 5.33) are the best in the set. Problems: *Kubernetes: Up and Running* and *Production Kubernetes* passages pasted into chapters that already covered the same thing in the book's own voice (5.9 has two full probe explanations, one with "Example 5-2", kuard and Docker-era event text; 5.3 says "The book's DNS Service"; 5.22 "PinterestService"). 5.4 is a bare-metal kubeadm lab that detours into a GKE quickstart. 5.7 is 16.5k words with 69 code blocks. 5.34 frames GKE as "one of the three clouds this role touches", which is a job-description leak. Gap for a Senior SRE interview: control-plane SLOs and API priority and fairness get only passing mention; etcd performance tuning (defrag, quotas, disk latency) is light.

**Part 6 (HPC and Slurm, 31 chapters).** The Slurm core (6.7 to 6.16) is excellent and interview-relevant. The supercomputer-book chapters (6.1, 6.2, 6.6, 6.24, 6.25) drag in fog computing, cloning a system disk by attaching drives, NIS/NIS+, and setting up a support mail alias. Titles 6.1 to 6.6 and 6.8 end with a full stop. 6.30 critiques its source book's acronym error in reader-facing text. 6.12 and 6.31 dump book tables (Llama 3 interruption list, 8B checkpoint byte counts) and generator-voice interview scripts. Ordering problem: 6.22, 6.23 and 6.31 depend on BCM and Redfish (Parts 7 and 8), which come later. Redundancy: containers on Slurm in 6.13, 6.29 and 8.10; facility power in 6.30, 8.15, 9.7 and 9.11.

**Part 7 (Redfish and BMC, 15 chapters).** Technically careful: grounded in DSP0266 sections, with a mock BMC and honest "what the tests do not prove" statements. Voice is a lab notebook: "My tool reads the whole inventory", "In my lab", "I have not run `nvfwupd`", "The user's notes tell this story" (7.10), "The Security volume of the notes (volume 18)" (7.15). DSP0266 clause numbers appear in body text where a beginner needs the idea, not the clause. Ramp is good from 7.1 to 7.7. Gap: OpenBMC internals and the Redfish telemetry service (metric reports) are thin, and NVIDIA's HMC on the HGX baseboard is described but not shown end to end.

**Part 8 (BCM, 16 chapters).** Faithful to the BCM 11 Administrator Manual and useful for anyone who will run BCM; 8.12 is a model of how to teach HA safely. The voice is "the manual says" throughout, headings carry manual section numbers ("(5.4)", "(10.2.4 to 10.2.8)"), and every exercise 1 is the same sentence ("Run `X_lab.py`. Choose four checks and explain each rule"), with lab paths missing `code/part08/`. 8.11 lists Base View icons left to right. 8.14 and 8.16 carry generator voice and version-specific bug notes (BCM 11.33 wizard bug, internal ticket BCM-31089) that will age in months. Gap: no chapter compares BCM with what a cloud SRE would use instead (Ironic, MAAS, Talos) in decision terms, which is the interview question.

**Part 9 (NVIDIA systems, 14 chapters).** The weakest voice in the set and the highest correctness risk. Every chapter has an empty "Concepts: basics → intermediate → advanced" H2, long sentences, drama vocabulary, and internal leaks ("Volume 21 Chapter 6 Part 3.2", "Volume 19 Chapters 3 and 6"). 9.5 splices generator sections with plain AI Systems Performance Engineering summaries that contradict them (power "fully liquid cooled" versus "hybrid liquid+air"; AC-to-DC conversion placed in the compute tray). 9.13 is written for a "Senior Solutions Architect" in a budget meeting, not an SRE. Depth is real (NVL72 crossbar math, BCM dual-protocol firmware, SuperPOD SU sizing), but numbers need a verification pass against NVIDIA documents, and the "Corpus scope note" in 9.5 admits the rack slot map did not come from the hardware user guide.

---

## 2. Chapter table (all 220 chapters)

Scores: voice, depth, accessibility, each 1 to 5. 5 means an expert human wrote it.

| chapter id | voice | depth | access | action | one-line reason |
|---|---|---|---|---|---|
| 0.1 | 2 | 1 | 3 | rewrite-chapter | Manufacturing/policy book summary; wrong sense of "AI factory"; keep only layers, roles, checkpoint Qs |
| 0.2 | 3 | 2 | 4 | expand | Useful lab setup stub; add cost guardrails per venue and a first-hour smoke test |
| 0.3 | 3 | 2 | 3 | expand | Paths table fine; opens with checkpoint text; add SRE path explicitly |
| 1.1 | 4 | 3 | 4 | light-edit | Good hook; 10k words for a big-picture chapter; trim |
| 1.2 | 4 | 4 | 4 | light-edit | Solid shell chapter; exercise headings exam-style |
| 1.3 | 4 | 4 | 4 | light-edit | Strong opening; FHS exercise trivia |
| 1.4 | 4 | 4 | 4 | keep | Clear, practical, right length |
| 1.5 | 3 | 3 | 4 | rewrite-sections | vi/Emacs book bibliographies in body; absorb 1.29's needed parts |
| 1.6 | 4 | 4 | 3 | light-edit | Good; 13k words; long tables |
| 1.7 | 3 | 4 | 3 | split | 16.5k words, 38 code blocks; split packaging basics vs GPU driver repos |
| 1.8 | 3 | 4 | 3 | split | 15.8k words; process model vs signals/job control |
| 1.9 | 3 | 4 | 3 | light-edit | `HLW` tag in heading; otherwise strong |
| 1.10 | 4 | 4 | 3 | light-edit | Dense device detail; hwdb aside could go |
| 1.11 | 3 | 4 | 3 | rewrite-sections | Drifts into Gregg software-design advice mid-chapter |
| 1.12 | 3 | 4 | 3 | split | 17.2k words, 57 code blocks; disks vs filesystems |
| 1.13 | 4 | 4 | 3 | light-edit | Good NVMe queue explanation; dm table exercises too exam-like |
| 1.14 | 3 | 4 | 3 | rewrite-sections | SysV inittab detail obsolete; keep GPU-boot material |
| 1.15 | 4 | 4 | 4 | light-edit | Strong systemd chapter |
| 1.16 | 4 | 4 | 4 | light-edit | Good chrony reading guidance |
| 1.17 | 4 | 5 | 3 | light-edit | Excellent depth; exercise asks PTE arithmetic without need |
| 1.18 | 4 | 4 | 3 | light-edit | Good cgroup framing |
| 1.19 | 4 | 4 | 4 | light-edit | Good; /dev/shm story works |
| 1.20 | 4 | 4 | 4 | keep | Good lab with real payoff |
| 1.21 | 3 | 4 | 3 | light-edit | Broad; harden/relax trade-off well framed |
| 1.22 | 3 | 4 | 3 | rewrite-sections | Strong core; leaks ("book's examples", "Volume 10"), "(flag)" markers, off-topic bullets |
| 1.23 | 3 | 4 | 3 | rewrite-sections | Gregg précis; no failure section; keep USE method, cut vocabulary list |
| 1.24 | 3 | 4 | 3 | light-edit | Good tool coverage; ftrace trigger detail heavy |
| 1.25 | 4 | 4 | 4 | light-edit | Strong opening; Bonnie++ exercise dated |
| 1.26 | 3 | 3 | 3 | rewrite-sections | "Gregg's example", Config A/B vocabulary; refocus on GPU passthrough/KubeVirt |
| 1.27 | 3 | 3 | 3 | rewrite-sections | 13k words, 2 code blocks; cloud book précis; cut by half |
| 1.28 | 3 | 4 | 3 | light-edit | Good capstone; PyTorch allocator aside belongs in Part 10 |
| 1.29 | 3 | 3 | 3 | merge-with 1.5 | Self-declared companion to 1.5; keep pdsh/console material as reference appendix |
| 1.30 | 3 | 3 | 3 | rewrite-sections | PuTTY/WinSCP/X11/VNC dated; keep rsync and NFS client depth |
| 2.1 | 4 | 4 | 4 | light-edit | Excellent framing chapter |
| 2.2 | 3 | 3 | 3 | rewrite-sections | Opening lists 11 undefined acronyms; circuit switching/ATM history |
| 2.3 | 4 | 4 | 4 | light-edit | Good L2 failure stories |
| 2.4 | 4 | 4 | 4 | light-edit | Good address-plan hook |
| 2.5 | 4 | 4 | 4 | light-edit | Good multi-homed GPU server framing |
| 2.6 | 4 | 4 | 3 | light-edit | Solid; transport-model taxonomy (RINA) is noise |
| 2.7 | 4 | 4 | 4 | keep | Practical PMTU method |
| 2.8 | 4 | 4 | 4 | keep | Strong ndots and resolver coverage |
| 2.9 | 4 | 4 | 4 | light-edit | Good PXE link |
| 2.10 | 4 | 4 | 4 | light-edit | Good cert-expiry framing |
| 2.11 | 3 | 3 | 3 | rewrite-sections | Switching internals plus protocol hello taxonomy; trim |
| 2.12 | 4 | 4 | 3 | light-edit | Good elephant-flow material |
| 2.13 | 3 | 4 | 3 | light-edit | BFD material good; AD/flooding detail heavy |
| 2.14 | 3 | 3 | 3 | rewrite-sections | RIP/EIGRP not needed; compress to OSPF/IS-IS underlay essentials |
| 2.15 | 4 | 4 | 3 | light-edit | Good; hot/cold potato aside optional |
| 2.16 | 3 | 4 | 2 | rewrite-sections | Figure transcribed as prose; replace with diagram |
| 2.17 | 3 | 3 | 3 | rewrite-sections | SR/SRv6/SD-WAN scope creep; focus VXLAN/EVPN for GPU clouds |
| 2.18 | 3 | 4 | 3 | light-edit | Strong; 12k words; torus aside could move |
| 2.19 | 4 | 5 | 3 | light-edit | Excellent; fix 14x serialization error; ECN vs PFC buffer location |
| 2.20 | 4 | 4 | 3 | light-edit | Good inference LB framing |
| 2.21 | 3 | 3 | 3 | rewrite-sections | Dated How-Linux-Works vulnerability text, STRIDE/biometrics generic |
| 2.22 | 4 | 4 | 3 | light-edit | Good counter reading |
| 2.23 | 4 | 4 | 3 | light-edit | Good conntrack story |
| 2.24 | 4 | 4 | 3 | light-edit | Good multi-homed tuning |
| 2.25 | 3 | 4 | 3 | light-edit | Overlaps 1.20 and 5.13; link instead of rebuild |
| 2.26 | 4 | 4 | 4 | light-edit | Good capture chapter |
| 2.27 | 4 | 4 | 4 | keep | Good lab |
| 2.28 | 3 | 4 | 3 | light-edit | Book-heavy model families |
| 2.29 | 3 | 3 | 3 | light-edit | Tool comparison on "10 axes" is book structure |
| 2.30 | 4 | 4 | 4 | keep | Strong method chapter |
| 2.31 | 4 | 4 | 4 | light-edit | Strong AI-fabric telemetry framing |
| 2.32 | 3 | 3 | 3 | rewrite-sections | IaaS/PaaS and AWS/Azure primer; make it GCP/Nebius GPU networking |
| 3.1 | 3 | 4 | 2 | rewrite-sections | 17k words, 103 code blocks; `LP` tags; split basics from REPL trivia |
| 3.2 | 3 | 4 | 3 | light-edit | Good packaging failures; LP import-cycle detail long |
| 3.3 | 3 | 4 | 2 | rewrite-sections | Fluent Python examples (FrenchDeck, "Example 9-14") |
| 3.4 | 3 | 4 | 3 | rewrite-sections | "In the book's example"; MRO rules from book |
| 3.5 | 3 | 4 | 3 | light-edit | Good failure discipline; LP misspelled example |
| 3.6 | 3 | 4 | 3 | rewrite-sections | Strong patterns; Fluent Python benchmark transcription; two errors |
| 3.7 | 3 | 4 | 3 | light-edit | Good; book chapter citations in exercises |
| 3.8 | 4 | 4 | 4 | light-edit | Good operational tooling chapter |
| 3.9 | 4 | 4 | 4 | light-edit | Good |
| 3.10 | 4 | 4 | 4 | light-edit | Good dataloader starvation section |
| 3.11 | 3 | 4 | 2 | rewrite-sections | 86 code blocks of LP metaprogramming; keep framework-reading purpose |
| 3.12 | 2 | 3 | 3 | cut-duplicate | Learning Python paraphrase; no infra content; copyright risk |
| 3.13 | 2 | 3 | 3 | cut-duplicate | Same; duplicates 3.1 |
| 3.14 | 2 | 3 | 3 | cut-duplicate | Same; tkinter lambda; duplicates 3.1/3.11 |
| 3.15 | 2 | 3 | 3 | cut-duplicate | Same; duplicates 3.2 |
| 3.16 | 2 | 3 | 3 | cut-duplicate | "Example 28-7" Person class; duplicates 3.4 |
| 3.17 | 2 | 3 | 3 | cut-duplicate | Python 2 codecs; duplicates 3.5/3.11 |
| 4.1 | 4 | 4 | 4 | light-edit | Good incident hook; `NPA` tag |
| 4.2 | 4 | 4 | 4 | light-edit | Good CAB story |
| 4.3 | 3 | 4 | 4 | light-edit | Scope the NOPASSWD advice |
| 4.4 | 3 | 4 | 3 | light-edit | XSLT aside is noise |
| 4.5 | 3 | 4 | 3 | light-edit | Vagrant port example from book |
| 4.6 | 3 | 4 | 3 | light-edit | Walkthrough named after book file |
| 4.7 | 3 | 4 | 3 | light-edit | Good data-driven framing |
| 4.8 | 3 | 4 | 3 | light-edit | Good order of defence |
| 4.9 | 3 | 3 | 3 | rewrite-sections | Mezzanine/Django deployment from book; use a GPU-adjacent service |
| 4.10 | 3 | 4 | 4 | light-edit | Good layered method |
| 4.11 | 3 | 4 | 4 | light-edit | Good |
| 4.12 | 4 | 4 | 4 | light-edit | Good leak response |
| 4.13 | 3 | 4 | 3 | light-edit | Good |
| 4.14 | 3 | 4 | 3 | light-edit | Opening has dangling "Other tools help too" |
| 4.15 | 3 | 4 | 3 | light-edit | Good GPU power-cap module |
| 4.16 | 3 | 4 | 3 | light-edit | Good fabric-as-data |
| 4.17 | 4 | 4 | 3 | light-edit | Strong bring-up graph |
| 4.18 | 3 | 4 | 3 | light-edit | `TUR` tags in headings |
| 4.19 | 4 | 4 | 4 | light-edit | Strong; AWS-centric examples in GCP/Nebius book |
| 4.20 | 3 | 4 | 3 | light-edit | Good |
| 4.21 | 3 | 4 | 3 | light-edit | Good gotchas |
| 4.22 | 3 | 4 | 3 | light-edit | Good layering rule |
| 4.23 | 3 | 4 | 3 | light-edit | Good policy-as-code |
| 4.24 | 3 | 3 | 3 | expand | Nebius provider specifics thin |
| 4.25 | 3 | 4 | 3 | light-edit | Good |
| 4.26 | 4 | 4 | 3 | light-edit | Good GitOps |
| 4.27 | 3 | 4 | 3 | keep | Good integrating lab |
| 5.1 | 4 | 4 | 4 | light-edit | Good image-pull hook |
| 5.2 | 4 | 4 | 3 | light-edit | Good; OCI history paragraph |
| 5.3 | 3 | 4 | 3 | light-edit | "The book's DNS Service" leak; `KUR` heading |
| 5.4 | 3 | 4 | 3 | rewrite-sections | GKE quickstart inside bare-metal kubeadm lab |
| 5.5 | 4 | 5 | 3 | light-edit | Excellent API/etcd chapter |
| 5.6 | 4 | 4 | 4 | light-edit | Good controller framing |
| 5.7 | 3 | 4 | 3 | split | 16.5k words, 69 code blocks; KUR basics pasted |
| 5.8 | 4 | 5 | 3 | keep | Excellent pod timeline |
| 5.9 | 3 | 5 | 3 | rewrite-sections | Excellent core; pasted KUR/PK probe sections contradict it |
| 5.10 | 3 | 4 | 3 | light-edit | Book GKE example leak |
| 5.11 | 4 | 4 | 4 | keep | Good ndots coverage |
| 5.12 | 3 | 4 | 3 | light-edit | Contour install from book |
| 5.13 | 3 | 4 | 3 | light-edit | Overlaps 2.25 |
| 5.14 | 4 | 4 | 3 | light-edit | Good decision frame |
| 5.15 | 4 | 4 | 3 | light-edit | Good |
| 5.16 | 3 | 4 | 3 | light-edit | 14.7k words; "the book" 24 times |
| 5.17 | 4 | 4 | 3 | light-edit | Good |
| 5.18 | 4 | 5 | 3 | keep | Excellent gang-scheduling hook |
| 5.19 | 3 | 4 | 3 | light-edit | Good dependency-graph idea |
| 5.20 | 4 | 4 | 3 | light-edit | Good |
| 5.21 | 3 | 4 | 3 | light-edit | Long; good |
| 5.22 | 3 | 4 | 3 | light-edit | PinterestService example from book |
| 5.23 | 4 | 4 | 4 | light-edit | Good |
| 5.24 | 4 | 4 | 3 | light-edit | Good |
| 5.25 | 3 | 4 | 3 | light-edit | ASL 17.6; long sentences |
| 5.26 | 4 | 5 | 3 | keep | Excellent kernel map |
| 5.27 | 3 | 4 | 3 | light-edit | Good |
| 5.28 | 3 | 4 | 3 | light-edit | Good |
| 5.29 | 4 | 4 | 3 | light-edit | Good |
| 5.30 | 3 | 4 | 3 | light-edit | Good |
| 5.31 | 3 | 4 | 3 | light-edit | Good |
| 5.32 | 4 | 5 | 4 | light-edit | Best project chapter; fix absent-condition contradiction and volume-10 section |
| 5.33 | 4 | 5 | 3 | keep | Excellent source-reading method |
| 5.34 | 3 | 4 | 3 | light-edit | "This role touches" JD leak |
| 5.35 | 3 | 4 | 3 | light-edit | Good |
| 6.1 | 3 | 3 | 3 | rewrite-sections | Fog computing; title full stop |
| 6.2 | 3 | 3 | 3 | rewrite-sections | 11k words, 3 code blocks; book précis |
| 6.3 | 4 | 4 | 4 | light-edit | Good Monday-morning hook |
| 6.4 | 4 | 4 | 3 | light-edit | Fix btl exclusion example |
| 6.5 | 4 | 4 | 3 | light-edit | Good ticket hook |
| 6.6 | 3 | 3 | 3 | rewrite-sections | Disk-copy-by-hand, "Zhumatiy notes" |
| 6.7 | 4 | 5 | 3 | keep | Excellent |
| 6.8 | 3 | 4 | 3 | light-edit | Good; backtick density 16.6 per 100 words |
| 6.9 | 3 | 4 | 3 | light-edit | Good fair-tree example |
| 6.10 | 4 | 5 | 3 | keep | Excellent GRES chapter |
| 6.11 | 4 | 4 | 4 | light-edit | Good |
| 6.12 | 3 | 4 | 3 | rewrite-sections | Strong layering; book-table dumps, LaTeX, inconsistent torchrun example |
| 6.13 | 4 | 4 | 4 | light-edit | Good |
| 6.14 | 4 | 4 | 4 | keep | Good method |
| 6.15 | 3 | 4 | 3 | rewrite-sections | Opening starts mid-thought; verify upgrade-hop rule |
| 6.16 | 3 | 4 | 3 | light-edit | Good |
| 6.17 | 3 | 4 | 3 | light-edit | Good |
| 6.18 | 3 | 4 | 3 | light-edit | Good |
| 6.19 | 3 | 4 | 3 | light-edit | Good |
| 6.20 | 3 | 3 | 3 | light-edit | CVMFS aside |
| 6.21 | 3 | 4 | 3 | light-edit | Good |
| 6.22 | 3 | 4 | 3 | rewrite-sections | BCM installer steps inside generic PXE chapter |
| 6.23 | 3 | 4 | 3 | light-edit | Compares with BCM before BCM is taught |
| 6.24 | 3 | 3 | 3 | rewrite-sections | NIS/NIS+, ext3 rquotad; keep LDAP/SSSD |
| 6.25 | 3 | 3 | 3 | rewrite-sections | Support mail alias; keep bastion/OOD |
| 6.26 | 3 | 4 | 3 | light-edit | Ganglia/SNMP history |
| 6.27 | 3 | 4 | 3 | light-edit | Good |
| 6.28 | 3 | 4 | 3 | light-edit | "The book's example, Table 5-1" |
| 6.29 | 3 | 4 | 3 | light-edit | Overlaps 6.13 |
| 6.30 | 3 | 3 | 4 | rewrite-sections | Critiques source book's AALC error in reader text |
| 6.31 | 2 | 4 | 3 | rewrite-sections | Generator voice, persona tables, LaTeX, depends on Parts 7/8 |
| 7.1 | 3 | 4 | 3 | light-edit | Good two-doors story |
| 7.2 | 3 | 4 | 3 | light-edit | DSP0266 clause numbers |
| 7.3 | 3 | 4 | 3 | light-edit | Good PATCH partial-success rule |
| 7.4 | 4 | 4 | 4 | light-edit | Good session-table point |
| 7.5 | 3 | 4 | 3 | light-edit | "In my lab" heading |
| 7.6 | 3 | 4 | 3 | light-edit | Good |
| 7.7 | 3 | 4 | 3 | light-edit | Good |
| 7.8 | 3 | 4 | 3 | light-edit | "The notes show" leak |
| 7.9 | 4 | 4 | 4 | light-edit | Good silent-degradation hook |
| 7.10 | 2 | 5 | 3 | rewrite-sections | Excellent activation teaching; notebook voice; spliced section 8.1 with errors |
| 7.11 | 4 | 4 | 4 | light-edit | Good |
| 7.12 | 3 | 4 | 3 | light-edit | "The client I used in all labs" |
| 7.13 | 3 | 4 | 3 | light-edit | Good |
| 7.14 | 3 | 4 | 3 | light-edit | "The notes put the stakes plainly" |
| 7.15 | 3 | 4 | 3 | light-edit | "Security volume of the notes (volume 18)" |
| 8.1 | 3 | 4 | 3 | light-edit | Good object model |
| 8.2 | 3 | 4 | 3 | light-edit | "In the manual's words" heading |
| 8.3 | 3 | 4 | 3 | light-edit | Manual section numbers in headings |
| 8.4 | 3 | 4 | 3 | light-edit | Good seven-cases section |
| 8.5 | 3 | 4 | 3 | light-edit | Good commit habit |
| 8.6 | 3 | 4 | 3 | light-edit | Good profile story |
| 8.7 | 3 | 4 | 3 | light-edit | Overlaps 7.10 firmware flow |
| 8.8 | 3 | 4 | 3 | light-edit | Drain paragraph trivial |
| 8.9 | 3 | 4 | 3 | light-edit | Good |
| 8.10 | 3 | 3 | 3 | light-edit | Overlaps 6.13/6.29 |
| 8.11 | 3 | 3 | 3 | rewrite-sections | Base View icon tour |
| 8.12 | 4 | 5 | 4 | light-edit | Model HA chapter; drop ticket id, fix numbering |
| 8.13 | 3 | 4 | 3 | light-edit | Good |
| 8.14 | 2 | 4 | 3 | rewrite-sections | Generator voice ("Zone 1: The Connected Staging Host") |
| 8.15 | 3 | 3 | 3 | light-edit | Duplicates 9.6/9.7 numbers; link instead |
| 8.16 | 2 | 3 | 3 | rewrite-sections | Version-specific bugs; Mission Control overview needs current sources |
| 9.1 | 2 | 3 | 3 | rewrite-sections | Drama voice; KV-cache exercise unclear |
| 9.2 | 2 | 4 | 3 | rewrite-sections | "Senior engineers never trust..." tone; good tray anatomy |
| 9.3 | 2 | 3 | 3 | rewrite-sections | "golden reference appliance"; unsourced 40-50% claim |
| 9.4 | 2 | 4 | 3 | rewrite-sections | Good PCIe-tax idea; ASL 20 |
| 9.5 | 2 | 4 | 2 | rewrite-chapter | Spliced voices, internal contradictions, AC/DC error |
| 9.6 | 2 | 4 | 3 | rewrite-sections | "physical twin" jargon; ASL 22 |
| 9.7 | 2 | 4 | 3 | rewrite-sections | Good B200 rack math; verify figures |
| 9.8 | 2 | 4 | 3 | rewrite-sections | Good SU numbers; ASL 21.5 |
| 9.9 | 2 | 4 | 3 | rewrite-sections | Good fabric map; bullet-bold voice |
| 9.10 | 2 | 3 | 3 | rewrite-sections | Good day-one defects list |
| 9.11 | 2 | 4 | 3 | rewrite-sections | Make canonical facility chapter |
| 9.12 | 2 | 3 | 3 | rewrite-sections | "Volume 21 Chapter 6" leak; overlaps Part 8 |
| 9.13 | 2 | 3 | 2 | rewrite-chapter | SA budget-meeting framing; abrupt list opening; volume leaks |
| 9.14 | 2 | 3 | 3 | rewrite-sections | Good archetypes; verify per-provider facts |

---

## 3. The 12 full-chapter reviews

### 3.1 Chapter 0.1 The AI factory landscape and the roles in it

Strengths: the first paragraph is excellent ("turn electricity and data into tokens"); the layer diagram, the training versus inference bullets, the roles table and the four checkpoint questions are exactly right.

Five most important problems:
1. Wrong subject. Lines 19 to 327 summarise a business-book chapter: Peloton, Walmart and Sears, BlueDot, lambda architecture, Industry 4.0, apprentice/journeyman/master, policymaking, triple bottom line.
2. Conflated definitions. "you get what the book calls an AI factory" is Iansiti and Lakhani's business sense, which contradicts the data-center sense in the opening.
3. Book voice: "the book" 19 times, "The book's table of enablers", "The book uses the Policy Lab approach".
4. Stale and irrelevant numbers: "In 2019, cloud spending on IaaS and SaaS hit $20 billion"; "SAP... requires a minimum of 60 GB".
5. Lists that violate the language rule: 12-bullet pros list, 9-bullet policy list, 10-statement smart-factory list.

Factual errors: "The IBM AC922 cluster has 4,608 servers" names the server model, not the system; the 4,608-node AC922 system is Summit (ORNL, TOP500), and it is retired. The 2016 data-volume figures are outdated.

Missing for a beginner: what a GPU server physically is, what a training step and an inference request are, why GPU-hours dominate cost, what "goodput" means.

Missing for an expert: utilisation and goodput economics (MFU, failure rate per thousand GPUs, checkpoint overhead), why scale makes reliability an SRE problem.

Rewrite instruction: Keep the opening paragraph, the layer diagram, "Training versus inference", "The roles" and the checkpoint questions. Delete everything from "Where the AI factory idea comes from" to "The triple bottom line". Add three short sections: "A training job, end to end" (scheduler, ranks, all-reduce, checkpoint), "An inference request, end to end" (load balancer, batching, KV cache, decode), and "What goes wrong at scale" (one failing GPU stalls 1,000; use the Llama 3 interruption rate as the single number). Target 2,500 words.

### 3.2 Chapter 1.22 Kernel modules, DKMS and sysctl tuning for GPU nodes

Strengths: the kernel ↔ module ↔ libraries ↔ CUDA chain is the right mental model; the unload order, the DKMS failure groups, the fleet delivery table, the troubleshooting flowchart and the seven-step upgrade procedure are senior grade.

Five problems:
1. Source leaks: "The project's operations notes (Volume 10) record the reasoning"; "In the book's examples, CUDA 13.x needs".
2. Editorial markers left in reader text: "(flag: verify before choosing)", "(flag)".
3. Off-topic bullets inside "Installation methods and pitfalls": nvcc fatbin/PTX, MLPerf on OpenShift "< 2%", clock locking, PyTorch allocator, TensorFlow memory growth.
4. Internal inconsistency: body lists "six groups" of DKMS failures, checkpoint Q6 and exercise 3 ask for "five".
5. Wrong cross-reference: "(chapter 6.x on BCM and Redfish)"; BCM and Redfish are Parts 7 and 8.

Factual issues: the sysctl table gives `kernel.yama.ptrace_scope` a typical value of 1 next to "MPI CMA"; CMA single-copy in Open MPI and UCX needs 0 or `CAP_SYS_PTRACE`, so state which. `PYTORCH_ALLOC_CONF` "(formerly `PYTORCH_CUDA_ALLOC_CONF`)" needs checking against the PyTorch version the book assumes.

Missing for a beginner: a one-paragraph explanation of what "kernel ABI" means before kABI and `weak-updates` appear.

Missing for an expert: GPU Operator precompiled driver containers and their kernel-version matching in practice; NVIDIA's driver/kernel support matrix cadence; a note that Secure Boot plus open modules signed by distributions (Ubuntu signed `linux-modules-nvidia`) removes the MOK step.

Rewrite instruction: Remove the leak sentences and "(flag)" markers; move the fatbin, container overhead, clock-lock and allocator paragraphs to Part 10 and leave one link. Make DKMS failures consistently five or six everywhere. Fix the cross-reference. Cut the 20 checkpoint questions to 10 that test diagnosis, not recall.

### 3.3 Chapter 2.19 Queuing, QoS, ECN, PFC and DCB

Strengths: one of the best chapters in the set. The problem-first opening, the honest "1:1 still congests" table, PFC frame details, watchdog stages, DCQCN threshold ordering and the troubleshooting flowchart are correct and practical.

Five problems:
1. Arithmetic error (see section 6): "A 64-byte packet queued behind it waits 14 times its own serialization time."
2. "In AI fabrics, 1:1 overprovisioning is the baseline" uses the wrong term; it means non-oversubscribed.
3. The threshold rule "XON < ECN (Kmin/Kmax) < XOFF" is stated as if both live in one queue; PFC thresholds are on ingress priority-group buffers and ECN on egress queues, often in a shared buffer with dynamic thresholds.
4. SFC sentence "being specified as an IETF- and IEEE-style standard" is vague; P802.1Qdw is an IEEE project.
5. The CSIG bullet carries five nested attributes in one sentence; beginner-unreadable.

Factual errors: the 14x figure (should be about 140x: 9,000 bytes is 140.6 times 64 bytes).

Missing for a beginner: a two-sentence contrast with InfiniBand's credit-based flow control, which PFC imitates.

Missing for an expert: shared-buffer alpha/dynamic thresholds, lossy RoCE with selective repeat (now common with ConnectX-7 and later), NVIDIA Spectrum-X adaptive routing plus its congestion control as the current production alternative to DCQCN-only.

Rewrite instruction: Fix the arithmetic and the term; add a paragraph "Where the thresholds live" (ingress PG vs egress queue, shared buffer); add a short "Lossy RoCE today" paragraph with the conditions under which teams drop PFC. Leave the rest.

### 3.4 Chapter 3.6 Concurrency: threads, processes and asyncio

Strengths: the decision diagram, bounded concurrency, `bounded_map`, the asyncio worker-pool template, retries with full jitter and the pitfalls table are excellent and directly useful for fleet tooling.

Five problems:
1. Book transcription: four paragraphs narrate *Fluent Python* spinner scripts down to `for char in itertools.cycle(r'\|/-'):`.
2. Author-laptop numbers presented as facts: "`~40.81s`", "`10.39s` with 6 processes", "`7.18s`".
3. Example citations leak: "`Example 20-6`", "`Example 21-18`", "Examples 19-1 to 19-13".
4. The asyncio example uses `aiohttp` without importing it and passes `timeout=5` where aiohttp expects a `ClientTimeout`; `retry` uses `random` without import.
5. Exercises 1 to 5 are about the book's demo files, not infrastructure fan-out.

Factual errors: the comment "default in 3.14 on Linux" under spawn is wrong; Python 3.14 changed the Linux default start method to `forkserver`, not `spawn`. "`paramiko` clients, database connections and `boto3` clients are generally safe for concurrent use" is wrong for paramiko and DB-API connections in general; only `boto3` clients carry that guarantee.

Missing for a beginner: a picture of what the event loop does on one tick.

Missing for an expert: free-threaded 3.14 status for real dependencies (NumPy, PyTorch), and `uvloop`/`anyio` trade-offs in production services.

Rewrite instruction: Replace the spinner and flags narrative with one short timed experiment the reader runs (sequential vs threads vs processes on a hash workload). Delete book example numbers and laptop timings. Fix the two errors. Make all six exercises infrastructure fan-out tasks (BMC poll, node health, S3 copy).

### 3.5 Chapter 4.19 Terraform state in depth

Strengths: complete and correct: state anatomy, backends with current locking (`use_lockfile`, DynamoDB deprecation), locking discipline, layout, `moved`/`import`/`removed` migration, recovery table, drift handling and secret exposure. A senior engineer would recognise their own runbook.

Five problems:
1. Book walkthrough intrudes: "Yevgeniy Brikman details why this fails in Chapter 3"; the stage/prod/mgmt layout and webserver-cluster with MySQL port 3306.
2. AWS-first examples in a book whose labs are GCP and Nebius; GCS gets three lines.
3. Mermaid diagram labelled "Read the diagram from top to bottom" but drawn left to right.
4. Exercises 1, 2 and 4 instruct the reader to follow the book's chapter.
5. Common mistakes section is a run-on list in paragraph form.

Factual errors: none found.

Missing for a beginner: a one-line explanation of what "lineage" protects against, before it appears in a table.

Missing for an expert: Nebius object storage as an S3-compatible backend (endpoint and locking caveats), and workload-identity federation for GCS state in CI.

Rewrite instruction: Replace the book layout paragraph with the handbook's own `infra-live` layout already shown; move GCS to the first backend example and add a Nebius S3-compatible example; remove book citations from exercises.

### 3.6 Chapter 5.9 The kubelet and the node

Strengths: the production KubeletConfiguration with GPU comments, allocatable arithmetic, CPU/Memory/Topology Manager guidance (relaxed for 8-GPU training, strict for small inference), eviction vs OOM vs API eviction, leases and taints, and the troubleshooting table are excellent.

Five problems:
1. Sections "Liveness probes, step by step" to "Startup probes for slow-starting applications" are pasted book material that repeats section 5 in another voice: "Example 5-2 adds a liveness probe to the `kuard` container."
2. Leaks: "The book covers Kubernetes Services in its Chapter 7"; "the book calls it a recent addition".
3. Contradictory probe arithmetic: "When more than three consecutive probes fail" and "When the last 10 probes have failed".
4. Docker-era event text: "Killing container with id docker://2ac946...".
5. The OOMKilled sample shows "Exit Code: 1" without comment; readers will memorise the wrong code.

Factual errors: "It samples node signals... at `evictionPressureTransitionPeriod` intervals" is wrong; the eviction manager runs on the housekeeping interval (10 s); `evictionPressureTransitionPeriod` (default 5m) is how long the node waits before leaving a pressure condition. `--node-monitor-grace-period` is given as 40 s; recent releases raised the default to 50 s (needs checking against the Kubernetes version the book targets).

Missing for a beginner: a sentence on why the kubelet watches pods by `spec.nodeName` (it is how scheduling becomes local action).

Missing for an expert: kubelet behaviour with DRA drivers and the device-plugin to DRA migration path; `MemoryQoS` and swap support status.

Rewrite instruction: Delete the five pasted probe subsections and keep section 5's own table and guidance, adding one compact YAML example with a startup probe sized for a 300-second model load. Fix the two factual points, the exit-code example (137 for SIGKILL) and the failure-count sentences.

### 3.7 Chapter 5.32 Project A: GPU node health operator

Strengths: the best chapter in the set. Clear requirements, pure decision core, honest "What the tests do not prove", rehearsal table, sensible extension ideas. Voice is human and calm.

Five problems:
1. Design contradiction: `Judge` treats an absent condition as `Healthy` immediately, with no `healthyFor` window. A detector outage would therefore release every cordon the policy owns on the next reconcile, which contradicts the rehearsal row "existing cordons stay until recovery rules say otherwise".
2. The subsection "How this operator fits into the full GPU platform layer (`volume-10`)" lists internal repository file paths the reader does not have.
3. "Table tests cover `Judge` with six cases" sits next to an eight-row decision table.
4. Exercise 6 uses LaTeX "$> 25\%$", which renders badly and breaks the plain-text rule.
5. Extension 7 cites "(5.22)" for SBOM signing; supply chain is 5.27.

Factual errors: none beyond the design contradiction.

Missing for a beginner: one paragraph on what a node condition is and who normally writes one (kubelet vs NPD).

Missing for an expert: the circuit breaker should be part of the core, not an extension, given the stated threat; leader election is discussed but `RequeueAfter` behaviour after leader change is not.

Rewrite instruction: Make absent conditions neither act nor release (same as Unknown), or require `healthyFor` before release, and update the decision table, code, Python sim and failure table to agree. Replace the volume-10 subsection with three plain sentences on where detection, scheduling and remediation live (Parts 10, 11, 17). Fix the counts and the cross-reference.

### 3.8 Chapter 6.12 Multi-node training on Slurm

Strengths: the layer model (Slurm, launcher, rendezvous, NCCL), the two launch styles, the tested glue code, the NCCL variable table sourced from `env.rst`, and the failure table are senior-grade and interview-ready.

Five problems:
1. Sections 7 and 8 dump book tables and numbers: Llama 3 interruption breakdown with nine categories and percentages; "which the book writes as `200.00 ms`".
2. LaTeX in prose: "$8.03\text{B} \times 2\text{ bytes} = \mathbf{16.06\text{ GB}}$".
3. Inconsistent launch example: "`srun torchrun --nproc_per_node=1 --nnodes=...`" for an 8-GPU node, copied from the source.
4. First-person drafting voice: "the clean venv I used did that".
5. Duplicated guidance: `NCCL_BUFFSIZE`, socket limits and channels appear in the table and again in 8.2 item 3.

Factual issues: the status table says the glue ran with "PyTorch 2.14.1"; that version needs checking. The gloo vs NCCL figure (400 MB at 2 GB/s, 200 ms) ignores ring all-reduce's 2(N−1)/N traffic factor; state it as a lower bound. "start at `4 MB`" for `NCCL_BUFFSIZE` restates the default.

Missing for a beginner: why `MASTER_ADDR` must be an address every node can reach on the right interface, shown as a two-node picture.

Missing for an expert: PyTorch flight recorder usage (`TORCH_NCCL_TRACE_BUFFER_SIZE`, dump on timeout), and NCCL RAS (`ncclras`), which 6.31 uses but this chapter only lists.

Rewrite instruction: Cut section 8.1 to the six pitfall names with one sentence each; cut the Llama 3 list to one sentence ("about 8 unplanned interruptions a day on 16,384 GPUs"); remove LaTeX and the 8B checkpoint arithmetic (move to 6.21); fix the torchrun example; add a short flight-recorder and `ncclras` subsection.

### 3.9 Chapter 6.31 Capstone: build and operate a small Slurm GPU cluster

Strengths: the single-source-of-truth pipeline with a real generator and a self-check, the eight-layer build order, the ten acceptance gates, and the frozen-job triage sequence are valuable and realistic.

Five problems:
1. Persona and generator voice: "Senior Systems Architect Answer", "Preserve the crime scene first", bold-heavy tables whose cells carry full explanations.
2. Leak: "(`volume-10/00c-slurm-bcm-interview-lab.md`)".
3. LaTeX arrows in tables: "Epilog/NHC exits non-zero $\rightarrow$ `scontrol update`".
4. Depends on Parts 7 and 8 (BCM `cmha-setup`, `cm-scale`, Redfish URIs) which the reader has not reached; section 7 "myths" is BCM content.
5. Opening paragraph is a recap list of 15 technologies in four sentences.

Factual issues needing checks: "returns 75 SEL members per page"; BMC password "13 to 20 characters"; Gate 5 "~350–390 GB/s" busbw on H100 NVSwitch (depends on NVLS and NCCL version); BCM HA described as requiring "shared NAS storage" (verify whether BCM 11 also supports HA without shared storage). "all `18` NVLink lanes per H100" should say links.

Missing for a beginner: a small-cluster version (6 nodes) of the build order that does not assume DGX SuperPOD hardware.

Missing for an expert: SLO definition for the cluster (goodput, queue wait, node availability) and how the acceptance baselines feed alerts.

Rewrite instruction: Move section 6.1 facts and section 7 BCM myths to Part 8 (or to a later cross-part capstone); convert the junior/senior table into a short prose section "How to structure an answer"; replace LaTeX arrows with numbered steps; rewrite the opening as one situation paragraph.

### 3.10 Chapter 7.10 Firmware inventory and the UpdateService

Strengths: the clearest explanation in the book of why a successful task is not an active update, with a mock that proves it and a tool that exits 7 when activation is missing. Pull vs push, `Targets`, `OnStartUpdateRequest` staging and the BCM mapping are correct and practical.

Five problems:
1. Notebook voice and leaks: "The user's notes tell this story", "My tool reads", "I have not run `nvfwupd`".
2. Section 8.1 is a different author: UFM SM priorities, GDS `cufile.json`, `nvidia-fs 2.25.7+`, LaTeX arrows; it belongs in Parts 12 and 13.
3. Broken sentence: "so you know what a failure means., and the groups below show what each one covers."
4. Exercise 1 says the 46-check lab "should show `45` / `46` checks pass", which reads as a known failure.
5. Section numbering jumps from 9 to "Exercises" to 11.

Factual issues: "The default is `15`" for SM priority needs checking (OpenSM's default `sm_priority` is 0; UFM may set its own); `mstflint` "unbundled from `MLNX_OFED 24.07`" and the `nvidia-fs 2.25.6` bug need checking.

Missing for a beginner: a picture of where firmware lives on a DGX (motherboard tray vs GPU tray) before the 30-component list.

Missing for an expert: rollback realities (ERoT anti-rollback, `LowestSupportedVersion`), and how to schedule AC power cycles through PDUs safely at rack scale.

Rewrite instruction: Replace "the notes"/"my" sentences with neutral statements of what was tested and what was not (one status note at the end). Delete section 8.1 and leave a link to the fabric and storage chapters. Fix the sentence, the check count and the numbering.

### 3.11 Chapter 8.12 High availability and head node failover

Strengths: a model chapter for teaching dangerous operations: split brain, fencing, quorum, STONITH, power-off vs pulled cable, update order, and a second-by-second failover timeline. Correct and cautious.

Five problems:
1. Manual section numbers in headings: "## 6. Building and checking the pair (15.2)".
2. Internal vendor ticket in reader text: "(a known stall, internal reference BCM-31089)".
3. "master-slave" terminology without the modern "primary/replica" alias.
4. Exercise 1 path "Run `python3 ha_lab.py`" lacks `code/part08/`.
5. Section numbering: "## 10", "### 10.1", "## Exercises", "## 12."

Factual errors: none found.

Missing for a beginner: one sentence on what CMDaemon is before it appears.

Missing for an expert: how Slurm controller HA (`SlurmctldHost` backup) interacts with BCM HA when both are configured, beyond the takeover script mention.

Rewrite instruction: Light edit only: remove section numbers from headings, drop the ticket id, fix paths and numbering.

### 3.12 Chapter 9.5 GB200 and GB300 NVL72 rack-scale systems

Strengths: the crossbar arithmetic, the BCM dual-protocol firmware table (Redfish for compute trays, NVOS REST for switch trays, 2 vs 3 packages) and the MoE motivation are valuable.

Five problems:
1. Two voices spliced: generator sections ("Dissect the front and rear", "In one minute" boxes) alternate with plainer book summaries ("Preintegrated rack appliance", "Liquid cooling loop") that repeat and contradict them.
2. Empty H2 "Concepts: basics → intermediate → advanced" immediately followed by another H2.
3. Meta commentary on the source: "The book itself summarizes the gain as 'roughly 30×'" next to a computed 44.12x.
4. Bold-heavy tables carrying explanations (compute tray subsystems, power shelf features).
5. Dated expansion: "SLURM (Simple Linux Utility for Resource Management)".

Factual errors: "power is distributed to each 1U compute node, where AC is converted to DC" contradicts the chapter's own busbar description; the power shelves convert AC to 48–54 V DC and the trays receive DC. "The NVL72 is fully liquid cooled" contradicts the table's "hybrid liquid+air cooling"; NVL72 racks still use some air cooling. Power is given as 120–130, 130, 130–150 and "~150 kW" in different places. GB300 "36 × 500 GB" LPDDR5X needs checking.

Missing for a beginner: why a copper backplane limits the domain to one rack (reach), stated before the optics power argument.

Missing for an expert: failure domains inside an NVL72 (what happens to a job when one compute tray or one switch tray fails; NVLink partitions via NMX-M), which is the operational question.

Rewrite instruction: Rewrite as one voice in plain prose: (1) why the rack became the unit, (2) tray anatomy, (3) crossbar math in one block, (4) power and cooling with one consistent number and the AC/DC path corrected, (5) firmware management, (6) failure domains and partitions. Remove "In one minute" boxes, LaTeX and the source meta-commentary; pick one speedup and attribute it in Sources.

---

## 4. Cross-cutting patterns and mechanical instructions

1. **Source leakage (the biggest single fix).** "the book" 485 hits in 77 chapters; `volume-N` or "Volume N Chapter" 445 hits in 100 chapters; "the notes"/"user's notes" 100 hits in 30 chapters; "Example N-N" 268 hits in 26 chapters. Instruction: in body text, replace "The book says X" with "X"; replace "the book's example uses Y" with an example the handbook owns; delete every `volume-*` path and "Volume N Chapter M" reference; delete "Example N-N" numbers and book file names. Attribution goes only in "Sources and review notes".

2. **Source abbreviations in headings and exercises.** `HLW`, `LP`, `AUR`, `TUR`, `NPA`, `KUR`, `SCL`, `DAI`, `ASP` in backticks: 215 hits in 62 chapters. Instruction: headings never carry a source tag or a manual section number; delete the parenthetical. In exercises, delete "This exercise draws on chapter N of *Book*".

3. **Drafter first person.** "my tool/lab/mock", "I have not run", "the clean venv I used": 49 hits in 14 chapters, mostly Part 7 and 6.12. Instruction: rewrite as "The lab tool..." and move test status to one sentence in the review notes ("Not run against real hardware").

4. **"(untested here)" noise.** 1,150 inline occurrences in 160 chapters. Instruction: remove inline tags; put one status line above each lab block ("Commands below were not run on live hardware").

5. **Status tables at chapter top.** 188 chapters open with a Level/Tier/Venue/Status table that repeats front matter and tells the reader the chapter is "Drafted, labs untested". Instruction: delete the table; keep front matter; keep at most "Lab venue" as one sentence in Prerequisites.

6. **Exercise blocks.** Pattern: "1. **Title Case With (`code`) vs. (`code`):** (a)... (b)... State the exact..., using `func()` in `code/partNN/x.py`". Instruction: each exercise starts with a one-sentence situation, asks one thing, is at most 60 words, names at most one file, and never cites a book chapter. Six exercises per chapter maximum.

7. **Fourfold repetition.** Body + Interview angles + Exercises + "Checkpoint questions (20)" (190 chapters). Instruction: cut checkpoints to 8 to 10 questions; delete any whose answer is a copy of a body paragraph; keep questions that require applying the idea to a new situation. Interview angles stay, without answers.

8. **LaTeX in prose and tables.** `$\rightarrow$`, `$\mathbf{...}$`, `$> 25\%$`: 178 hits in 52 chapters. Instruction: replace with words or plain characters ("then", "→" only in diagrams), and move any formula into a fenced text block after the explanation.

9. **Generator voice fingerprints.** "Concepts: basics → intermediate → advanced" empty H2 (13 chapters, all Part 9 plus some), "In one minute" admonitions, "workload physics", "inert silicon", "golden reference", "Senior Systems Architect", bolded table cells longer than 15 words. Instruction: delete the empty H2; delete "In one minute" boxes; turn table cells that contain sentences into prose; ban the listed phrases.

10. **Formulaic section closers.** Language rule 12 produced a closing "Before you X, check Y" after nearly every section, often restating the paragraph above. Instruction: keep at most one closing decision sentence per H2 and only where it names a real decision; delete closers that repeat the previous sentence.

11. **Openings that list undefined terms.** For example 2.2 lists 11 acronyms in its first paragraph. Instruction: an opening names at most three technical terms and defines each in plain words at first use.

12. **Structure defects.** Titles ending with "." (6.1 to 6.6, 6.8); section numbering gaps (7.10, 8.12 and others); Part 8 lab commands without `code/part08/`; wrong cross-references (1.22 "chapter 6.x on BCM", 5.32 "(5.22)" for SBOM). Instruction: run a script that (a) strips trailing full stops from titles, (b) checks H2 numbering is consecutive or removes numbers, (c) checks every `python3 X.py` has a `code/partNN/` path that exists, (d) checks every "chapter N.M" cross-reference title matches its topic.

13. **Chapter length.** 39 chapters in Parts 1 to 6 exceed 11,000 words. Instruction: any chapter over 14,000 words is split at its natural seam (listed in the table); any chapter over 11,000 words cuts duplicated reference tables before anything else.

---

## 5. Priority rework list (40 chapters, ranked)

1. **3.16** Cut. Delete the file and remove it from the sidebar; add one line to 3.4's Sources pointing readers to *Learning Python* Part VI for full OOP coverage. Move nothing; 3.4 already covers what infrastructure engineers need.
2. **3.14** Cut. Same treatment; 3.1 and 3.11 cover scopes, arguments and closures. Check 3.11 still explains `nonlocal` in two sentences.
3. **3.12** Cut. Same; add to 3.1 a short table of built-in types and their mutability if missing.
4. **3.17** Cut. Same; ensure 3.5 covers `except*` and text vs bytes in a paragraph each.
5. **3.13** Cut. Same; 3.1 covers statements and iteration.
6. **3.15** Cut. Same; 3.2 covers imports and packages.
7. **0.1** Rewrite chapter per review 3.1: delete manufacturing/policy content, keep the opening, layers, roles and checkpoints, add "training job end to end", "inference request end to end" and "what goes wrong at scale". Target 2,500 words.
8. **9.5** Rewrite chapter per review 3.12 in one voice; fix AC/DC path, cooling statement and power figures; add NVL72 failure domains and NVLink partitions.
9. **9.13** Rewrite chapter as "Capacity planning for an SRE": start with a concrete question (will the fleet run out of power in 12 months), keep the worked calculations, delete Solutions Architect framing and all "Volume N" references.
10. **6.31** Rewrite sections per review 3.9: move BCM/Redfish facts and the myths table to Part 8, convert junior/senior table to prose guidance, remove LaTeX and the volume path, rewrite the opening.
11. **7.10** Rewrite sections per review 3.10: neutral voice, delete section 8.1, fix broken sentence, 45/46 check, numbering.
12. **5.9** Rewrite sections per review 3.6: delete pasted probe subsections, fix eviction-interval and probe-count errors, fix the exit-code example.
13. **6.12** Rewrite sections per review 3.8: compress book tables, remove LaTeX and first person, fix torchrun example, add flight recorder and `ncclras`.
14. **5.32** Fix the absent-condition design contradiction in prose, Go code, Python sim and tables; replace the volume-10 subsection; fix counts and cross-reference.
15. **3.6** Rewrite sections per review 3.4: replace Fluent Python narrative with a reader-run experiment; fix forkserver and thread-safety errors; infrastructure exercises.
16. **9.12** Rewrite sections in plain voice; delete "Volume 21 Chapter 6 Part 3.2" style references; cut overlap with Part 8 to links; keep the software pyramid and the Kubernetes multi-node job primitives.
17. **9.1** Rewrite sections: replace drama openings with one concrete purchase mistake; define the four "workload physics" dimensions plainly or drop the term; fix and explain the KV-cache exercise formula.
18. **9.2** Rewrite sections: keep tray anatomy and dual-BMC explanation, drop "Senior infrastructure engineers never trust" tone, average sentences under 18 words.
19. **9.11** Rewrite sections and make it the canonical facility deep dive; 6.30 stays as the beginner primer, and 8.15 and 9.7 link here for shared numbers.
20. **9.3** Rewrite sections: source or remove "40 to 50 percent slower" and "15 percent discount"; keep the DGX vs OEM support-boundary material.
21. **9.6, 9.7, 9.8, 9.9, 9.10, 9.14** (counted as one item) Rewrite sections for voice: delete the empty "Concepts" H2, cut sentence length, convert explanation-bearing table cells to prose, and verify every hardware number against the named NVIDIA reference architecture.
22. **1.27** Rewrite sections: cut by half; keep "why a cloud GPU node behaves differently" (noisy neighbours, nested virtualization, SR-IOV, NUMA exposure); delete cloud-history material.
23. **1.23** Rewrite sections: keep USE, workload characterisation and drill-down with one GPU-cluster worked example; delete vocabulary lists; add a failure section.
24. **1.26** Rewrite sections around GPU passthrough, vfio, IOMMU groups and KubeVirt; remove "Gregg's Config A/B" framing.
25. **1.22** Rewrite sections per review 3.2.
26. **2.2** Rewrite sections: opening with one packet story and at most three defined terms; drop circuit switching, ATM and OpenFlow history to a paragraph.
27. **2.14** Rewrite sections: one page on why distance-vector is legacy, then OSPF/IS-IS underlay operations (adjacency states, MTU EXSTART, LSDB checks).
28. **2.17** Rewrite sections: VXLAN and EVPN for GPU clouds in depth; SR, SRv6 and SD-WAN reduced to a comparison paragraph.
29. **2.21** Rewrite sections: replace generic threat taxonomy and dated vulnerability text with AI-cluster threats (BMC exposure, RDMA fabric isolation, model-weight exfiltration, crypto-mining) and controls.
30. **2.32** Rewrite sections: GCP VPC-native GKE, multi-NIC GPU VMs, Nebius networking; reduce AWS/Azure primer and cloud-model taxonomy to a table.
31. **2.16** Rewrite sections: replace the prose figure transcription with a mermaid diagram; keep RFC 7938 design reasoning.
32. **3.1** Rewrite sections: split into "Python core" (types, names, functions) and move REPL and execution-model trivia to an appendix; remove `LP` tags.
33. **3.3** Rewrite sections: replace FrenchDeck and other book examples with infrastructure objects (a node inventory that supports `len`, slicing, iteration).
34. **3.11** Rewrite sections: keep "how frameworks work" goal; show FastAPI dependency injection and pydantic validators as the worked cases; cut generic metaclass catalogue.
35. **6.1** Rewrite sections: delete fog computing and marketing-rank history; keep TOP500/HPL and HPC vs AI factory comparison; fix title punctuation.
36. **6.2** Rewrite sections: cut by 40 percent; keep node roles and wrong-workload-on-wrong-node incidents.
37. **6.24** Rewrite sections: delete NIS/NIS+ setup and ext3 quota commands; keep LDAP/SSSD, UID consistency and filesystem quotas on Lustre/Weka.
38. **6.30** Rewrite sections: remove source-book error commentary and adopter anecdotes; make it a beginner primer that links to 9.11.
39. **8.14** Rewrite sections in plain voice: turn bold "Zone" lists into prose steps; keep the staging-host matching rule.
40. **8.16** Rewrite sections: remove version-specific bug notes or move them to a dated "known issues" box; re-verify Mission Control scope against current NVIDIA docs.

---

## 6. Technical correctness watch list

| Chapter | Claim | Assessment and evidence |
|---|---|---|
| 2.19 | 64-byte packet behind a 9,000-byte packet "waits 14 times its own serialization time" | Wrong. 9,000 / 64 = 140.6, so about 140 times (0.72 ms vs 5.12 µs at 100 Mb/s). |
| 2.19 | "In AI fabrics, 1:1 overprovisioning is the baseline" | Wrong term; non-oversubscribed (1:1) is meant. |
| 3.6 | spawn is the "default in 3.14 on Linux" | Wrong. Python 3.14 changed the default start method on Linux to `forkserver` (What's New in Python 3.14, multiprocessing). |
| 3.6 | paramiko clients and database connections "generally safe for concurrent use" | Wrong as a general rule; DB-API connections vary (`threadsafety` attribute), sqlite3 is not shareable by default, paramiko SSHClient sessions are not designed for concurrent use. Only boto3 clients are documented thread-safe. |
| 3.6 | `session.get(..., timeout=5)` with aiohttp | aiohttp expects `aiohttp.ClientTimeout`; integer support is deprecated. Needs checking against pinned version. |
| 5.9 | Eviction manager samples "at `evictionPressureTransitionPeriod` intervals" | Wrong. It runs on the housekeeping interval (10 s); `evictionPressureTransitionPeriod` (default 5m) delays leaving a pressure condition (Kubernetes node-pressure eviction docs). |
| 5.9 | `--node-monitor-grace-period` default 40 s | Raised to 50 s in recent releases; needs checking against the targeted Kubernetes version. |
| 5.9 | OOMKilled example "Exit Code: 1" | Misleading; OOM-killed containers normally report 137 (SIGKILL). Annotate or replace. |
| 5.9 | "When more than three consecutive probes fail" | With `failureThreshold: 3`, the restart follows three consecutive failures, not more than three. |
| 5.32 | Absent condition treated as Healthy without `healthyFor` | Design contradiction: owned cordons would be released immediately on detector outage, contradicting the chapter's failure table. |
| 6.4 | `OMPI_MCA_btl=^tcp,self,openib` | Excluding `self` breaks loopback sends with the ob1 PML; `openib` was removed in Open MPI 5. Use `^tcp,openib` for Open MPI 4 or `--mca pml ucx`. |
| 6.12 | "PyTorch 2.14.1" in the tested status | Needs checking; version appears too high for late 2026. |
| 6.12 | `srun torchrun --nproc_per_node=1` for 8-GPU nodes | Inconsistent with the chapter's own 8 ranks per node. |
| 6.12 | gloo 400 MB at 2 GB/s takes 200 ms | Ignores ring all-reduce traffic factor 2(N−1)/N; present as lower bound. |
| 6.12 | "Creating 32 separate communicators... 2–3 minutes" | Unsourced; needs checking or removal. |
| 6.15 | 22.05 to 26.05 needs "three intermediate hops" | Depends on Slurm's supported upgrade window (historically two prior major releases, changed in recent releases); needs checking against the Slurm upgrade guide. |
| 6.31 | BCM HA uses "shared NAS storage — not Pacemaker + DRBD" | The Pacemaker point is right; whether shared storage is mandatory needs checking against the BCM 11 manual (8.12 also implies NAS). |
| 6.31 | SEL "75 entries per page"; BMC password 13–20 characters | Needs checking against the DGX H100/H200 User Guide. |
| 6.31 | Gate 5 busbw "~350–390 GB/s" on H100 NVSwitch nodes | Depends on NVLS and NCCL version; NVLS can exceed this. Needs checking. |
| 6.31 | "all 18 NVLink lanes per H100" | Terminology: 18 links, each of several lanes. |
| 7.10 | SM priority default 15 | OpenSM default `sm_priority` is 0; verify UFM's default before stating. |
| 7.10 | `mstflint` unbundled from MLNX_OFED 24.07; `nvidia-fs` 2.25.6 P2P bug | Needs checking against release notes. |
| 9.5 | AC converted to DC in each compute tray | Wrong; NVL72 power shelves convert AC to a 48–54 V DC busbar, as the chapter's own diagram states. |
| 9.5 | "The NVL72 is fully liquid cooled" | Contradicts the chapter's "hybrid liquid+air"; NVL72 racks retain some air cooling. |
| 9.5 | Rack power 120–130, 130, 130–150, ~150 kW | Inconsistent across sections; pick sourced GB200 and GB300 figures. |
| 9.5 | GB300 Grace memory "36 × 500 GB" | Needs checking against the GB300 SuperPOD RA. |
| 9.5 | "Grace CPUs (2,592 cores)" | 36 × 72 = 2,592, consistent; keep. |
| 9.7 | "Blackwell SXM6" | Module naming needs checking. |
| 9.1 | KV-cache exercise "8 bytes per token element" | Formula unclear; standard is 2 × layers × hidden × bytes per element per token. Needs rewrite. |
| 9.3 | OEM HGX "40 to 50 percent slower", "15 percent discount" | Unsourced; remove or source. |
| 0.1 | "IBM AC922 cluster has 4,608 servers" | Misnamed: that is Summit (ORNL), built from AC922 nodes, now retired. |
| 1.22 | `kernel.yama.ptrace_scope` typical 1 with "MPI CMA" | CMA single-copy needs 0 or CAP_SYS_PTRACE; state the conflict explicitly. |
| 1.22 | DKMS failure groups six vs five | Internal inconsistency. |
| 1.22 | "chapter 6.x on BCM and Redfish" | Wrong cross-reference (Parts 7 and 8). |
| 1.22 | `PYTORCH_ALLOC_CONF` "(formerly `PYTORCH_CUDA_ALLOC_CONF`)" | Needs checking against PyTorch release notes. |
| 4.3 | Grant the automation group `NOPASSWD: ALL` | Not wrong for many fleets, but needs a scope caveat (dedicated account, no interactive login, audited). |
| 5.32 | "(5.22)" for SBOM | Wrong cross-reference; supply chain is 5.27. |
| 7.10 | Lab "should show 45 / 46 checks pass" | Inconsistent with "46 checks"; verify the lab. |

---

## 7. Structural advice

1. **Remove 3.12 to 3.17.** They are 178,000 words of language reference with copyright exposure and no infrastructure content; 3.1 to 3.11 already cover the language at the needed depth.
2. **Add a bridge chapter 0.4 "A tour of a GPU node and a training job".** Parts 1 to 6 use NVSwitch, Fabric Manager, Xid, NCCL and DCGM from the first chapter, but the reader meets GPU hardware only in Part 9 and CUDA in Part 10. One 3,000-word tour (node anatomy, a job from `sbatch` to all-reduce, an inference request) gives every later "Picture a GPU node..." opening something to stand on.
3. **Fix the Part 6/7/8 ordering.** 6.22 (head node installer steps), 6.23 (compare with BCM) and 6.31 (BCM HA, `cm-scale`, Redfish URIs) depend on Parts 7 and 8. Either move Parts 7 and 8 before 6.22, or keep Part 6 generic and move all BCM and Redfish content in it to Parts 7 and 8, with the capstone's interview section moved to a cross-part capstone after Part 9.
4. **One canonical home per topic, with links elsewhere.**
   - Facility power and cooling: 6.30 (primer) and 9.11 (deep); 8.15 section 5, 9.5 power, 9.7 keep only their specific numbers and link.
   - Firmware update: 7.10 (Redfish) and 8.7 (BCM); 9.5 section 5 and 8.16 link to them.
   - Containers on Slurm: 6.13 (enroot/pyxis) and 6.29 (Apptainer); 8.10 covers only the BCM wrapper.
   - Hand-built container networking: 1.20 (kernel lab) and 2.25 (networking); 5.13 links back instead of rebuilding.
   - SSH: 1.5 for daily use; 1.29 becomes a reference appendix or merges into 1.5.
   - Load balancing: 2.20 owns algorithms; 5.10 and 5.12 link for theory.
5. **Rebalance Part 4.** Fifteen Ansible chapters against nine Terraform/GitOps chapters is skewed for a cloud GPU SRE. Merge 4.5 into 4.7 (inventory and variables), fold 4.8 into 4.6, replace 4.9's Django deployment with a GPU-node service deployment, and use the space for a CI pipeline chapter that runs Terraform plan/apply with OIDC against GCP and Nebius.
6. **Compress legacy networking.** 2.13 and 2.14 can become one chapter on routing control planes (convergence, link-state underlay, BFD), with RIP/EIGRP as a paragraph.
7. **Split the oversized chapters** listed with action "split": 1.7, 1.8, 1.12, 5.7.
8. **SRE framing is missing in Parts 0 to 9.** Monitoring chapters (2.31, 5.24, 6.26, 8.11) describe signals and tools but rarely define SLOs, error budgets or goodput targets for the systems they monitor. If Part 17 covers SRE practice, each of these four chapters should end with a short "SLOs for this layer" section that links forward, so the interview thread runs through the whole book.
