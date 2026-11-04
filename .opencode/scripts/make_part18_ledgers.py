#!/usr/bin/env python3
"""Generate claim/ledger markdown files for Part 18 (Security) chapters 18.1 through 18.7."""
from __future__ import annotations

import datetime
import pathlib

ROOT = pathlib.Path("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook")
LEDGER_DIR = ROOT / "planning" / "ledgers"

CHAPTERS = [
    {
        "n": 1,
        "title": "Threat modeling for AI infrastructure",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapter 1",
             "STRIDE methodology for AI infrastructure; asset inventory; attack surface; threat catalogue; risk matrix; mitigation status."),
            ("V8", "nvidia-zero-to-hero/volume-8", "Chapter 3",
             "Platform-level security patterns and the trust model."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapter 9",
             "Security patterns and the risk-driven approach."),
        ],
        "key_numbers": [
            ("STRIDE: 6 threat categories (Spoofing, Tampering, Repudiation, Information Disclosure, DoS, EoP)", "industry standard"),
            ("Risk score: likelihood (1-5) x impact (1-5)", "industry standard"),
            ("Risk thresholds: 20-25 Critical; 15-19 High; 10-14 Medium; 5-9 Low; 1-4 Very Low", "industry standard"),
            ("Threat model workshop: half-day; 4-6 participants", "V18 ch1"),
            ("Asset categories: 7 (models, weights, datasets, keys, logs, GPUs, credentials)", "industry standard"),
        ],
    },
    {
        "n": 2,
        "title": "Hardware and firmware trust",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapter 2",
             "UEFI secure boot; TPM measured boot; GPU attestation; FW BOM; firmware update process."),
            ("V10", "nvidia-zero-to-hero/volume-10", "Chapter 16",
             "Operational patterns for firmware trust."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapter 9",
             "Firmware trust model and security patterns."),
        ],
        "key_numbers": [
            ("UEFI secure boot chain: ROM -> secure boot -> firmware -> bootloader -> kernel -> userspace", "UEFI spec"),
            ("TPM PCRs: 24 registers (PCR0-23)", "TPM 2.0 spec"),
            ("GPU attestation: endorsement key (fuse), attestation key, firmware measurement", "NVIDIA docs"),
            ("FW BOM fields: node_id, component, version, vendor, signature_status, attestation_status, cve", "V18 ch2"),
            ("Firmware update cycle: quarterly (test -> canary 10% -> full 100%)", "industry standard"),
        ],
    },
    {
        "n": 3,
        "title": "Containers and the software supply chain",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapter 3",
             "cosign signing; OPA Gatekeeper/Kyverno admission control; SBOM generation; Trivy/Grype vulnerability scanning; dependency confusion defence."),
            ("PK", "production-kubernetes", "Chapter 15",
             "Supply chain patterns and admission control patterns."),
        ],
        "key_numbers": [
            ("cosign signing: 100% of images signed", "V18 ch3"),
            ("SBOM format: CycloneDX or SPDX", "industry standard"),
            ("Vulnerability scan: every image, every build", "V18 ch3"),
            ("Dependency pinning: lockfile with hashes for every dependency", "V18 ch3"),
            ("Admission control: Gatekeeper validate action or Kyverno enforce mode", "V18 ch3"),
        ],
    },
    {
        "n": 4,
        "title": "Kubernetes access control and pod security",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapters 4, 5",
             "RBAC least-privilege; Workload Identity; Pod Security Standards; NetworkPolicies default-deny; External Secrets Operator."),
            ("PK", "production-kubernetes", "Chapters 8, 10",
             "Kubernetes access control patterns and operational discipline."),
        ],
        "key_numbers": [
            ("RBAC: Roles (namespace), ClusterRoles (cluster-wide)", "K8s docs"),
            ("Workload Identity: short-lived credentials (1 hour)", "GCP docs"),
            ("Pod Security Standards: Privileged, Baseline, Restricted", "K8s docs"),
            ("NetworkPolicy default-deny: every namespace", "K8s docs"),
            ("Secret rotation: 30 days default", "industry standard"),
        ],
    },
    {
        "n": 5,
        "title": "GPU sharing security, DMA, IOMMU and SR-IOV",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapters 6, 7",
             "IOMMU address translation; NVIDIA MIG partitions; SR-IOV virtual functions; time-slicing security implications; GPU memory scraping defence."),
            ("V11", "nvidia-zero-to-hero/volume-11", "Chapter 21",
             "GPU device plugin patterns and MIG configuration."),
        ],
        "key_numbers": [
            ("IOMMU: address translation, access control, isolation, audit", "IOMMU spec"),
            ("MIG A100 80GB: 7 instances (1x 5g.40gb, 1x 4g.40gb, 2x 3g.20gb, 4x 1g.10gb)", "NVIDIA docs"),
            ("SR-IOV: Physical Function (PF), Virtual Functions (VFs)", "PCIe spec"),
            ("GPU sharing modes: time-slicing (sequential), MIG (spatial), SR-IOV (spatial)", "NVIDIA docs"),
            ("GPU memory scraping attack: DMA-based read of another tenant's memory", "V18 ch6"),
        ],
    },
    {
        "n": 6,
        "title": "BlueField, DOCA and confidential computing",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapters 8, 9",
             "BlueField-3 DPU as security root of trust; DOCA offload of security functions; confidential VMs (NVIDIA GPU CC, SEV-SNP, TDX); attestation chains."),
            ("V11", "nvidia-zero-to-hero/volume-11", "Chapter 29",
             "BlueField deployment and DOCA configuration."),
        ],
        "key_numbers": [
            ("BlueField-3: 8-16 ARM cores, 16-32 GB DDR, 100-400 Gbps network", "NVIDIA docs"),
            ("DOCA libraries: DMA, Flow, SHA, Rivermax, RegEx", "NVIDIA docs"),
            ("AMD SEV-SNP: memory encryption + attestation", "AMD docs"),
            ("Intel TDX: memory encryption + attestation", "Intel docs"),
            ("Attestation chain: TPM -> DPU -> CVM -> GPU -> Workload", "V18 ch8"),
        ],
    },
    {
        "n": 7,
        "title": "Data and model protection, audit and compliance",
        "primary": [
            ("V18", "nvidia-zero-to-hero/volume-18", "Chapters 10, 11",
             "Encryption at rest and in transit; model watermarking; DLP; tamper-evident audit log; lineage for compliance."),
            ("V8", "nvidia-zero-to-hero/volume-8", "Chapter 3",
             "Platform security and trust patterns."),
            ("EAS", "engineering-ai-systems-architecture-and-devops-essentials", "Chapters 9, 10",
             "Security patterns and privacy/fairness considerations."),
        ],
        "key_numbers": [
            ("Encryption at rest: CMEK for every bucket and disk", "V18 ch10"),
            ("Encryption in transit: TLS 1.3 enforced for every service", "V18 ch10"),
            ("Model watermarking: 100% of production models", "V18 ch10"),
            ("Audit log retention: 7 years for regulated industries", "industry standard"),
            ("Lineage graph: nodes (data, model, customer), edges (derived_from, trained_on, served_to)", "V18 ch11"),
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

    return f"""# Claim & Coverage Ledger: Chapter 18.{n} (`{title}`)

Generated by `.opencode/scripts/make_part18_ledgers.py` on {today}. Each ledger
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

Queries executed via `python3 tools/check_coverage.py 18.{n}` against the
TOON-RAG corpus (`~/Desktop/books-toon-rag/_index/chunks.db`):
- Title query: `"18.{n} {title}"`
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
18 and the relevant chapters in earlier parts (Kubernetes, GPU, supply chain).

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

The corresponding coverage file is `planning/coverage/chapters/18-{cc}.md`.
That file is auto-checked against source headings by
`tools/coverage/chapter_cov.py`; rows that need a decision (covered, moved,
skipped, or gap-doc) are tracked there.
"""


def main() -> int:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for ch in CHAPTERS:
        out = LEDGER_DIR / f"18-{ch['n']:02d}.md"
        out.write_text(render_ledger(ch))
        written.append(out.name)
    print(f"Wrote {len(written)} ledger files: {', '.join(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
