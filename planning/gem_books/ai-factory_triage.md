# Phase 1 Triage: AI Factory (Karim, Galar, Kumar)

- **Corpus folder name:** `ai-factory`
- **Source code:** `AF`
- **Front/back matter skipped:** `Half Title`, `Series Page`, `Title Page`, `Copyright Page`, `Table of Contents`, `About the Authors`, `Foreword`, `Preface`, `Acknowledgements`, `Prologue`, `Index`

| Book chapter | Relevant to me? (YES / PARTLY / SKIP) | One-line reason | Where it belongs (handbook chapter number, or "deferred to Part N: <topic>") | Already covered? (FULL / PARTIAL / NONE, with the handbook chapter and section that covers it) |
|---|---|---|---|---|
| Chapter 1 Introduction | SKIP | Industrial AI and eMaintenance overview, AI winter/spring history, and sector survey (healthcare, retail, banking); out of scope for GPU platform engineering (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 2 Digital Twins | SKIP | Industrial digital twins, SysML, MES integration, and railway switch point-machine predictive maintenance; industrial asset-management scope (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 3 Hypes and Trends in Industry | SKIP | ISO 55000 physical asset management, Industry 4.0 nine pillars, drones, and predictive maintenance transformation; dated industrial scope (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 4 Data Analytics | SKIP | Maintenance descriptive/diagnostic/predictive/prescriptive analytics; Section 4.20 briefly surveys distributed filesystems at an encyclopedia level already exceeded by 6.18–6.20 and Part 13 (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 5 Data-Driven Decision-Making | SKIP | eMaintenance data maturity, data quality in industrial maintenance phases, and general ML data augmentation overview; industrial scope (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 6 Fundamental in Artificial Intelligence | SKIP | Managerial decision-making models, knowledge discovery, business intelligence vs AI, and classical symbolic inference engines; covered better for ML systems by DMLS, AIE, and EAS (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 7 Systems Thinking and Systems Engineering | SKIP | General systems theory (Checkland's taxonomy, system-of-systems, system lifecycle stages); high-level background only (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 8 Software Engineering | PARTLY | General software engineering lifecycle, Lehman's evolution laws, architecture patterns (layered, event-driven, microkernel, microservices, space-based), CBSE, software maintenance (corrective/adaptive/perfective/preventive), and AI in SDLC; mapped to `17.10` for lifecycle and maintenance framing. | deferred to Part 17: Cluster lifecycle, upgrades and change management (17.10) | deferred to Part 17 (17.10 is `status: scaffold`) |
| Chapter 9 Distributed Computing | PARTLY | Cloud computing service models (`IaaS`, `SaaS`), deployment models (`Public / private / hybrid cloud`, `multitenancy`), and storage taxonomy (`File store`, `Block store`, `Object store`, `Hybrid` clusters) give framing for distributed cluster types. | 6.1, 1.27 | FULL (6.1 `## 5. Kinds of clusters` and 1.27 `## 1. The cloud model` ("Instance types", "Cloud storage", "Multitenancy") — includes `IaaS` vs `FaaS / SaaS`, `Public / private / hybrid cloud` & `multitenancy`, `File store` / `Block store` / `Object store` table, and `HPC`/`HTC`/`HA`/`Cloud`/`Hybrid` cluster types; verified in `planning/coverage/chapters/06-01.md`) |
| Chapter 10 Case Studies | SKIP | Industrial case studies (AI Factory for Railway track/wheel detectors, Mining AIF/M, railway AR/VR point clouds, railway stakeholder cybersecurity); out of scope (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |
| Chapter 11 AI Factory: A Roadmap for AI Transformation | PARTLY | Defines the "AI Factory" virtuous cycle and data pipeline infrastructure (11.1), 3 competency levels (11.2), and batch/speed Lambda ML architecture on cloud/edge (11.3.2.2), while the rest is industrial manufacturing/transport policymaking and TBL sustainability. | deferred to Part 0: The AI factory landscape and the roles in it (0.1; also partially covered in 6.1 §4) | deferred to Part 0 (`0.1` is an unwritten Tier 2 scaffold; `6.1` §4 covers the datacentre AI factory vs HPC contrast) |
| Chapter 12 In Industrial AI We Believe | SKIP | Closing summary of Industrial AI (IAI) for process plants, autonomy taxonomy, and IMS architecture; summary and industrial scope only (`planning/coverage/skips.txt`). | — | — (skipped in `planning/coverage/skips.txt`) |

## Totals

- **Total numbered chapters triaged:** 12 (Chapters 1–12)
- **Relevance:**
  - **YES:** 0
  - **PARTLY:** 3 (Chapters 8, 9, 11)
  - **SKIP:** 9 (Chapters 1, 2, 3, 4, 5, 6, 7, 10, 12 — all 9 listed in `planning/coverage/skips.txt`)
- **Coverage status of the 3 YES and PARTLY chapters:**
  - **FULL (in Parts 1–11):** 1 (Chapter 9 in `6.1` and `1.27`)
  - **PARTIAL (in Parts 1–11):** 0
  - **NONE (in Parts 1–11):** 0
  - **Deferred:** 2 (Chapter 8 → deferred to Part 17: `17.10`; Chapter 11 → deferred to Part 0: `0.1`, which is written last per `planning/HANDOVER_TO_GEMINI.md`)
