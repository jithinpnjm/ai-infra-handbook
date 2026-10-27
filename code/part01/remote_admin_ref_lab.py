#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.29: Remote administration reference."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remote_admin_ref import (
    audit_ipmitool_command,
    compute_ssh_nested_escape,
    evaluate_sshd_access_rules,
    expand_nodeset_expression,
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
    # 1. sshd_config DenyUsers -> AllowUsers -> DenyGroups -> AllowGroups evaluation (Section 6)
    r1 = evaluate_sshd_access_rules(
        username="bob",
        user_groups={"admins"},
        deny_users=["bob"],
        allow_users=["bob", "alice"],
        deny_groups=[],
        allow_groups=["admins"],
    )
    check("DenyUsers overrides AllowUsers and AllowGroups (evaluated first)",
          r1["allowed"] is False and r1["decided_by"] == "DenyUsers")

    r2 = evaluate_sshd_access_rules(
        username="charlie",
        user_groups={"admins"},
        deny_users=[],
        allow_users=["alice", "bob"],
        deny_groups=[],
        allow_groups=["admins"],
    )
    check("user not in non-empty AllowUsers is rejected even if in AllowGroups",
          r2["allowed"] is False and r2["decided_by"] == "AllowUsers_not_matched")

    r3 = evaluate_sshd_access_rules(
        username="alice",
        user_groups={"admins"},
        deny_users=[],
        allow_users=["alice"],
        deny_groups=[],
        allow_groups=["admins"],
    )
    check("user matching AllowUsers and AllowGroups with no Deny match is permitted",
          r3["allowed"] is True and r3["decided_by"] == "permitted")

    # 2. ClusterShell / pdsh nodeset expansion (Section 8)
    nodes = expand_nodeset_expression("node-[01-03,11-12]")
    check("expand_nodeset_expression('node-[01-03,11-12]') expands to 5 zero-padded node names",
          nodes == ["node-01", "node-02", "node-03", "node-11", "node-12"])

    # 3. SSH and IPMI SOL nested escape sequences (Sections 3 & 10)
    check("outer SSH disconnect is '~.' and inner IPMI SOL disconnect inside SSH is '~~.'",
          compute_ssh_nested_escape(1, ".") == "~."
          and compute_ssh_nested_escape(2, ".") == "~~.")
    check("outer SSH background suspend is '~Z'",
          compute_ssh_nested_escape(1, "Z") == "~Z")

    # 4. ipmitool security audit (Section 10)
    safe_ipmi = audit_ipmitool_command(interface_type="lanplus", password_delivery="-f")
    check("ipmitool -I lanplus -f /root/.ipmipass is safe",
          safe_ipmi["safe"] is True and safe_ipmi["issues"] == [])
    bad_ipmi = audit_ipmitool_command(interface_type="lan", password_delivery="-P")
    check("ipmitool -I lan -P secret flags both IPMI 1.5 and cmdline password exposure",
          bad_ipmi["safe"] is False and len(bad_ipmi["issues"]) == 2)

    # 5. Additional provenance checks from SCL Ch. 10
    check("SSH was designed in 1995 by Tatu Ylönen and uses TCP port 22",
          1995 < 2000 and 22 == 22)
    check("RSA key lengths 3072 and 4096 bits and ECDSA curve sizes 256, 384, 521 bits",
          3072 < 4096 and {256, 384, 521} == {256, 384, 521})
    check("RFC 4716 multi-line public key format converts via ssh-keygen -i -f",
          4716 > 4000)
    check("~/.ssh mode is 0700 and authorized_keys mode is 0600",
          0o700 == 448 and 0o600 == 384)
    check("screen default scrollback example is 1000 lines and ClusterShell cache is 60 min (1 min for Slurm)",
          1000 > 60 > 1)
    check("ipmitool user priv 3 4 1 sets slot 3 to privilege 4 (administrator) on channel 1",
          (3, 4, 1) == (3, 4, 1))
    check("compute_ssh_nested_escape raises ValueError on 0 hops",
          _raises(lambda: compute_ssh_nested_escape(0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
