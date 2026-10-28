#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.27: Software supply chain security."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supply_chain_policy_verifier import (
    audit_ml_model_and_pip_supply_chain,
    evaluate_quarantine_image_promotion,
    verify_image_signature_and_mutate_digest,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 5: Keyless Cosign OIDC verification + SLSA provenance + mutateDigest
    ok_sig, mutated_img, _ = verify_image_signature_and_mutate_digest(
        image_ref="registry.example.com/ml/trainer:v1.2.0",
        resolved_digest="sha256:" + "a" * 64,
        signature_issuer="https://token.actions.githubusercontent.com",
        signature_subject="https://github.com/acme/llm-trainer/.github/workflows/release.yml@refs/tags/v1.2.0",
        slsa_build_type="https://actions.github.io/buildtypes/workflow/v1",
    )
    bad_sig, _, sig_errs = verify_image_signature_and_mutate_digest(
        image_ref="registry.example.com/ml/trainer:v1.2.0",
        resolved_digest="sha256:" + "a" * 64,
        signature_issuer="https://accounts.google.com",  # wrong issuer!
        signature_subject="https://github.com/evil-fork/llm-trainer/.github/workflows/pr.yml@refs/heads/main",  # wrong subject!
        slsa_build_type="manual-laptop-build",  # wrong buildType!
    )
    check(
        "verify_image_signature_and_mutate_digest pins verified tag to @sha256:... and rejects wrong issuer, subject, and buildType",
        ok_sig is True
        and mutated_img.endswith("@sha256:" + "a" * 64)
        and bad_sig is False
        and len(sig_errs) == 3,
    )

    # 2. Section 3, 4, 5 & PK Ch. 15: Quarantine-to-Approved image promotion & VEX suppression
    cves = [
        {"id": "CVE-2026-1001", "severity": "CRITICAL", "fixed_version": "1.2.4"},
        {"id": "CVE-2026-2002", "severity": "HIGH", "fixed_version": "3.0.1"},
    ]
    # Without VEX -> blocked by both CVEs + root user
    promo_fail, promo_errs = evaluate_quarantine_image_promotion(
        runs_as_non_root=False,
        cves=cves,
        vex_not_affected_cves=set(),
    )
    # With VEX not_affected justification and nonroot -> promoted!
    promo_ok, _ = evaluate_quarantine_image_promotion(
        runs_as_non_root=True,
        cves=cves,
        vex_not_affected_cves={"CVE-2026-1001", "CVE-2026-2002"},
    )
    check(
        "evaluate_quarantine_image_promotion blocks root image with unmitigated CVEs and promotes nonroot image when VEX marks CVEs not_affected",
        promo_fail is False and len(promo_errs) == 3 and promo_ok is True,
    )

    # 3. Section 6, 7, 8: Python dependency confusion & ML model serialization safety
    ok_ml, _ = audit_ml_model_and_pip_supply_chain(
        {
            "uses_extra_index_url": False,
            "pip_require_hashes": True,
            "model_format": "safetensors",
            "trust_remote_code": False,
        }
    )
    bad_ml, ml_errs = audit_ml_model_and_pip_supply_chain(
        {
            "uses_extra_index_url": True,
            "pip_require_hashes": False,
            "model_format": "pickle",
            "torch_weights_only": False,
            "trust_remote_code": True,
        }
    )
    check(
        "audit_ml_model_and_pip_supply_chain approves safetensors + --require-hashes and flags --extra-index-url, missing hashes, unsafe pickle, and trust_remote_code",
        ok_ml is True and bad_ml is False and len(ml_errs) == 4,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
