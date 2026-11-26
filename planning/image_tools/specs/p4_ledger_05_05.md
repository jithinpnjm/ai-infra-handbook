# docs/part-05-kubernetes/05-the-api-server-and-etcd-how-a-request-becomes-cluster-state.md
- ## Why this matters for AI infrastructure | 170 | NO FIGURE NEEDED intro motivation and context
- ## Prerequisites and outcomes | 180 | NO FIGURE NEEDED checklist of prerequisites
- ## 1. The API surface | 45 | NO FIGURE NEEDED short introductory transition
- ### Groups, versions, kinds, resources | 270 | COVERED(p3-0505-url-anatomy)
- ### Versioning and conversion | 160 | COVERED(p2-0505-storage-version)
- ### Verbs and HTTP mapping | 160 | NO FIGURE NEEDED clean mapping table provided in text
- ## 2. The request pipeline | 890 | COVERED(p3-0505-webhook-deadlock, m5-05-1)
- ## 3. resourceVersion, generation and concurrency | 640 | COVERED(p3-0505-three-counters, p3-0505-list-watch-410, k05-conflict)
- ## 4. Writing objects: create, update, patch, apply | 330 | COVERED(p3-0505-apply-managers)
- ## 5. Audit, authn/z debugging and security notes | 280 | NO FIGURE NEEDED policy levels and commands clearly listed
- ## 6. API Priority and Fairness (APF) | 380 | COVERED(k05-apf)
- ## 7. etcd internals | 0 | NO FIGURE NEEDED section container heading
- ### Deployment models for etcd | 320 | NEEDS FIGURE stacked vs dedicated cluster topologies and placement rules
- ### Data model and Raft | 230 | COVERED(k05-raft-write)
- ### MVCC, revisions, compaction, defrag | 230 | COVERED(p3-0505-nospace-recovery, k05-compact-defrag)
- ### What lives in etcd | 160 | NEEDS FIGURE hierarchical registry keyspace layout and size limits
- ### Encrypting Secrets in etcd | 870 | COVERED(p3-0505-encryption-rotation, p2-0505-envelope-keys)
- ### Performance factors and tuning | 290 | NO FIGURE NEEDED metrics and performance levers clearly catalogued
- ### Backup, restore, and member operations | 290 | COVERED(p2-0505-etcd-restore)
- ## 8. API server operations and scaling | 310 | NEEDS FIGURE stateless API server HA pool, LB timeouts, and separate events store
- ## 9. Diagnosing control-plane saturation | 310 | COVERED(p3-0505-saturation-ladder)
- ## 10. Lab | 390 | NO FIGURE NEEDED hands-on terminal exercises
- ## 11. Common mistakes | 160 | NO FIGURE NEEDED bullet list of operational pitfalls
- ## 12. Interview angles | 120 | NO FIGURE NEEDED interview questions
- ## Exercises | 250 | NO FIGURE NEEDED assignment exercises
- ## Checkpoint questions (20) | 1400 | NO FIGURE NEEDED reference questions and answers
- ## Sources and review notes | 230 | NO FIGURE NEEDED reference notes

Specs kept 3, dropped 0: []
