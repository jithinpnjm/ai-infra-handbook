#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.2: The command line: shells, commands, pipes and redirection."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from shell_pipeline import (
    decode_exit_status,
    evaluate_pipeline_exit,
    lookup_errno_meaning,
    resolve_command_in_path,
    select_bash_startup_files,
    simulate_redirection_order,
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
    # 1. Left-to-right redirection order (HLW Ch. 2)
    r_good = simulate_redirection_order("> file 2>&1")
    r_bad = simulate_redirection_order("2>&1 > file")
    check("cmd > file 2>&1 directs both stdout and stderr to file",
          r_good["fd1_stdout"] == "file" and r_good["fd2_stderr"] == "file")
    check("cmd 2>&1 > file leaves stderr on terminal while stdout goes to file",
          r_bad["fd1_stdout"] == "file" and r_bad["fd2_stderr"] == "terminal")
    r_swap = simulate_redirection_order("3>&1 1>&2 2>&3")
    check("3>&1 1>&2 2>&3 swaps stdout and stderr via descriptor 3",
          r_swap["fd1_stdout"] == "terminal" and r_swap["fd2_stderr"] == "terminal")

    # 2. Exit codes (0, 126, 127, 130, 137, 143)
    check("exit code 0 means success", decode_exit_status(0)["success"] is True)
    check("exit code 126 means found but not executable",
          decode_exit_status(126)["code"] == 126 and "not executable" in str(decode_exit_status(126)["reason"]))
    check("exit code 127 means command not found",
          decode_exit_status(127)["code"] == 127 and "not found" in str(decode_exit_status(127)["reason"]))
    check("exit code 130 decodes to 128 + 2 (SIGINT / Ctrl-C)",
          decode_exit_status(130)["signal"] == 2)
    check("exit code 137 decodes to 128 + 9 (SIGKILL / OOMKilled)",
          decode_exit_status(137)["signal"] == 9)
    check("exit code 143 decodes to 128 + 15 (SIGTERM)",
          decode_exit_status(143)["signal"] == 15)

    # 3. Pipeline status and pipefail
    check("without pipefail, false (1) | cat (0) returns 0",
          evaluate_pipeline_exit([1, 0], pipefail=False) == 0)
    check("with set -o pipefail, false (1) | cat (0) returns non-zero (1)",
          evaluate_pipeline_exit([1, 0], pipefail=True) == 1)
    check("with set -o pipefail, [0, 2, 0] returns 2",
          evaluate_pipeline_exit([0, 2, 0], pipefail=True) == 2)

    # 4. Bash startup file selection (HLW Ch. 13)
    login_all = select_bash_startup_files(
        is_login=True,
        is_interactive=True,
        home_files_present=["~/.bash_profile", "~/.bash_login", "~/.profile", "~/.bashrc"],
    )
    check("login bash reads /etc/profile and only the first of ~/.bash_profile, ~/.bash_login, ~/.profile",
          login_all == ["/etc/profile", "~/.bash_profile"])
    login_fallback = select_bash_startup_files(
        is_login=True,
        is_interactive=True,
        home_files_present=["~/.profile", "~/.bashrc"],
    )
    check("login bash falls back to ~/.profile when ~/.bash_profile and ~/.bash_login are absent",
          login_fallback == ["/etc/profile", "~/.profile"])
    inter_nonlogin = select_bash_startup_files(
        is_login=False,
        is_interactive=True,
        home_files_present=["~/.profile", "~/.bashrc"],
    )
    check("interactive non-login bash reads ~/.bashrc only",
          inter_nonlogin == ["~/.bashrc"])
    non_inter = select_bash_startup_files(
        is_login=False,
        is_interactive=False,
        home_files_present=["~/.bash_profile", "~/.bashrc"],
    )
    check("non-interactive bash (cron, ssh host cmd, Slurm script) reads no startup file by default",
          non_inter == [])

    # 5. Command resolution precedence: alias -> function -> builtin -> PATH
    path_dirs = [("/home/alice/bin", ["python3"]), ("/usr/bin", ["python3", "ls"])]
    check("builtin cd resolves before PATH",
          resolve_command_in_path("cd", [], [], ["cd", "export"], path_dirs) == "builtin:cd")
    check("alias ll resolves before functions, builtins, and PATH",
          resolve_command_in_path("ll", ["ll"], [], ["cd"], path_dirs) == "alias:ll")
    check("prepended /home/alice/bin/python3 wins over /usr/bin/python3 in PATH",
          resolve_command_in_path("python3", [], [], ["cd"], path_dirs) == "/home/alice/bin/python3")
    check("missing command returns ENOENT_127",
          resolve_command_in_path("nosuchcmd", [], [], ["cd"], path_dirs) == "ENOENT_127")

    # 6. Unix errno table (HLW Ch. 2)
    check("ENOENT maps to 'No such file or directory'",
          lookup_errno_meaning("ENOENT")[0] == "No such file or directory")
    check("EACCES maps to 'Permission denied'",
          lookup_errno_meaning("EACCES")[0] == "Permission denied")
    check("EPERM maps to 'Operation not permitted'",
          lookup_errno_meaning("EPERM")[0] == "Operation not permitted")
    check("ENOTDIR maps to 'Not a directory'",
          lookup_errno_meaning("ENOTDIR")[0] == "Not a directory")
    check("ENOSPC maps to 'No space left on device'",
          lookup_errno_meaning("ENOSPC")[0] == "No space left on device")
    check("E2BIG maps to 'Argument list too long'",
          lookup_errno_meaning("E2BIG")[0] == "Argument list too long")

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
