# docs/part-02-networking/08-dns-in-depth-resolution-records-resolvers-and-caching.md
- ## Why this matters for AI infrastructure | 160 | NO FIGURE NEEDED introductory overview of DNS importance in clusters
- ## Prerequisites and outcomes | 170 | NO FIGURE NEEDED outcome checklist and prerequisites
- ## 1. The structure of DNS | 380 | COVERED(p3-0208-delegation-glue, m2-08-1) hierarchy, delegation, glue, zone transfer, and roles
- ## 2. How a lookup actually works | 480 | COVERED(p3-0208-transport-rcodes, p3-0208-ttl-cutover, n08-fig1-dns) resolution sequence, UDP/TCP, TTL, and cutover
- ## 3. Resource records | 520 | COVERED(p3-0208-reverse-name, p3-0208-zone-read, n08-records) record types table, zone file syntax, and reverse DNS
- ## 4. Tools: dig and friends | 340 | COVERED(p3-0208-dig-anatomy) dig output anatomy and direct DNS vs getaddrinfo path
- ## 5. How a Linux host resolves names | 460 | COVERED(p3-0208-split-dns, p3-0208-app-caching, p3-0208-resolver-timeout, m2-08-3) split DNS, app caching, resolver timeouts, and Linux host path
- ### Hostnames | 110 | NO FIGURE NEEDED plain definition of /etc/hostname and cloud metadata naming conventions
- ### Following one lookup, step by step | 160 | NO FIGURE NEEDED getaddrinfo lookup path already covered by m2-08-3 and p3-0208-dig-anatomy
- ### The hosts file and its limits | 140 | NO FIGURE NEEDED short code snippet and plain text explanation of /etc/hosts format
- ### Caching daemons and the resolv.conf file | 190 | NO FIGURE NEEDED resolv.conf options and local stubs already covered by p3-0208-split-dns and m2-08-3
- ## 6. DNS in Kubernetes and containers | 430 | COVERED(p3-0208-k8s-dns-debug, n08-ndots) pod resolv.conf, ndots expansion, CoreDNS debug ladder
- ## 7. DNS in HPC and AI clusters | 340 | COVERED(p3-0208-cluster-names) multi-NIC GPU naming, fabric vs management resolution, Slurm/MPI hostfiles
- ## 8. Security: DNSSEC, DoT/DoH, and abuse | 310 | COVERED(p3-0208-dnssec-chain) DNSSEC chain of trust, keys, RRSIG, and abuse threat table
- ## 9. Running your own DNS | 230 | NEEDS FIGURE local rack caching resolver topology showing local zone authority, upstream shielding, and metrics
- ## 10. Diagnosing DNS problems | 200 | COVERED(m2-08-4) diagnostic ladder flowchart across resolution layers
- ## 11. Case study: "random 5-second delays" in a GPU inference cluster | 240 | COVERED(n08-5sec) conntrack race for parallel A and AAAA queries causing 5s timeout
- ## 12. Hands-on lab: DNS from both sides | 360 | NO FIGURE NEEDED lab steps and validation scripts
- ## 13. Common mistakes | 230 | NO FIGURE NEEDED bulleted review of common configuration mistakes
- ## 14. Interview angles | 170 | NO FIGURE NEEDED interview questions and sample talking points
- ## Exercises | 240 | NO FIGURE NEEDED end of chapter exercises
- ## Checkpoint questions (20) | 1250 | NO FIGURE NEEDED review Q&A
- ## Sources and review notes | 200 | NO FIGURE NEEDED bibliographic sources

Specs kept 1, dropped 0: []
