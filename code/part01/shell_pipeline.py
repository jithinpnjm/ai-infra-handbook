"""Chapter 1.2 model: Shell parsing, quoting, redirection order, exit status
decoding (126, 127, 128+N), PATH lookup, startup file selection, and errno codes.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 2
  ("Basic Commands and Directory Hierarchy") and Chapter 13 ("User Environments"):
  globbing, single vs double quoting, standard streams (fd 0, 1, 2), left-to-right
  redirection order, login vs non-login startup file order (/etc/profile, then first
  of ~/.bash_profile, ~/.bash_login, ~/.profile; interactive check on $-), and
  standard Unix errno messages.
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapters 7 and 8:
  brace expansion, seq -w, 3>&1 1>&2 2>&3 stream swap, exit codes, and pipelines.
- Jason Edelman et al., Network Programmability and Automation, 2nd ed. (NPA),
  Chapter 3: prompt anatomy, cd - toggle, and relative vs absolute paths.
"""
from typing import Dict, List, Optional, Tuple


ERRNO_TABLE: Dict[str, Tuple[str, str]] = {
    "ENOENT": ("No such file or directory", "path or #! interpreter does not exist"),
    "EACCES": ("Permission denied", "insufficient permissions on file or directory component"),
    "EPERM": ("Operation not permitted", "operation requires root or a kernel capability"),
    "EEXIST": ("File exists", "target path already exists"),
    "ENOTDIR": ("Not a directory", "a path component used as a directory is a regular file"),
    "EISDIR": ("Is a directory", "attempted file read/write on a directory"),
    "ENOSPC": ("No space left on device", "filesystem out of data blocks or inodes"),
    "EMFILE": ("Too many open files", "per-process open file descriptor limit reached"),
    "E2BIG": ("Argument list too long", "expanded arguments exceed kernel ARG_MAX"),
}


def simulate_redirection_order(order: str) -> Dict[str, str]:
    """Simulate fd 1 (stdout) and fd 2 (stderr) targets under left-to-right redirection."""
    fd1 = "terminal"
    fd2 = "terminal"
    if order == "> file 2>&1":
        fd1 = "file"
        fd2 = fd1  # points to where fd1 currently goes ("file")
    elif order == "2>&1 > file":
        fd2 = fd1  # points to where fd1 currently goes ("terminal")
        fd1 = "file"
    elif order == "3>&1 1>&2 2>&3":
        fd3 = fd1
        fd1 = fd2
        fd2 = fd3
    else:
        raise ValueError(f"Unsupported redirection pattern: {order}")
    return {"fd1_stdout": fd1, "fd2_stderr": fd2}


def decode_exit_status(code: int) -> Dict[str, object]:
    """Decode POSIX/bash exit status codes including 126, 127, and 128+N signal exits."""
    if not (0 <= code <= 255):
        raise ValueError("Exit code must be between 0 and 255")
    signals = {2: "SIGINT", 9: "SIGKILL", 11: "SIGSEGV", 15: "SIGTERM"}
    if code == 0:
        return {"code": 0, "success": True, "reason": "success", "signal": None}
    if code == 126:
        return {"code": 126, "success": False, "reason": "command found but not executable", "signal": None}
    if code == 127:
        return {"code": 127, "success": False, "reason": "command not found in PATH", "signal": None}
    if code > 128:
        sig_num = code - 128
        sig_name = signals.get(sig_num, f"SIG{sig_num}")
        return {"code": code, "success": False, "reason": f"killed by signal {sig_num} ({sig_name})", "signal": sig_num}
    return {"code": code, "success": False, "reason": "general or command-specific error", "signal": None}


def evaluate_pipeline_exit(stage_codes: List[int], pipefail: bool = False) -> int:
    """Return pipeline exit status under default bash rules vs set -o pipefail."""
    if not stage_codes:
        raise ValueError("stage_codes must not be empty")
    if not pipefail:
        return stage_codes[-1]
    for code in reversed(stage_codes):
        if code != 0:
            return code
    return 0


def select_bash_startup_files(
    is_login: bool,
    is_interactive: bool,
    home_files_present: List[str],
    bash_env: Optional[str] = None,
) -> List[str]:
    """Return the exact sequence of startup files bash reads (HLW Ch. 13)."""
    read_files: List[str] = []
    if is_login:
        read_files.append("/etc/profile")
        for candidate in ("~/.bash_profile", "~/.bash_login", "~/.profile"):
            if candidate in home_files_present:
                read_files.append(candidate)
                break
        return read_files
    if is_interactive:
        if "~/.bashrc" in home_files_present:
            read_files.append("~/.bashrc")
        return read_files
    if bash_env:
        read_files.append(bash_env)
    return read_files


def resolve_command_in_path(
    cmd: str,
    aliases: List[str],
    functions: List[str],
    builtins: List[str],
    path_dirs: List[Tuple[str, List[str]]],
) -> str:
    """Resolve a command name following bash precedence: alias -> function -> builtin -> PATH."""
    if cmd in aliases:
        return f"alias:{cmd}"
    if cmd in functions:
        return f"function:{cmd}"
    if cmd in builtins:
        return f"builtin:{cmd}"
    for d, binaries in path_dirs:
        if cmd in binaries:
            return f"{d}/{cmd}"
    return "ENOENT_127"


def lookup_errno_meaning(code: str) -> Tuple[str, str]:
    """Return standard strerror text and operational cause for an errno symbol."""
    if code not in ERRNO_TABLE:
        raise ValueError(f"Unknown errno code: {code}")
    return ERRNO_TABLE[code]
