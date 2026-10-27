#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.9: A real playbook end to end: deploying an application."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_app_deployment import (
    AtomicReleaseDeployer,
    render_gunicorn_conf,
    validate_pinned_version,
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
    # 1. Section 5: Pinned version validation (tags and SHAs allowed; moving branches rejected)
    check(
        "validate_pinned_version accepts semantic tags (v1.4.2) and commit SHAs (a1b2c3d) and rejects moving branches ('main')",
        validate_pinned_version("v1.4.2") is True
        and validate_pinned_version("4121bfa9c0ffee") is True
        and validate_pinned_version("main") is False,
    )

    # 2. Section 5: AtomicReleaseDeployer symlink switch, N=3 pruning, and instant rollback
    deployer = AtomicReleaseDeployer(keep_releases=3)
    for ver in ("v1.0.0", "v1.0.1", "v1.0.2", "v1.0.3"):
        out = deployer.deploy(ver)
    rb = deployer.rollback("v1.0.2")
    check(
        "AtomicReleaseDeployer switches current symlink, prunes oldest v1.0.0 when keep_releases=3, and rolls back to v1.0.2",
        out["current"] == "releases/v1.0.3"
        and out["retained"] == ["v1.0.1", "v1.0.2", "v1.0.3"]
        and out["pruned"] == ["v1.0.0"]
        and rb == "releases/v1.0.2",
    )

    # 3. AUR Ch. 7 Example 7-21: gunicorn.conf.py.j2 worker sizing and Unix socket bind
    gconf = render_gunicorn_conf("/home/vagrant/mezzanine/mezzanine_example", "mezzanine_example", vcpus=4)
    check(
        "render_gunicorn_conf binds unix socket and sizes workers = vcpus * 2 (8)",
        'bind = "unix:/home/vagrant/mezzanine/mezzanine_example/gunicorn.sock"' in gconf
        and "workers = 8" in gconf,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
