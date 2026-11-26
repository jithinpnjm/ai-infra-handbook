# docs/part-02-networking/01-what-happens-when-you-curl-a-url-a-packet-s-journey-end-to-end.md
- ## Why this matters for AI infrastructure | 380 | NO FIGURE NEEDED introductory motivation framing the request journey
- ## Prerequisites and outcomes | 160 | NO FIGURE NEEDED bulleted prerequisites and self-check outcomes list
- ## 1. The whole journey in one picture | 130 | COVERED(m2-01-1)
- ## 2. Step 0: the process and the URL | 250 | COVERED(p3-0201-strace-diary)
- ## 3. Step 1: name resolution (what is the IP address?) | 580 | COVERED(p3-0201-ndots-search, n01-dnschain)
- ## 4. Step 2: the socket, the route and the source address | 460 | COVERED(p2-0201-route-pick)
- ## 5. Step 3: from IP to Ethernet (ARP or NDP) and out of the NIC | 470 | COVERED(p3-0201-arp-neighbour, p3-0201-encapsulation-frame)
- ## 6. Step 4: the switch, the router, NAT and the Internet | 560 | COVERED(p3-0201-pmtud-stall, p3-0201-router-four-steps, p3-0201-hop-rewrite)
- ## 7. Step 5: TCP connection establishment | 390 | COVERED(p2-0201-tcp-handshake)
- ## 8. Step 6: TLS handshake (HTTPS) | 360 | COVERED(p3-0201-tls-handshake)
- ## 9. Step 7: the HTTP request and response | 360 | COVERED(p3-0201-http-versions)
- ## 10. Step 8: transfer, acknowledgements and teardown | 210 | COVERED(p3-0201-loss-teardown)
- ## 11. Timing: reading `curl -w` | 240 | COVERED(n01-curlw)
- ## 12. A map from symptom to layer | 320 | COVERED(p3-0201-bisect-strategies, n01-symptommap)
- ## 13. The same journey in AI infrastructure | 370 | COVERED(p3-0201-ai-journey)
- ## 14. Hands-on lab: trace one request end to end | 420 | COVERED(p3-0201-lab-faults)
- ## 15. Common mistakes | 210 | NO FIGURE NEEDED bulleted summary of common debugging traps
- ## 16. Interview angles | 160 | NO FIGURE NEEDED interview prompt questions
- ## Exercises | 270 | NO FIGURE NEEDED practice problem specifications
- ## Checkpoint questions (20) | 1050 | NO FIGURE NEEDED self-test Q&A reference items
- ## Sources and review notes | 260 | NO FIGURE NEEDED bibliographical sources and review metadata

Specs kept 0, dropped 0: []
