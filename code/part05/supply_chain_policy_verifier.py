"""Chapter 5.27 model: Cosign keyless OIDC signature + SLSA provenance verifier
with `mutateDigest`, `PK` Ch. 15 quarantine-to-approved image promotion & VEX
CVE evaluator, and AI model (`safetensors` vs pickle) + Python `--require-hashes`
dependency-confusion auditor.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 15 ("Software Supply Chain"):
  * Multi-stage Dockerfile (`golang:1.12.7` -> `gcr.io/distroless/base` running
    as `USER nonroot:nonroot`), Cloud Native Buildpacks (`/cnb/lifecycle/builder`),
    and the Golden Base Images Antipattern.
  * Tekton `Task` (`git-clone`, `buildpacks-phases`) and `Pipeline`
    (`clone-and-buildpack`).
  * Container registries (`Harbor`, `Quay`), CVE scanning (`Clair`, `Trivy`),
    Notary v1 Globally Unique Name (`GUN`) registry-URL limitation vs digest
    signing, and the Quarantine-to-Approved image promotion pipeline.
  * Push-based vs Pull-based (GitOps `Flux`/`Argo CD`) and progressive delivery
    (`Flagger` canary / blue-green).
"""
import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def verify_image_signature_and_mutate_digest(
    *,
    image_ref: str,
    resolved_digest: str,
    signature_issuer: str,
    signature_subject: str,
    slsa_build_type: str,
    expected_issuer: str = "https://token.actions.githubusercontent.com",
    expected_subject_regex: str = r"^https://github\.com/acme/.+/\.github/workflows/release\.yml@refs/tags/v.*$",
    expected_build_type: str = "https://actions.github.io/buildtypes/workflow/v1",
) -> Tuple[bool, str, List[str]]:
    """Model Section 5 Kyverno `verifyImages` with `mutateDigest: true`, keyless
    Fulcio OIDC issuer/subject regex verification, and SLSA provenance check.
    """
    errors: List[str] = []
    if signature_issuer != expected_issuer:
        errors.append(f"OIDC issuer mismatch: got {signature_issuer!r}, expected {expected_issuer!r}")
    if not re.match(expected_subject_regex, signature_subject):
        errors.append(f"Fulcio certificate subject {signature_subject!r} does not match {expected_subject_regex!r}")
    if slsa_build_type != expected_build_type:
        errors.append(f"SLSA provenance buildType {slsa_build_type!r} != {expected_build_type!r}")

    if len(errors) > 0:
        return False, image_ref, errors

    base_repo = image_ref.split("@")[0]
    mutated = f"{base_repo}@{resolved_digest}"
    return True, mutated, []


def evaluate_quarantine_image_promotion(
    *,
    runs_as_non_root: bool,
    cves: Sequence[Mapping[str, str]],
    vex_not_affected_cves: Set[str],
) -> Tuple[bool, List[str]]:
    """Model Section 3, 4, & 5 (`PK` Ch. 15) quarantine-to-approved registry
    promotion gate with VEX (`not_affected`) suppression.
    """
    reasons: List[str] = []
    if not runs_as_non_root:
        reasons.append("image USER is root (0); must run as nonroot:nonroot")

    for cve in cves:
        cve_id = str(cve["id"])
        sev = str(cve.get("severity", "LOW")).upper()
        has_fix = bool(cve.get("fixed_version"))
        if sev in {"CRITICAL", "HIGH"} and has_fix and cve_id not in vex_not_affected_cves:
            reasons.append(f"unmitigated {sev} vulnerability {cve_id} (fix available: {cve['fixed_version']})")

    return (len(reasons) == 0), reasons


def audit_ml_model_and_pip_supply_chain(cfg: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Model Section 6, 7, & 8 Python dependency confusion and ML model loading
    supply-chain checks.
    """
    errors: List[str] = []
    if cfg.get("uses_extra_index_url", False):
        errors.append("--extra-index-url is vulnerable to dependency confusion; use a single private --index-url")
    if not cfg.get("pip_require_hashes", False):
        errors.append("pip install must use --require-hashes with a hash-pinned lockfile")
    if cfg.get("model_format") == "pickle" and not cfg.get("torch_weights_only", False):
        errors.append("unsafe pickle model format without weights_only=True executes arbitrary code on load; use safetensors")
    if cfg.get("trust_remote_code", False):
        errors.append("trust_remote_code=True executes unreviewed Python from model repository")
    return (len(errors) == 0), errors
