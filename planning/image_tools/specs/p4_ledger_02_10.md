# docs/part-02-networking/10-http-tls-and-pki-basics.md
- ## Why this matters for AI infrastructure | 160 | NO FIGURE NEEDED intro motivation and context
- ## Prerequisites and outcomes | 150 | NO FIGURE NEEDED prerequisite links and outcome bullet list
- ## 1. HTTP in practice | 250 | COVERED(p3-0210-status-where, n10-httpmsg)
- ### Connections and versions | 450 | COVERED(p3-0210-stream-buffer, p3-0210-idle-mismatch, n10-httpver)
- ### `curl` as a diagnostic tool | 210 | NEEDS FIGURE breakdown of curl -w timing stages and delta calculations
- ### Reading a protocol trace | 270 | COVERED(p3-0210-trace-ascii)
- ## 2. Security goals and cryptographic building blocks | 460 | COVERED(p3-0210-mitm-defence, p3-0210-forward-secrecy, n10-crypto)
- ## 3. TLS | 80 | NO FIGURE NEEDED brief introductory section before handshake
- ### The handshake (TLS 1.3) | 450 | COVERED(p3-0210-tls-extras, n10-rtt, m2-10-1)
- ### Inspecting TLS with openssl | 120 | NO FIGURE NEEDED concise command snippet reference
- ## 4. Certificates and public-key infrastructure | 260 | COVERED(p3-0210-trust-stores, p3-0210-cert-fields, m2-10-2)
- ### Certificate authorities | 230 | COVERED(n10-fig1-certchain.jpg)
- ### Revocation and lifetimes | 100 | COVERED(p3-0210-revocation-expiry)
- ### Generating certificates (labs and private CAs) | 180 | COVERED(p3-0210-private-ca)
- ## 5. TLS and PKI in Kubernetes and AI platforms | 420 | COVERED(p3-0210-certmanager-modes)
- ## 6. Troubleshooting TLS and HTTP | 300 | COVERED(p3-0210-tls-ladder)
- ## 7. Hands-on lab: build a CA, serve HTTPS with mTLS, and break it on purpose | 320 | NO FIGURE NEEDED procedural lab steps
- ## 8. Common mistakes | 160 | NO FIGURE NEEDED summary checklist of common errors
- ## 9. Interview angles | 140 | NO FIGURE NEEDED list of practice questions
- ## Exercises | 250 | NO FIGURE NEEDED practice problems
- ## Checkpoint questions (20) | 1500 | NO FIGURE NEEDED self-test questions and answers
- ## Sources and review notes | 200 | NO FIGURE NEEDED bibliography and notes

Specs kept 1, dropped 0: []
