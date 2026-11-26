# docs/part-02-networking/20-load-balancing-l4-l7-ecmp-hashing-and-proxies.md
- ## Why this matters for AI infrastructure | 230 | NO FIGURE NEEDED introductory framing and motivational context for inference load balancing
- ## Prerequisites and outcomes | 100 | NO FIGURE NEEDED list of prerequisite chapter links and learning outcomes
- ## 1. What a load balancer does | 210 | COVERED(p3-0220-five-questions, n20-fig1-lb.jpg)
- ### Layers and families | 240 | COVERED(n20-families)
- ### Packet paths | 380 | COVERED(m2-20-1)
- ## 2. Algorithms | 520 | COVERED(p3-0220-hash-remap, p3-0220-p2c-herd, p3-0220-algo-pick)
- ## 3. Health checks, failure handling and draining | 650 | COVERED(p3-0220-drain-sequence, p3-0220-retry-storm, p3-0220-health-params)
- ## 4. ECMP, anycast and scaling out the L4 tier | 480 | COVERED(p3-0220-inference-path, n20-anycast)
- ## 5. L4 tools: IPVS and friends | 330 | COVERED(p3-0220-ipvs-dr-walk)
- ## 6. L7 tools: HAProxy, nginx, Envoy | 110 | NO FIGURE NEEDED introductory lead-in to individual L7 proxy tool subsections
- ### HAProxy (HTTP and TCP) | 370 | COVERED(p3-0220-grpc-through-haproxy, p3-0220-stream-timers)
- ### nginx | 150 | NEEDS FIGURE token streaming latency under proxy buffering on versus off
- ### Envoy | 370 | COVERED(p3-0220-reload-vs-xds)
- ## 7. TLS, client identity and L4/L7 interplay | 460 | COVERED(p3-0220-pinning-fixes, p3-0220-proxy-protocol, n20-tlsplace)
- ## 8. Cloud and Kubernetes load balancing (overview) | 450 | COVERED(p3-0220-cloud-lbs, p3-0220-kubeproxy-prob)
- ## 9. Load balancing for AI inference | 850 | NEEDS FIGURE prefix-cache-aware routing with bounded-load spillover
- ## 10. Troubleshooting | 280 | COVERED(p3-0220-502-walk)
- ## 11. Hands-on lab: build and break load balancers | 360 | NO FIGURE NEEDED step-by-step hands-on terminal exercise instructions
- ## 12. Common mistakes | 130 | NO FIGURE NEEDED bulleted review of common implementation pitfalls
- ## 13. Interview angles | 110 | NO FIGURE NEEDED list of candidate interview practice questions
- ## Exercises | 380 | NO FIGURE NEEDED student practice exercises and scenarios
- ## Checkpoint questions (20) | 1800 | NO FIGURE NEEDED self-assessment questions and detailed answer accordions
- ## Sources and review notes | 260 | NO FIGURE NEEDED bibliographic sources and lab verification notes

Specs kept 2, dropped 0: []
