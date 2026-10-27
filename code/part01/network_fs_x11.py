"""Chapter 1.30 model: rsync trailing-slash path resolution and --delete mirror
semantics, rsync quick-check (size + mtime) vs --checksum (-c) and --update (-u),
first-match-wins --include/--exclude filter evaluation, and X11 client/server
role and DISPLAY mapping.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 12
  ("Network File Transfer and Sharing": SimpleHTTPServer / http.server, rsync
  exact copies, trailing slash, excludes/includes, quick check vs -c, -z,
  --bwlimit, Samba smb.conf and smbpasswd, CIFS, SSHFS, NFS, cloud storage, AFS
  and Kerberos) and Chapter 14 ("The Linux Desktop and Printing": Wayland vs X11,
  compositors, window managers, toolkits, D-Bus system/session buses, xwininfo/xev/xinput,
  CUPS printing).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 18
  ("Remote User Access": SSH, PuTTY/WinSCP, FTP vs SFTP, web servers, X11
  client/server roles, Xming/VcXsrv, xauth vs xhost, VNC, RDP, x2go, NX, SPICE)
  and Chapter 28 (NFS server/client and Xorg recipes).
"""
import fnmatch
from typing import Dict, List, Set, Tuple


def resolve_rsync_dest_paths(
    source_arg: str,
    source_files: List[str],
    dest_dir: str,
) -> List[str]:
    """Compute resulting destination file paths for 'rsync -a dir dest_dir' vs 'rsync -a dir/ dest_dir'."""
    clean_dest = dest_dir.rstrip("/")
    has_trailing_slash = source_arg.endswith("/")
    src_basename = source_arg.rstrip("/").split("/")[-1]
    out: List[str] = []
    for f in source_files:
        rel = f.lstrip("/")
        if has_trailing_slash:
            out.append(f"{clean_dest}/{rel}")
        else:
            out.append(f"{clean_dest}/{src_basename}/{rel}")
    return sorted(out)


def evaluate_rsync_file_decision(
    src_size: int,
    src_mtime: int,
    src_checksum: str,
    dst_exists: bool,
    dst_size: int = 0,
    dst_mtime: int = 0,
    dst_checksum: str = "",
    use_checksum: bool = False,
    use_update: bool = False,
    ignore_existing: bool = False,
) -> str:
    """Determine whether rsync transfers or skips a file under quick-check, -c, -u, and --ignore-existing."""
    if not dst_exists:
        return "transfer_new_file"
    if ignore_existing:
        return "skip_ignore_existing"
    if use_update and dst_mtime > src_mtime:
        return "skip_destination_is_newer"
    if use_checksum:
        return "skip_checksum_match" if src_checksum == dst_checksum else "transfer_checksum_differs"
    if src_size == dst_size and src_mtime == dst_mtime:
        return "skip_quick_check_size_and_mtime_match"
    return "transfer_size_or_mtime_differs"


def evaluate_rsync_filter_rules(
    filename: str,
    rules: List[Tuple[str, str]],
) -> bool:
    """Evaluate ordered rsync ('include'|'exclude', pattern) rules; first match wins (default is include)."""
    for action, pat in rules:
        if fnmatch.fnmatch(filename, pat):
            return action == "include"
    return True


def describe_x11_roles(
    workstation_host: str,
    cluster_node_host: str,
    app_name: str = "xclock",
) -> Dict[str, str]:
    """Return the X11 Server (owns display/keyboard/mouse) and X11 Client (application) hosts."""
    return {
        "x_server_host": workstation_host,
        "x_client_host": cluster_node_host,
        "x_client_program": app_name,
    }
