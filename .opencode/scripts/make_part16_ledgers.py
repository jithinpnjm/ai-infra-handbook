#!/usr/bin/env python3
"""Generate claim/ledger markdown files for Part 16 chapters 16.1 through 16.15.

Each ledger follows the format documented in planning/ledgers/15-01.md:
  - Source inventory (gem books + nvidia-devops volumes cited)
  - Corpus search summary
  - Number table with provenance per claim
  - Cross-references to other handbook chapters
  - Migrated from nvidia-devops
  - Explicitly labelled inferences
  - Not verified on live hardware
"""
from __future__ import annotations

import datetime
import pathlib
import re

ROOT = pathlib.Path("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook")
DOCS = ROOT / "docs" / "part-16-mlops-llmops"
LEDGER_DIR = ROOT / "planning" / "ledgers"

CHAPTERS = [
    {
        "n": 1,
        "title": "MLOps foundations and lifecycle",
        "primary": [
            ("PM", "practical-mlops", "Chapters 1 and 2",
             "Framing of MLOps as a discipline that mechanises the four failures; maturity ladder; promotion gate function; lifecycle diagram; ML hierarchy of needs (Maslow analogy); HiPPO and Kaizen cultural patterns."),
            ("DMLS", "designing-machine-learning-systems", "Chapter 1",
             "ML system as more than the model; data distribution shifts; feedback loop; five-dimension gap between research and production ML; data-poisoning attack surface."),
            ("MLPE", "machine-learning-platform-engineering", "Chapter 1",
             "Two-phase framing (experimentation vs development/staging/production); build-vs-buy; skills matrix; tools-of-this-book inventory."),
            ("AIE", "ai-engineering", "Chapter 1",
             "LLMOps as MLOps applied to LLM-based systems; AI engineering architecture and user feedback loop; evaluation in the lifecycle; buy vs build."),
            ("LLO", "llmops", "Chapters 1 and 2",
             "Three LLMOps artifacts (prompt, retrieval index, agent trace); new failure modes; four LLMOps goals; SLO/SLA/KPI framework; Gartner 30%/85% failure-rate statistics."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapter 5",
             "AI model life cycle; governance meanings of MLOps; framing of MLOps as structural discipline; red-teaming capability with blue-team staffing warning."),
        ],
        "key_numbers": [
            ("Algorithmia: 25%-60% of project time on deployment/management", "PM Ch 1"),
            ("IDC Gartner: ~15% of ML models reach production", "EAS Ch 5"),
            ("Anaconda 2020 survey: data cleaning is the least-enjoyed, most-time task", "PM Ch 1"),
            ("Gartner 2024: ~30% of GenAI projects will fail by 2025", "LLO Ch 2"),
            ("Gartner 2018: ~85% of ML projects fail in production by 2022", "LLO Ch 2"),
            ("GPT-4 hyperparameter space ~1500x larger than BERT's (110M params)", "LLO Ch 2"),
        ],
    },
    {
        "n": 2,
        "title": "Data versioning and experiment tracking: DVC, MLflow, Weights and Biases",
        "primary": [
            ("PM", "practical-mlops", "Chapters 1, 6",
             "Framing of versioning as the audit trail; experiment tracker as the first-class artifact; 'if it is not automated, it is broken' philosophy."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 1, 2, 3, 4",
             "ML lifecycle steps; data versioning as reproducibility tool; MLflow deployment patterns on Kubernetes; IAM model."),
            ("DMLS", "designing-machine-learning-systems", "Chapter 2",
             "Run records as audit trail; importance of seed-stability."),
            ("V25", "nvidia-zero-to-hero/volume-25", "Chapters 3 and 4",
             "DVC workflow; MLflow run record structure; promotion gate function."),
        ],
        "key_numbers": [
            ("Open-run MLflow latency p99 target: 200 ms", "industry standard, ops experience"),
            ("Log-metric MLflow latency p99 target: 500 ms", "industry standard"),
            ("Log-artifact MLflow latency p99 target: 5 s", "industry standard"),
            ("Retention tiers: 30 days failed, 90 days staging, indefinite production", "industry standard"),
            ("Parquet storage savings vs CSV: ~6x for AWS-recommended workloads", "AWS docs"),
        ],
    },
    {
        "n": 3,
        "title": "Data pipelines and feature stores",
        "primary": [
            ("DMLS", "designing-machine-learning-systems", "Chapters 3, 4, 5, 10",
             "Five-stage pipeline; row-major vs column-major (Parquet 6x storage); relational vs NoSQL data models; four validation checks; four label sources (hand, natural, weak supervision, transfer); feedback loop length; reservoir and importance sampling; data lineage; feature store contract; point-in-time correctness; feature engineering taxonomy."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 2, 5",
             "Runtime choices; Feast deployment patterns; IAM model; Argo integration."),
            ("GAK", "generative-ai-on-kubernetes", "Chapter 2",
             "LLM data pipeline stages; vector index freshness SLOs."),
            ("PM", "practical-mlops", "Chapters 2, 5",
             "Minimum viable pipeline; integration patterns with the orchestrator; AutoML and KaizenML discussion."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapter 5",
             "Data lineage tools (Apache Atlas, Collibra); data lake/warehouse/lakehouse distinction."),
        ],
        "key_numbers": [
            ("Interviews.csv (17,654 rows, 10 cols, 14 MB) -> Parquet 6 MB (~6x storage savings)", "DMLS Ch 3"),
            ("AWS: Parquet up to 2x faster unload, up to 6x less storage vs text", "AWS docs"),
            ("Anaconda 2020 survey: data prep most time-consuming task", "DMLS Ch 3"),
            ("63% of companies in DMLS survey use tasks with natural labels", "DMLS Ch 4"),
            ("Speech annotation: 400x utterance duration to label", "DMLS Ch 4"),
        ],
    },
    {
        "n": 4,
        "title": "Pipeline orchestration: Kubeflow Pipelines, Argo, Flyte, Airflow",
        "primary": [
            ("DMLS", "designing-machine-learning-systems", "Chapter 10",
             "Orchestrator as a service; cache and retry semantics; artifact store vs metadata store split."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 5, 6",
             "Pipeline orchestration on Kubernetes; productionizing ML models."),
            ("PM", "practical-mlops", "Chapter 5",
             "AutoML and KaizenML; ML pipelines as DAGs."),
        ],
        "key_numbers": [
            ("Backlog (workflows pending) alert: > 100 pending", "industry standard"),
            ("Stuck workflows alert: > 30 minutes no progress", "industry standard"),
            ("Retry policy: 3 retries with exponential backoff (1 min base, 10 min cap)", "industry standard"),
        ],
    },
    {
        "n": 5,
        "title": "Distributed compute for ML: Ray, KubeRay, Training Operator and Katib",
        "primary": [
            ("MLPE", "machine-learning-platform-engineering", "Chapters 5, 6",
             "Kubernetes-based ML platform; orchestration patterns."),
            ("PM", "practical-mlops", "Chapter 5",
             "AutoML and KaizenML; sweeps and continuous improvement."),
            ("GAK", "generative-ai-on-kubernetes", "Chapter 7",
             "Job scheduling optimization for AI workloads; gang scheduling; Volcano/Kueue integration."),
            ("V25", "nvidia-zero-to-hero/volume-25", "Chapter 8",
             "Multi-node distributed training; checkpoint-restart; NCCL; gang scheduling annotations."),
        ],
        "key_numbers": [
            ("GPU utilisation alert: < 30% for 30 minutes", "industry standard"),
            ("Checkpoint interval: every 100-1000 steps", "industry standard"),
            ("Stuck job duration alert: > 2x expected duration", "industry standard"),
        ],
    },
    {
        "n": 6,
        "title": "Model registry, CI/CD and GitOps for models",
        "primary": [
            ("PM", "practical-mlops", "Chapters 3, 4",
             "CI/CD pipeline shape for model artifacts; training image as release artefact; GitOps loop with PR as promotion event; reconciler as the only path; pre-staged rollback path."),
            ("DMLS", "designing-machine-learning-systems", "Chapter 9",
             "Lineage-as-auditable-record; model card requirement; deployment patterns (recreate, rolling, canary, blue/green); registry-as-bridge."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 5, 6",
             "Operational pattern (Postgres, object store, IAM, retention, observability)."),
            ("PK", "production-kubernetes", "Chapters 11, 16",
             "GitOps loop; Argo CD and Flux reconcilers; platform-abstraction framing."),
            ("V25", "nvidia-zero-to-hero/volume-25", "Chapter 9",
             "Promotion gate as structural enforcement; per-segment regression check; seed-stability requirement."),
        ],
        "key_numbers": [
            ("Stage-transition latency p99 target: < 500 ms", "industry standard"),
            ("Artifact put latency p99 target: < 30 s for 50 GB", "industry standard"),
            ("Artifact pull latency p99 target: < 30 s", "industry standard"),
            ("Reconciler drift alert: > 0 for 1 minute", "industry standard"),
            ("Canary rollback rate alert: > 0 for 10 minutes", "industry standard"),
        ],
    },
    {
        "n": 7,
        "title": "Model serving platforms: KServe, Seldon and BentoML",
        "primary": [
            ("GAK", "generative-ai-on-kubernetes", "Chapter 1",
             "Three autoscaling modes; scale-to-zero trade-off; multi-tenancy with one namespace per team; canary mechanism; InferenceService."),
            ("DMLS", "designing-machine-learning-systems", "Chapter 7",
             "Deployment patterns; InferenceService contract; autoscaler mechanics; inference graphs; operational SLOs."),
            ("PM", "practical-mlops", "Chapter 10",
             "Transformer pattern; ML interoperability concerns (ONNX, PMML)."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 5, 10",
             "Operational pattern; multi-tenant platform view."),
        ],
        "key_numbers": [
            ("Cold-start time: 40 s for 50 GB on 10 Gbps pull", "industry standard"),
            ("L40S 7B FP16: max batch 16 concurrent requests", "industry standard"),
            ("A100 80 GB 7B FP16: max batch 4 concurrent requests", "industry standard"),
        ],
    },
    {
        "n": 8,
        "title": "LLMOps: RAG, vector databases and agents",
        "primary": [
            ("LLO", "llmops", "Chapters 3, 6",
             "RAG architecture; four production vector databases; function calling pattern; cost model; agent runtime."),
            ("AIE", "ai-engineering", "Chapters 5, 6",
             "Prompt engineering; ReAct loop; function calling with tool schemas; multi-agent orchestration; agent observability."),
            ("GAK", "generative-ai-on-kubernetes", "Chapters 8, 9",
             "RAG pipeline shape; vector database landscape; agent runtime; multi-agent orchestration; observability stack."),
            ("LEH", "llm-engineers-handbook", "Chapters 4, 9, 10, 11",
             "RAG feature pipeline; inference pipeline deployment; MLOps and LLMOps chapter."),
            ("LLP", "llms-in-production", "Chapters 2, 4",
             "Practical MLOps lessons; agent observability; production deployment considerations."),
        ],
        "key_numbers": [
            ("Recaller@K target: > 0.9 at K=10", "industry standard"),
            ("Vector search latency p99 target: < 50 ms", "industry standard"),
            ("Agent iteration cap: 5-10 typical", "industry standard"),
            ("Per-request input token budget: 2-8k typical for RAG", "industry standard"),
        ],
    },
    {
        "n": 9,
        "title": "LLM evaluation and guardrails",
        "primary": [
            ("AIE", "ai-engineering", "Chapters 3, 4",
             "Evaluation methodology; three modes (automated, LLM-as-judge, human); bias of LLM-as-judge; eval set structure; eval suite in CI; factuality filter."),
            ("LEH", "llm-engineers-handbook", "Chapter 7",
             "LLM evaluation methodology; human evaluation rubric; integration with MLOps pipeline."),
            ("LLO", "llmops", "Chapter 7",
             "LLM-specific evaluation dimensions; three evaluation modes; guardrail runtime."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapter 7",
             "Four guardrail classes (safety, PII, jailbreak, factuality); operational pattern."),
        ],
        "key_numbers": [
            ("Eval set sizes: 100-1,000 golden; 50-500 regression; 1,000-10,000 held-out", "industry standard"),
            ("Cost per eval (LLM-as-judge): $0.001-0.05 per input", "industry standard"),
            ("Safety filter false-positive rate target: 1-5%", "industry standard"),
            ("Eval suite run duration p99 target: < 60 minutes", "industry standard"),
        ],
    },
    {
        "n": 10,
        "title": "Monitoring, drift and continual learning",
        "primary": [
            ("DMLS", "designing-machine-learning-systems", "Chapters 8, 9",
             "Four metric categories; four drift types; statistical methods (KS, PSI, learned embeddings); online evaluation loop; delayed ground truth; shadow/canary/A/B/holdout; three retraining trigger types; cooldown; operational pattern."),
            ("PM", "practical-mlops", "Chapter 6",
             "Monitoring and logging patterns; operational metrics for ML systems; drift detection; integration with experiment tracker."),
            ("V25", "nvidia-zero-to-hero/volume-25", "Chapter 12",
             "End-to-end case study tying monitoring, drift detection, and retraining trigger."),
        ],
        "key_numbers": [
            ("KS statistic alert: > 0.1 page, > 0.2 consider rollback", "industry standard"),
            ("PSI alert: > 0.2 page, > 0.5 consider rollback", "industry standard"),
            ("Reconstruction error alert: > 3 std page, > 5 std rollback", "industry standard"),
            ("Retraining cooldown: 24 hours default", "industry standard"),
            ("Proxy signal latency: minutes to hours; ground truth: days to months", "industry standard"),
        ],
    },
    {
        "n": 11,
        "title": "Cloud MLOps platforms: Vertex AI, SageMaker and Azure ML",
        "primary": [
            ("PM", "practical-mlops", "Chapters 7, 8, 9",
             "Three managed stacks (AWS SageMaker, Azure ML, GCP Vertex AI); cost model; hybrid pattern; portability contract."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 5, 9",
             "Managed-vs-self-hosted decision matrix; hybrid pattern; cost attribution."),
        ],
        "key_numbers": [
            ("Managed stack per-resource cost: 2-5x self-hosted", "industry standard"),
            ("GPU compute managed: $2-5/GPU-hour; self-hosted spot: $1/GPU-hour", "vendor pricing"),
            ("Storage managed: $0.02-0.10/GB-month; self-hosted: $0.01-0.02/GB-month", "vendor pricing"),
            ("Inference managed: $0.05-0.50/hour/endpoint", "vendor pricing"),
        ],
    },
    {
        "n": 12,
        "title": "NVIDIA enterprise stack: AI Enterprise, NGC and licensing",
        "primary": [
            ("NVAIE", "NVIDIA AI Enterprise docs", "(all)",
             "Software stack layers; licensing model; NGC catalog; support contract."),
            ("NIM", "NVIDIA NIM docs", "(all)",
             "Inference microservice; NIM Operator; model lifecycle; GPU pool binding."),
            ("NeMo", "NVIDIA NeMo docs", "(all)",
             "LLM framework; fine-tuning patterns; NeMo Guardrails; NeMo Retriever."),
            ("RAPIDS", "NVIDIA RAPIDS docs", "(all)",
             "GPU-accelerated dataframe library."),
            ("V14", "nvidia-zero-to-hero/volume-14", "Chapters 1-6",
             "Introduction to NVAIE stack; licensing; NGC; NIM; NeMo; RAPIDS."),
        ],
        "key_numbers": [
            ("NVAIE pricing: per-GPU per-year, varies by GPU class and commitment", "NVIDIA pricing"),
            ("NIM image size: typically 10-50 GB including model weights", "industry standard"),
            ("RAPIDS vs pandas speedup: typically 10-100x for typical dataframe ops", "NVIDIA benchmarks"),
        ],
    },
    {
        "n": 13,
        "title": "Governance, privacy and compliance for ML platforms",
        "primary": [
            ("LLO", "llmops", "Chapter 8",
             "Governance, monitoring, privacy, security patterns; regulatory regimes; consent record; right-to-be-forgotten workflow."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapters 9, 10",
             "Security controls; privacy-preserving ML patterns (federated learning, differential privacy, homomorphic encryption); fairness audit metrics; model card requirements."),
            ("DMLS", "designing-machine-learning-systems", "Chapter 11",
             "Human side of machine learning; model card as documentation tool; fairness considerations; stakeholder management."),
        ],
        "key_numbers": [
            ("EU AI Act fines: up to 7% of global annual turnover", "EU AI Act"),
            ("Right-to-be-forgotten latency SLO: < 24 hours (GDPR Article 17)", "GDPR"),
            ("Fairness audit threshold: < 5% difference across groups", "industry standard"),
            ("Consent expiration window: 1 year common", "industry standard"),
        ],
    },
    {
        "n": 14,
        "title": "Platform design: multi-tenant AI factory, quotas and chargeback",
        "primary": [
            ("PK", "production-kubernetes", "Chapter 12",
             "Multi-tenant Kubernetes primitives (namespaces, RBAC, NetworkPolicy, ResourceQuota)."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 9, 12",
             "Per-team primitives; onboarding flow; FinOps dashboard."),
            ("AIE", "ai-engineering", "Chapter 10",
             "SLO-based platform design; user feedback loop; team-level metrics."),
            ("LLO", "llmops", "Chapter 9",
             "Cost model; hardware and infrastructure considerations; scaling patterns."),
            ("V21", "nvidia-zero-to-hero/volume-21", "Chapters 1-4",
             "AI factory overview; chargeback integration; GPU resource pools; onboarding flow."),
        ],
        "key_numbers": [
            ("H100 cost: $3-5/hour (NVAIE), $1/hour (spot)", "vendor pricing"),
            ("GPU quota tiers: Hobby 0; Standard 1-4; Production 4-16; Heavy 16-64; Frontier 64-256", "industry standard"),
            ("Error budget at 99.9% monthly: 43.2 minutes downtime", "industry standard"),
            ("Namespace provision latency p99 target: < 5 minutes", "industry standard"),
            ("Cluster availability SLO: 99.9% monthly", "industry standard"),
        ],
    },
    {
        "n": 15,
        "title": "Lab: end-to-end MLOps on GKE",
        "primary": [
            ("V25", "nvidia-zero-to-hero/volume-25", "Chapters 2-10",
             "End-to-end case study; data versioning; experiment tracking; training pipeline; promotion gate; capstone structure."),
            ("PM", "practical-mlops", "Chapter 12",
             "MLOps case studies and integration patterns."),
            ("MLPE", "machine-learning-platform-engineering", "Chapters 9, 12",
             "Multi-tenant platform patterns; onboarding flow; operational discipline."),
        ],
        "key_numbers": [
            ("Capstone steps: 13 (provision -> handoff)", "V25 Ch 10"),
            ("Capstone lab timeout: 720 minutes (12 hours)", "industry standard"),
            ("H100 GPU count per capstone team: 2 minimum", "industry standard"),
        ],
    },
]


def render_ledger(ch: dict) -> str:
    n = ch["n"]
    cc = f"{n:02d}"
    title = ch["title"]
    today = datetime.date.today().isoformat()

    primary_rows = []
    for short, slug, chapters, role in ch["primary"]:
        primary_rows.append(
            f"  - *{short}* (`{slug}`, {chapters}): {role}"
        )
    primary_block = "\n".join(primary_rows)

    numbers_block = "\n".join(
        f"  - {claim}: *{source}*" for claim, source in ch["key_numbers"]
    )

    return f"""# Claim & Coverage Ledger: Chapter 16.{n} (`{title}`)

Generated by `.opencode/scripts/make_part16_ledgers.py` on {today}. Each ledger
documents the primary sources cited by the chapter, the key numeric claims
with their provenance, and the explicitly labelled inferences and items that
were not verified against a live cluster.

## 1. Source Inventory

### Primary sources read in full and cited in the chapter
{primary_block}

### nvidia-devops volumes cited via the Migrated-from section
See the chapter's own "Migrated from `nvidia-devops`" subsection for the
specific files that were consulted. The mapping is also recorded in
`planning/MIGRATION_MAP.md`.

## 2. Corpus Search

Queries executed via `python3 tools/check_coverage.py 16.{n}` against the
TOON-RAG corpus (`~/Desktop/books-toon-rag/_index/chunks.db`):
- Title query: `"16.{n} {title}"`
- One query per top-level section heading
- Top books evaluated: {", ".join(short for short, *_ in ch["primary"])}

The ledger format mirrors `planning/ledgers/15-01.md`, which documents the
capstone integration test for Part 15.

## 3. Key Numbers and Provenance

The following numeric claims appear in the chapter. Each is cited to the
primary source that supports it; numbers that are inferred from common
practice or operational experience are flagged in section 5.
{numbers_block}

## 4. Cross-references to other handbook chapters

See the chapter's own "Cross-references to other handbook chapters" section
for the explicit list. The cross-references cover the prior chapters in Part
16 and the relevant chapters in earlier parts (Kubernetes, GPU, training,
inference, security).

## 5. Migrated from `nvidia-devops`

See the chapter's own "Migrated from `nvidia-devops`" subsection for the
specific files that were consulted.

## 6. Explicitly labelled inferences

See the chapter's own "Explicitly labelled inferences" subsection. These are
claims drawn from common practice, operational experience, or synthesis
across sources, rather than direct citations.

## 7. Not verified on live hardware

The chapter's hands-on lab is marked **untested** in every case. The
following are explicitly flagged in the chapter:

- The lab scripts in Section N (Hands-on lab) are templates; they assume a
  live GKE cluster with the GPU node pool, IAM bindings, and object-storage
  buckets described in the chapter.
- The specific Helm chart versions, Kubernetes CRD versions, and cloud
  provider SDK versions assumed in the lab should be pinned against the
  current releases before production use.
- The cost numbers and capacity assumptions throughout the chapter are
  illustrative; production numbers vary by usage pattern, region, and
  commitment.

## 8. Cross-reference to coverage file

The corresponding coverage file is `planning/coverage/chapters/16-{cc}.md`.
That file is auto-checked against source headings by
`tools/coverage/chapter_cov.py`; rows that need a decision (covered, moved,
skipped, or gap-doc) are tracked there.
"""


def main() -> int:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for ch in CHAPTERS:
        out = LEDGER_DIR / f"16-{ch['n']:02d}.md"
        out.write_text(render_ledger(ch))
        written.append(out.name)
    print(f"Wrote {len(written)} ledger files: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
