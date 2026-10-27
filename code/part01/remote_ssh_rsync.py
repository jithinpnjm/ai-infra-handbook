"""Chapter 1.5 model: SSH StrictModes permission checks, ~/.ssh/config first-match
precedence, port-forwarding tunnel direction (-L, -R, -D), and rsync trailing-slash
vs scp -r directory resolution.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 2
  (section 2.12 text editors, Robbins et al. Learning the vi and Vim Editors 7th ed.,
  Cameron et al. Learning GNU Emacs 3rd ed.) and Chapter 12 (scp -r nesting pitfall,
  rsync trailing-slash rule, --bwlimit=10000 KB/s uplink ACK starvation, SSHFS, NFS).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapters 10 and 18
  (OpenSSH keys, StrictModes 700/600, X11 xauth and XAUTHORITY under sudo, pdsh/clush,
  tmux/screen, ipmitool lanplus SOL).
"""
from typing import Dict, List, Tuple


def validate_ssh_strict_modes(
    home_mode_octal: int,
    ssh_dir_mode_octal: int,
    authorized_keys_mode_octal: int,
    private_key_mode_octal: int,
) -> Dict[str, object]:
    """Validate OpenSSH StrictModes permission rules (no group/world write on ~, ~/.ssh, authorized_keys; 600/400 on private key)."""
    reasons: List[str] = []
    if home_mode_octal & 0o022:
        reasons.append("home_dir_group_or_world_writable")
    if ssh_dir_mode_octal & 0o077:
        reasons.append("ssh_dir_too_open_must_be_700")
    if authorized_keys_mode_octal & 0o022:
        reasons.append("authorized_keys_group_or_world_writable")
    if private_key_mode_octal & 0o077:
        reasons.append("private_key_unprotected_must_be_600_or_400")
    return {"accepted": len(reasons) == 0, "reasons": reasons}


def resolve_rsync_destination_paths(
    source_arg: str,
    dest_arg: str,
    source_files: List[str],
) -> List[str]:
    """Model the rsync trailing-slash rule: 'src/' copies contents into dest; 'src' creates dest/src/."""
    dest_clean = dest_arg.rstrip("/")
    src_clean = source_arg.rstrip("/")
    src_base = src_clean.split("/")[-1]
    if source_arg.endswith("/"):
        return [f"{dest_clean}/{f}" for f in source_files]
    return [f"{dest_clean}/{src_base}/{f}" for f in source_files]


def resolve_scp_recursive_destination(
    source_dir_name: str,
    dest_dir: str,
    dest_already_exists: bool,
) -> str:
    """Model HLW Ch. 12 scp -r pitfall: if dest_dir already exists, scp -r nests source_dir inside dest_dir."""
    dest_clean = dest_dir.rstrip("/")
    if dest_already_exists:
        return f"{dest_clean}/{source_dir_name}"
    return dest_clean


def describe_ssh_port_forward(flag: str, spec: str, ssh_server: str) -> Dict[str, str]:
    """Parse -L local_port:target_host:target_port, -R remote_port:target_host:target_port, or -D socks_port."""
    if flag == "-D":
        return {
            "mode": "dynamic_socks",
            "listener_host": "local_client",
            "listener_port": spec,
            "egress_via": ssh_server,
        }
    parts = spec.split(":")
    if len(parts) != 3:
        raise ValueError(f"Expected port:host:port specification, got: {spec}")
    listen_p, tgt_h, tgt_p = parts
    if flag == "-L":
        return {
            "mode": "local_forward",
            "listener_host": "local_client",
            "listener_port": listen_p,
            "target_host_from_server": tgt_h,
            "target_port": tgt_p,
            "via_ssh_server": ssh_server,
        }
    if flag == "-R":
        return {
            "mode": "remote_forward",
            "listener_host": ssh_server,
            "listener_port": listen_p,
            "target_host_from_client": tgt_h,
            "target_port": tgt_p,
        }
    raise ValueError(f"Unsupported forwarding flag: {flag}")


def evaluate_ssh_config_first_match(
    hostname: str,
    stanzas: List[Tuple[str, Dict[str, str]]],
) -> Dict[str, str]:
    """Apply OpenSSH first-match-wins rule across Host stanzas in ~/.ssh/config."""
    import fnmatch

    effective: Dict[str, str] = {}
    for pattern_str, kv in stanzas:
        patterns = pattern_str.split()
        if any(fnmatch.fnmatch(hostname, pat) for pat in patterns):
            for k, v in kv.items():
                if k not in effective:
                    effective[k] = v
    return effective
