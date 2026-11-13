# Voice rewrite Part 2, pass D (chapters 2.27, 2.28, 2.29, and 2.15 exercise 5)

Uncommitted. Base commit eff242e. Gates run per file with HEAD as base.

## Guard and chain results
| File | Words before to after | Hard failures | New numbers flagged | Chain gate |
|---|---|---|---|---|
| 15-bgp-fundamentals.md | 8359 to 8381 | 0 | 0 | 0.0 |
| 27-lab-build-network-topologies-with-namespaces-frr-and-containerlab.md | 8400 to 10609 | 0 | 1 (`0% packet loss`, string from the validate.py check that already exists) | 0.0 |
| 28-network-automation-fundamentals-apis-yang-netconf-gnmi-sdn-templates.md | 12286 to 13660 | 0 | 1 (`9214`, the MTU value already in the ncclient and XML example; now also named in prose) | 0.1 |
| 29-network-automation-in-practice-ansible-nornir-and-ci-cd-for-networks.md | 11573 to 12964 | 0 | 1 (`3.12`, Python version already in the GitHub Actions example) | 0.0 |

No code block, Mermaid block, front matter, heading, checkpoint count or Sources section was changed. Exercises were changed only in 2.15 exercise 5.

## 2.15 exercise 5 (fixed)
- Old: "(a) Compare hot-potato, cold-potato and mashed-potato routing."
- New: "(a) Compare hot-potato and cold-potato routing. For each one, say whose network carries the traffic for longer, and name the BGP attribute you would change to get that behaviour."
- Why: "mashed-potato" appears nowhere in the chapter body. Body lines about 263 teach hot-potato (IGP cost step, LOCAL_PREF) and cold-potato (high LOCAL_PREF, honouring MED, selective advertisement). The new wording uses only those.
- Flag for owner: the Sources row for chapter 15 (book chapter 17) and the chapter intro (line 42) still mention "resource segmentation" and "flow pinning". The body does not teach either one. Sources were not touched. Decide whether to add a short body paragraph or drop the phrase from the intro.

## 2.27 (lab steps)
Added plain-language walkthroughs, no new facts or commands:
- Lab 1: the five experiments as one story (route get, MTU black hole, NAT with conntrack, rp_filter reply path).
- Lab 2: start_frr() flags one by one; R1.conf line by line; how to read experiments 1 and 2 (ExStart to Full, outage as lost pings times interval).
- Lab 3: fabric.clab.yml read top-down (container naming, binds, links); gen.py read in run order (LEAVES, SPINES, DAEMONS, templates, route-map CONN); the verification block explained command by command; experiment outcomes and how to read them.
- Lab 4: step 1 commands explained as separate jobs, plus a picture of the VXLAN path.
- Lab 5: encapsulation and ECMP hashing explained for items 1 and 4.
- Lab 6: DR mode in IPVS (MAC rewrite only), items 2 and 3 as measurements, tc netem in item 4.
- Lab 7: validate.py in three parts (sh, check, main loop, exit code).

## 2.28 (YANG, NETCONF, RESTCONF, gNMI, SDN, lab)
- YANG: rest of the module explained (namespace, container, list key, default, leaf-list, pyang tree).
- NETCONF: ncclient snippet line by line, including the OpenConfig namespace in the XML and what the confirmed commit timer does.
- RESTCONF: URL built from the model, PATCH versus PUT, status codes read in order.
- gNMI: path read left to right (keys, state versus config), gNMIc flags and each command, pygnmi snippet read as a story.
- Netmiko snippet explained line by line, including why the before-state is logged.
- SDN: Fibbing explained with a road-map analogy; BGP-as-SDN given a lived situation (controller pins a flow, withdraws it after the job).
- Lab section: notes on the YAML Norway problem, commit confirmed, and rollout habit.

## 2.29 (Ansible, Nornir, Terraform, CI, lab)
- Ansible inventory read top-down (groups, children, connection vars).
- Ansible playbook task by task (serial, max_fail_percentage, delegate_to, changed_when, eos_config options, handler, until/retries).
- Nornir: three-file merge order and env() password; dry_run and Result flags explained.
- Terraform: HCL resources read as promises; dependency graph from references; plan symbols (+, ~, -, -/+).
- CI workflow read job by job (on, needs, if: always(), environment approval gate, --limit canary).
- Lab steps 5 to 7 given a purpose (drift check, Batfish gate, injected failure).

## Facts to double-check (explanations added from general knowledge, not from a chapter source)
- 2.27: DR mode in IPVS rewrites only the destination MAC; backends hold the VIP on loopback. Standard IPVS behaviour, not checked against the IPVS docs here.
- 2.27: rp_filter strict mode drops a packet when the route back to its source does not leave by the arrival interface. Kernel behaviour, not run.
- 2.27: `nolearning` turns off flood-and-learn in VXLAN. `pvid untagged` maps untagged frames to the VLAN. Both from iproute2 and kernel docs, not run.
- 2.27: EBGP rejects a path that carries its own ASN (loop detection). Standard BGP behaviour.
- 2.28: YAML 1.1 reads a bare NO as boolean false (the Norway problem). Applies to PyYAML; not tested here.
- 2.28: commit confirmed rolls back on timer expiry; lock released when the ncclient block ends. Described from the ncclient usage in the chapter, not from its docs.
- 2.28: gNMI `state` (operational) versus `config` (intended) split in paths. OpenConfig convention.
- 2.29: Terraform plan symbols (+, ~, -, -/+). Standard Terraform output.
- 2.29: ansible `until` with retries 12 and delay 5 gives a 60 second window. Derived from existing values; the 60 second total was not written into the text.

## Needs source (none added as facts)
- None of the new text adds a number that is not already in the chapter's code or prose.

## Unresolved or not done
- Lab outputs were not run. Explanations describe only output the chapter already states (for example, ECMP two next hops, Established, `ExStart` to `Full`).
- Checkpoint questions and Sources sections were not touched in any of the four files.
- 2.27 exercises, 2.28 exercises and 2.29 exercises were not touched.
- Lab explanations are not human-read.
- 2.27 Sources row in 2.15 flagged above (resource segmentation and flow pinning).
- Build (npm run build), Mermaid check and language audit not run in this pass, since no Mermaid or front matter changed.
