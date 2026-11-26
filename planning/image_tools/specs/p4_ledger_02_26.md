# docs/part-02-networking/26-packet-capture-from-scratch-tcpdump-tshark-and-wireshark.md
- ## Why this matters for AI infrastructure | 250 | NO FIGURE NEEDED introductory motivation and high-level context
- ## Prerequisites and outcomes | 60 | NO FIGURE NEEDED prerequisite checklist and scope outcomes
- ## 1. How packet capture works | 650 | COVERED(p3-0226-drop-counters, p3-0226-tap-pipeline, m2-26-1)
- ### Capture points | 250 | COVERED(p3-0226-where-to-capture, n26-capturepoints)
- ## 2. tcpdump | 250 | COVERED(p3-0226-command-anatomy)
- ### What tcpdump shows on the wire | 300 | COVERED(p3-0226-read-conversation, n26-readcapture)
- ### Capture filter syntax (pcap-filter) | 380 | NEEDS FIGURE byte offset slicing and bitmask syntax anatomy across IP and TCP headers
- ### Primitives and operators | 130 | COVERED(n26-filters)
- ### Permission to capture | 150 | NO FIGURE NEEDED plain prose explaining ethics and capture permissions
- ## 3. tshark and Wireshark | 650 | COVERED(p3-0226-capture-to-event, p3-0226-filter-vs-display, p3-0226-silence-or-refuse)
- ## 4. Decoding the protocols you meet in AI infrastructure | 350 | COVERED(p3-0226-tcp-trace-signs, p2-0226-first-minute)
- ## 5. Capturing at scale and in awkward places | 750 | COVERED(p3-0226-mirror-options, p3-0226-pod-capture-steps, p2-0226-scale-ladder)
- ## 6. BPF-based tracing for networking (BCC and bpftrace) | 280 | COVERED(p3-0226-bpf-mechanism)
- ### BCC and bpftrace | 450 | COVERED(p3-0226-bpftrace-anatomy)
- ### Using BPF tools in network investigations | 250 | COVERED(p2-0226-bpf-question-tool)
- ## 7. A capture-driven troubleshooting workflow | 450 | COVERED(p3-0226-pattern-guesses, p3-0226-two-side-diagnosis, n26-workflow)
- ## 8. Hands-on lab: capture, read, and decode | 450 | COVERED(p3-0226-lab-ladder)
- ## 9. Common mistakes | 250 | COVERED(p3-0226-ssh-loop)
- ## 10. Interview angles | 120 | NO FIGURE NEEDED list of interview questions
- ## Exercises | 260 | NO FIGURE NEEDED student exercises list
- ## Checkpoint questions (20) | 1300 | NO FIGURE NEEDED study Q and A review list
- ## Sources and review notes | 250 | NO FIGURE NEEDED bibliography and verification notes

Specs kept 1, dropped 0: []
