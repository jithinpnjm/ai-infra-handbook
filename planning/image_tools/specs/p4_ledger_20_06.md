# docs/part-20-nebius-sre-interview/06-network-debugging-from-socket-to-switch.md
- ## What the interviewer is testing | 178 words | NO FIGURE NEEDED interview meta-context and expectations
- ## The core ideas | 10 words | NO FIGURE NEEDED structural container heading
- ### 1. Refused, timed out, reset: three different stories | 467 words | COVERED(x06-refused-timeout-reset)
- ### 2. The method: split the path in half | 358 words | COVERED(p2-2006-half-split, m20-06-1)
- ### 3. Reading ss: states and the two numbers | 598 words | COVERED(p3-2006-ss-states-fault)
- ### 4. SYN backlog and accept queue | 525 words | COVERED(x06-two-queues)
- ### 5. TIME_WAIT and ephemeral ports | 506 words | COVERED(p2-2006-port-budget)
- ### 6. Conntrack: the table that fills quietly | 557 words | COVERED(p3-2006-conntrack-guest-list)
- ### 7. DNS failures and ndots in Kubernetes | 512 words | COVERED(x06-ndots-candidate-ladder)
- ### 8. MTU and path MTU black holes | 569 words | COVERED(p2-2006-mtu-tunnel)
- ### 9. Retransmits and reading tcpdump | 545 words | COVERED(p3-2006-tcpdump-reading)
- ### 10. TLS handshake failures | 344 words | COVERED(p2-2006-tls-layers)
- ### 11. Idle timeouts and keepalive, the streaming problem | 632 words | COVERED(x06-idle-timeout-timeline)
- ### 12. The Kubernetes Service path | 400 words | COVERED(x06-service-path-ladder)
- ## How to answer out loud | 370 words | NO FIGURE NEEDED verbal interview rehearsal responses
- ## Worked scenarios | 75 words | NO FIGURE NEEDED introductory text for scenario walkthroughs
- ### Scenario 1: the full accept queue | 529 words | COVERED(p3-2006-accept-queue-numbers)
- ### Scenario 2: ports run out | 195 words | NO FIGURE NEEDED worked exercise applying port budget from section 5
- ### Scenario 3: conntrack is full | 148 words | NO FIGURE NEEDED worked exercise applying conntrack logic from section 6
- ### Scenario 4: the slow external call in a pod | 148 words | NO FIGURE NEEDED worked exercise applying ndots ladder from section 7
- ### Scenario 5: large responses hang over an overlay | 180 words | NO FIGURE NEEDED worked exercise applying MTU math from section 8
- ### Scenario 6: the stream that dies at one minute | 269 words | NO FIGURE NEEDED worked exercise applying idle timeout timeline from section 11
- ## Hands-on lab | 380 words | NO FIGURE NEEDED step-by-step console commands for lab reproduction
- ## Drill questions | 360 words | NO FIGURE NEEDED review drill questions and answers
- ## Common mistakes and weak answers | 210 words | NO FIGURE NEEDED bulleted list of interview pitfalls
- ## Connections to the rest of the handbook | 110 words | NO FIGURE NEEDED bulleted list of chapter cross references
- ## Sources and review notes | 480 words | NO FIGURE NEEDED reference citations and lab environment notes

Specs kept 0, dropped 0: []
