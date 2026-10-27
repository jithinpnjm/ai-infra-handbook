"""Chapter 1.29 model: sshd_config Allow/Deny directive evaluation order
(DenyUsers -> AllowUsers -> DenyGroups -> AllowGroups), pdsh/ClusterShell
node-range expansion and folding (node-[01-03,10]), SSH escape-sequence
nesting for IPMI SOL (~~.), and ipmitool invocation security auditing.

Sources modeled:
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 10
  ("Remote Management": out-of-band BMC/IPMI pre-configuration, 1995 Tatu Ylönen
  SSH protocol, 7-step session sequence, ssh/ssh_config/sshd_config options and
  Match blocks, host-based auth /etc/shosts.equiv, pdsh/pdcp and ClusterShell
  clush/cluset with Slurm @sp/@st groups, screen/tmux, ipmitool lan/power/sol/user,
  conman, powerman, iKVM) and Chapter 7 ("Cluster" commands loop).
"""
import fnmatch
from typing import Dict, List, Set


def evaluate_sshd_access_rules(
    username: str,
    user_groups: Set[str],
    deny_users: List[str],
    allow_users: List[str],
    deny_groups: List[str],
    allow_groups: List[str],
) -> Dict[str, object]:
    """Evaluate OpenSSH access directives in canonical order:
    1. DenyUsers, 2. AllowUsers, 3. DenyGroups, 4. AllowGroups.
    """
    for pat in deny_users:
        if fnmatch.fnmatch(username, pat):
            return {"allowed": False, "decided_by": "DenyUsers"}
    if allow_users:
        if not any(fnmatch.fnmatch(username, pat) for pat in allow_users):
            return {"allowed": False, "decided_by": "AllowUsers_not_matched"}
    for pat in deny_groups:
        if any(fnmatch.fnmatch(g, pat) for g in user_groups):
            return {"allowed": False, "decided_by": "DenyGroups"}
    if allow_groups:
        if not any(any(fnmatch.fnmatch(g, pat) for g in user_groups) for pat in allow_groups):
            return {"allowed": False, "decided_by": "AllowGroups_not_matched"}
    return {"allowed": True, "decided_by": "permitted"}


def expand_nodeset_expression(expr: str) -> List[str]:
    """Expand a ClusterShell/pdsh node expression like 'node-[01-03,10]' into ['node-01', 'node-02', 'node-03', 'node-10']."""
    if "[" not in expr or not expr.endswith("]"):
        return [expr.strip()]
    prefix, bracket = expr.split("[", 1)
    inner = bracket[:-1]
    result: List[str] = []
    for item in inner.split(","):
        item = item.strip()
        if "-" in item:
            a_str, b_str = item.split("-", 1)
            width = len(a_str)
            for n in range(int(a_str), int(b_str) + 1):
                result.append(f"{prefix}{n:0{width}d}")
        else:
            result.append(f"{prefix}{item}")
    return result


def compute_ssh_nested_escape(ssh_hops: int, action_char: str = ".") -> str:
    """Compute the Enter + tilde escape sequence to reach hop N (1 = outer ssh '~.', 2 = inner ssh or IPMI SOL '~~.')."""
    if ssh_hops < 1:
        raise ValueError("ssh_hops must be >= 1")
    return ("~" * ssh_hops) + action_char


def audit_ipmitool_command(
    interface_type: str,
    password_delivery: str,
) -> Dict[str, object]:
    """Audit an ipmitool invocation for IPMI 2.0 (-I lanplus) and safe password delivery (-f or -E, never -P)."""
    issues: List[str] = []
    if interface_type != "lanplus":
        issues.append("use_lanplus_for_ipmi_2_0_and_sol")
    if password_delivery == "-P":
        issues.append("password_on_cmdline_exposed_in_ps_and_history")
    elif password_delivery not in {"-f", "-E"}:
        issues.append("unknown_password_delivery_flag")
    return {"safe": len(issues) == 0, "issues": issues}
