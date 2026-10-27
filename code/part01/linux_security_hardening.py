"""Chapter 1.21 model: PAM stack evaluation (required, requisite, sufficient,
optional), Linux 5 capability sets and no_new_privs execve transition, SELinux
security context (user:role:type:level) parsing, and Yama ptrace_scope access
control.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 7
  (user databases, ruid/euid/suid, PAM function types auth/account/session/password
  and control flags required/requisite/sufficient/optional, chsh stack example).
- Josh Rosso et al., Production Kubernetes (production-kubernetes), Chapter 8
  (Kubernetes admission chain: mutating -> schema validation -> validating -> etcd,
  Pod Security Standards privileged/baseline/restricted).
- nvidia-devops/volume-10/03-os-provisioning-and-linux-security-hardening.md
  (GPU/HPC CIS hardening exceptions, Yama ptrace_scope, SELinux, Secure Boot MOK).
"""
from typing import Dict, List, Set, Tuple


CAPABILITY_SETS: List[str] = [
    "Permitted",
    "Effective",
    "Inheritable",
    "Bounding",
    "Ambient",
]


def evaluate_pam_stack(rules: List[Tuple[str, str, bool]]) -> Dict[str, object]:
    """Evaluate a sequence of PAM rules: (control_flag, module_name, module_succeeded).
    Control flags: 'required', 'requisite', 'sufficient', 'optional'.
    """
    executed_modules: List[str] = []
    prior_required_failed = False
    decided_success = False

    for control, mod, ok in rules:
        executed_modules.append(mod)
        if control == "required":
            if not ok:
                prior_required_failed = True
        elif control == "requisite":
            if not ok:
                return {"authenticated": False, "executed": executed_modules}
        elif control == "sufficient":
            if ok and not prior_required_failed:
                return {"authenticated": True, "executed": executed_modules}
        elif control == "optional":
            if ok:
                decided_success = True
        else:
            raise ValueError(f"Unsupported PAM control flag: {control}")

        if ok and control in {"required", "requisite"}:
            decided_success = True

    return {
        "authenticated": (not prior_required_failed) and decided_success,
        "executed": executed_modules,
    }


def parse_selinux_context(ctx: str) -> Dict[str, str]:
    """Parse an SELinux security context 'user:role:type:level' into its four components."""
    parts = ctx.strip().split(":", 3)
    if len(parts) != 4:
        raise ValueError(f"Invalid SELinux context (expected 4 colon-separated fields): {ctx}")
    return {
        "user": parts[0],
        "role": parts[1],
        "type": parts[2],
        "level": parts[3],
    }


def evaluate_execve_capabilities(
    ambient_caps: Set[str],
    file_permitted_caps: Set[str],
    bounding_caps: Set[str],
    no_new_privs: bool,
    fs_mounted_nosuid: bool,
) -> Set[str]:
    """Model which file capabilities survive execve() given bounding set, no_new_privs, and nosuid."""
    if no_new_privs or fs_mounted_nosuid:
        return set(ambient_caps) & set(bounding_caps)
    gained_from_file = set(file_permitted_caps) & set(bounding_caps)
    return (set(ambient_caps) & set(bounding_caps)) | gained_from_file


def check_yama_ptrace_allowed(
    ptrace_scope: int,
    tracer_is_parent_or_ancestor: bool,
    tracer_has_cap_sys_ptrace: bool,
) -> bool:
    """Evaluate kernel.yama.ptrace_scope (0=classic, 1=restricted to descendants, 2=admin only, 3=none)."""
    if ptrace_scope not in {0, 1, 2, 3}:
        raise ValueError(f"Invalid ptrace_scope: {ptrace_scope}")
    if ptrace_scope == 3:
        return False
    if tracer_has_cap_sys_ptrace:
        return True
    if ptrace_scope == 0:
        return True
    if ptrace_scope == 1:
        return tracer_is_parent_or_ancestor
    return False
