# docs/part-05-kubernetes/06-controllers-and-the-reconcile-loop-how-kubernetes-thinks.md
- ## Why this matters for AI infrastructure | 157 words | NO FIGURE NEEDED introductory motivation and overview
- ## Prerequisites and outcomes | 112 words | NO FIGURE NEEDED bulleted outcome checklist
- ## 1. The controller pattern | 565 words | COVERED(p2-0506-desired-observed, m5-06-1)
- ## 2. The machinery: informers and work queues | 463 words | COVERED(p3-0506-workqueue-sets, p2-0506-informer-pipeline)
- ## 3. Built-in controllers (a tour) | 54 words | NO FIGURE NEEDED introductory tour text
- ### Deployment → ReplicaSet → Pod | 395 words | COVERED(p3-0506-scale-down-order, k06-deploy-chain)
- ### StatefulSet | 172 words | COVERED(p3-0506-statefulset-identity)
- ### DaemonSet | 129 words | NO FIGURE NEEDED straightforward per-node agent placement and nodeSelector matching
- ### Job and CronJob | 230 words | COVERED(p3-0506-kueue-suspend, p3-0506-job-patterns)
- ### Node lifecycle and eviction | 315 words | COVERED(p3-0506-statefulset-split-brain, p2-0506-node-timeline)
- ### EndpointSlice and Service controllers | 115 words | NEEDS FIGURE mechanism showing how readiness probes decouple traffic routing from pod lifecycle via EndpointSlice conditions
- ### Namespace, garbage collector, TTL, PV/PVC, HPA and others | 168 words | NO FIGURE NEEDED summary list of auxiliary controllers
- ## 4. Owners, selectors, finalizers, conditions | 0 words | NO FIGURE NEEDED section container
- ### Reconciliation loops and the loose link to Pods | 189 words | NO FIGURE NEEDED conceptual framing of loose coupling
- ### ownerReferences and adoption | 460 words | COVERED(k06-quarantine)
- ### Finalizers | 114 words | COVERED(p3-0506-namespace-terminating)
- ### Status and conditions | 144 words | NEEDS FIGURE anatomy of status.conditions and observedGeneration with the /status subresource contract
- ## 5. Leader election and HA | 252 words | COVERED(k06-lease)
- ## 6. Failure modes and diagnostics | 250 words | COVERED(p3-0506-hot-loop)
- ## 7. Designing safe automation with the controller mindset | 490 words | COVERED(p3-0506-gpu-remediation-flow)
- ## 8. Lab | 420 words | NO FIGURE NEEDED hands-on terminal steps
- ## 9. Common mistakes | 130 words | NO FIGURE NEEDED bulleted list of anti-patterns
- ## 10. Interview angles | 118 words | NO FIGURE NEEDED sample interview questions
- ## Exercises | 320 words | NO FIGURE NEEDED self-study exercises
- ## Checkpoint questions (20) | 1300 words | NO FIGURE NEEDED diagnostic Q&A reference
- ## Sources and review notes | 220 words | NO FIGURE NEEDED source citations

Specs kept 2, dropped 0: []
