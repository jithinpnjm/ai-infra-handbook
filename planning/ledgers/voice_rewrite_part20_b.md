# Voice rewrite, Part 20 chapters 04-06 (batch b)

Scope: `docs/part-20-nebius-sre-interview/04-files-descriptors-syscalls-and-permissions.md`, `05-cpu-memory-disk-and-the-scheduler.md`, `06-network-debugging-from-socket-to-switch.md`. Front matter, H1 and H2/H3 headings, code blocks, Mermaid, tables, checkpoints (18, 10, 10), lab step counts (04: 2 + 6, 05: 8, 06: 8), the Sources and review notes tail, "Explicitly labelled inferences" and "Not verified" kept from HEAD. Nothing committed. `planning/EXTERNAL_EDITS.md` not edited (run instruction).

## Word counts (`wc -w`)

| Chapter | Before | After | Growth |
|---|---|---|---|
| 04 files, descriptors, syscalls, permissions | 8302 | 10643 | +28.2% |
| 05 CPU, memory, disk and the scheduler | 9077 | 11635 | +28.2% |
| 06 network debugging | 10180 | 13050 | +28.2% |

## Gates (run on each file)

- `python3 tools/rewrite_guard.py HEAD WORKTREE <file>`: 0 hard failures on all three.
  - 04: new numbers 0, lost numbers 0, new code spans 2 (`df` and `du`, commands added in prose), lost 0.
  - 05: new numbers 0, lost numbers 0, new code spans 0, lost 0.
  - 06: new numbers 0, lost numbers 0, new code spans 0, lost 0.
- `python3 tools/restore/chain_gate.py <file>`: 04 = 0.0, 05 = 0.0, 06 = 0.1 (target 0.2 or lower, all pass).
- Span check (HEAD vs worktree, prose only, code fences excluded): `{}` on all three.
- Structure: code fences 14 / 18 / 32 unchanged; `<summary>` 18 / 10 / 10 unchanged; numbered lab and exercise lines 8 / 8 / 8 unchanged.
- Banned-pattern scan on prose (no "you will be able", no "should be able to", no exclamation marks, no raw `<` or `{` outside code, no "the book says", no "Volume N", no "untested here"): clean on all three after two fixes (04 "should be able to read" and 05 "should be able to say" reworded; 05 "the book says" became "as Systems Performance reports").
- Mermaid: diagram blocks are byte-identical to HEAD (the guard code-block check is zero). `node tools/check_mermaid.mjs` was not run in this batch. `npm run build` was not run (the run instruction says no npm build).
- Checkpoint answers and drill questions are byte-identical to HEAD, so the form rule holds.

## Honest status

- 04: one plain sentence above the lab says the steps were run in a container, not on a live server. The Not verified tail (locked) also carries the status.
- 05: one plain sentence above the lab says the lab steps were run on a Docker VM, not on a live GPU server.
- 06: the lab intro says the steps ran in a container and on a Mac, and were not run on a live cluster.

## Needs source (general explanations added, not in the original text)

Each item is general background that the original did not state. A reviewer should confirm or cut it.

- 04: the `open` call walk (name lookup, open file description with its own offset, lowest free slot in the table); the epoll description ("the kernel object a program uses to wait on many sockets"); the errno-as-envelope-label analogy; the room-and-door analogy for path search; "the owner class is decided first and the search stops there" (reading of path_resolution, reinforced by the original text); log rotation mechanism (writer keeps the old descriptor until told to reopen); the rescue step explanation (truncating through `/proc` leaves a sparse hole, the process keeps its offset); user namespace "phone book" analogy and the statement that a host user's files appear under a different number inside; "the mount check runs first" ordering for `EROFS` against mode checks; `fsGroup` as making a shared volume writable for a group the process belongs to; "USE stands for utilisation, saturation and errors" expansion; the tmpfs `nr_inodes` default explanation (from the kernel tmpfs page, already cited in the original).
- 05: CFS expansion (Completely Fair Scheduler); "verified" meaning in eBPF (kernel checks programs before they run); write-back caching meaning; transparent hugepage compaction latency; the pinned-page "reserved seats" analogy and the claim that the copy engine can read pinned pages without waiting; the claim that a working set is the part the kernel cannot give back cheaply (reasoning, not sourced); reclaim-order "drawers" analogy and the cost ordering; "direct reclaim" meaning; QoS expansion (quality of service); the hypervisor as the software that shares the physical machine; the NUMA interconnect explanation and the data-loader-on-wrong-socket walk; the "shop with a long line" and "bakery with one oven" analogies (no numbers); the power-of-two bucket description for `biolatency` (original names the buckets, the doubling is a general statement); the claim that a rented-desk analogy fits steal time; the statement that a line-by-line PSI reading shows load rising while pressure stops at its ceiling (reasoning from the original table).
- 06: MTU expansion (maximum transmission unit); SYN as the first handshake packet; SO_LINGER explanation; the hash table definition; middlebox definition; binary search analogy for half split; `app_limited`, `rwnd_limited`, `sndbuf_limited` meanings (general ss/TCP reading, the flags themselves are from the original); SYN flood definition; reception desk and waiting room analogy; the parking lot and guest list analogies; the claim that TIME_WAIT pressure "usually" comes from a client loop that opens a new connection per request (reasoning, not sourced); the PMTUD step sequence in plain words (ICMP too-big names the largest size, the sender lowers and retries); the radio channel analogy for idle timeouts; the walkthrough of a deploy-time connect spike healing by itself (scenario reasoning, not a measurement); the statement that streaming is one main way chat answers reach a user (general); the claim that pods on one node share that node's conntrack table (follows from the original's description of conntrack as per-node).

## Attribution check

- Gem books named by full title where the original named them. No abbreviations introduced.
- "the book says" in 05 section 11 became "as Systems Performance reports" (same attribution, named).
- No new attribution to a book or chapter was added. The new paragraphs cite nothing.

## Residue handling

- Test-log language in the lab and scenario outputs ("Ran: yes", "Real output", "Expected") is kept. It records facts that rule 9 says must not change, and the chapters have no separate Verification log. The locked Not verified tails carry the caveats. Rule 13 asked for test-log language to move to the Verification log, and that is not possible here without changing locked tail sections, so it was left in place and is listed under unresolved.
- First-person lines ("I created", "I did not read here", "that is my reasoning") kept as honest uncertainty in natural voice.

## Lab and exercise rule 9

- Lab steps and drill questions keep their counts and commands. Long lab lines in 04 Part B were split into shorter sentences (one situation per sentence, two numbers or fewer per sentence where the original allowed), without changing any number or command.
- Interview answers in 04, 05 and 06 keep their Question headings and bold question lines. Answer text was rewritten in teacher voice and kept in the original order: say the frame, name the first command, give the expected number, then the trade-off.

## Unresolved

1. 04 says "Three scenarios needed the container started with ..." (the unconfined seccomp and apparmor flags), but the lab lists four scenarios (3, 4, 7 and 9) as needing those flags. This is an inconsistency in the original text. Kept as-is; owner should decide whether it is "three" or "four".
2. 04 "Explicitly labelled inferences" and the "Not verified" tail are locked and were not touched. The tail still uses first-person and test-log wording, as in HEAD.
3. 05 and 06 use "Ran: yes" style lab lines (06) and "Real output" lines (05, 04). Kept as facts, see Residue handling.
4. 06 SHARP-style expansions were not present in this chapter, so no SHARP source question here. The MTU, SYN and SO_LINGER expansions are listed under Needs source.
5. `node tools/check_mermaid.mjs` and `npm run build` not run in this batch. Owner should run them before any commit.
6. Nothing committed. Owner go-ahead needed.
