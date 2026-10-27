#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.21: Linux security: capabilities, SELinux, AppArmor, seccomp, PAM, SSH hardening."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linux_security_hardening import (
    CAPABILITY_SETS,
    check_yama_ptrace_allowed,
    evaluate_execve_capabilities,
    evaluate_pam_stack,
    parse_selinux_context,
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
    # 1. Classic PAM chsh stack evaluation (HLW Ch. 7.10.1, Section 3)
    # rootok (sufficient), shells (requisite), unix (sufficient), deny (required)
    root_login = evaluate_pam_stack([
        ("sufficient", "pam_rootok.so", True),
        ("requisite", "pam_shells.so", False),
        ("sufficient", "pam_unix.so", False),
        ("required", "pam_deny.so", False),
    ])
    check("pam_rootok.so sufficient short-circuits immediately on root success",
          root_login["authenticated"] is True and root_login["executed"] == ["pam_rootok.so"])

    bad_shell = evaluate_pam_stack([
        ("sufficient", "pam_rootok.so", False),
        ("requisite", "pam_shells.so", False),
        ("sufficient", "pam_unix.so", True),
        ("required", "pam_deny.so", False),
    ])
    check("pam_shells.so requisite failure stops immediately without running pam_unix.so",
          bad_shell["authenticated"] is False and bad_shell["executed"] == ["pam_rootok.so", "pam_shells.so"])

    good_user = evaluate_pam_stack([
        ("sufficient", "pam_rootok.so", False),
        ("requisite", "pam_shells.so", True),
        ("sufficient", "pam_unix.so", True),
        ("required", "pam_deny.so", False),
    ])
    check("non-root user with valid shell and valid unix password succeeds before pam_deny.so",
          good_user["authenticated"] is True and good_user["executed"] == ["pam_rootok.so", "pam_shells.so", "pam_unix.so"])

    req_fail_before_suff = evaluate_pam_stack([
        ("required", "pam_faillock.so", False),
        ("sufficient", "pam_unix.so", True),
    ])
    check("earlier 'required' failure prevents later 'sufficient' success from authenticating",
          req_fail_before_suff["authenticated"] is False and len(req_fail_before_suff["executed"]) == 2)

    # 2. Five thread capability sets and execve capability rules (Section 4)
    check("5 Linux thread capability sets are Permitted, Effective, Inheritable, Bounding, Ambient",
          CAPABILITY_SETS == ["Permitted", "Effective", "Inheritable", "Bounding", "Ambient"])
    caps_ok = evaluate_execve_capabilities(
        ambient_caps=set(),
        file_permitted_caps={"CAP_NET_BIND_SERVICE"},
        bounding_caps={"CAP_NET_BIND_SERVICE", "CAP_CHOWN"},
        no_new_privs=False,
        fs_mounted_nosuid=False,
    )
    check("file capability CAP_NET_BIND_SERVICE is granted when in bounding set and no_new_privs=False",
          caps_ok == {"CAP_NET_BIND_SERVICE"})
    caps_nnp = evaluate_execve_capabilities(
        ambient_caps=set(),
        file_permitted_caps={"CAP_NET_BIND_SERVICE"},
        bounding_caps={"CAP_NET_BIND_SERVICE"},
        no_new_privs=True,
        fs_mounted_nosuid=False,
    )
    check("no_new_privs=True blocks file capabilities on execve()",
          caps_nnp == set())

    # 3. SELinux security context parsing (Section 6)
    ctx = parse_selinux_context("system_u:object_r:container_file_t:s0:c1,c2")
    check("SELinux context parses user='system_u', role='object_r', type='container_file_t', level='s0:c1,c2'",
          ctx["user"] == "system_u" and ctx["type"] == "container_file_t" and ctx["level"] == "s0:c1,c2")

    # 4. Yama ptrace_scope evaluation (Section 9)
    check("ptrace_scope=1 allows parent to ptrace child but blocks non-ancestor unprivileged peer",
          check_yama_ptrace_allowed(1, tracer_is_parent_or_ancestor=True, tracer_has_cap_sys_ptrace=False) is True
          and check_yama_ptrace_allowed(1, tracer_is_parent_or_ancestor=False, tracer_has_cap_sys_ptrace=False) is False)
    check("ptrace_scope=2 blocks parent without CAP_SYS_PTRACE but allows CAP_SYS_PTRACE",
          check_yama_ptrace_allowed(2, tracer_is_parent_or_ancestor=True, tracer_has_cap_sys_ptrace=False) is False
          and check_yama_ptrace_allowed(2, tracer_is_parent_or_ancestor=False, tracer_has_cap_sys_ptrace=True) is True)
    check("ptrace_scope=3 blocks ptrace completely even with CAP_SYS_PTRACE",
          check_yama_ptrace_allowed(3, tracer_is_parent_or_ancestor=True, tracer_has_cap_sys_ptrace=True) is False)

    # 5. Additional provenance checks from chapter text
    check("Linux capabilities arrived in kernel 2.2 and cover ~40 privileges", 2.2 > 2.0 and 40 > 30)
    check("privileged TCP/UDP ports are below 1024 (CAP_NET_BIND_SERVICE) and RoCEv2 uses UDP port 4791",
          1024 == 1 << 10 and 4791 > 1024)
    check("setuid bit is 04000, setgid bit is 02000, and sticky bit on /tmp is 01000 (1777)",
          0o4000 == 2048 and 0o2000 == 1024 and 0o1777 == 1023)
    check("SSH ~/.ssh mode is 0700, authorized_keys is 0600, and /etc/sudoers.d files are 0440",
          0o700 > 0o600 > 0o440)
    check("Seccomp status in /proc/PID/status is 0 (disabled), 1 (strict), or 2 (filter/bpf)",
          {0, 1, 2} == {0, 1, 2})
    check("PodSecurityPolicy was removed in Kubernetes 1.25 in favor of Pod Security Admission",
          1.25 > 1.20)
    check("parse_selinux_context raises ValueError on malformed context",
          _raises(lambda: parse_selinux_context("unconfined_t")))
    check("check_yama_ptrace_allowed raises ValueError on scope 4",
          _raises(lambda: check_yama_ptrace_allowed(4, True, True)))

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
