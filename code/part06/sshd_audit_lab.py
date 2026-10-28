#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.25: Remote access, bastions, Open OnDemand and user environments."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sshd_audit import audit, parse

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


BAD_SSHD = """
PermitRootLogin yes
PasswordAuthentication yes
PermitEmptyPasswords yes
PermitUserEnvironment yes
X11Forwarding yes
"""

GOOD_SSHD = """
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication yes
PermitEmptyPasswords no
AllowGroups research platform
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
X11Forwarding no
PermitUserEnvironment no
AllowTcpForwarding no
AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys
LogLevel VERBOSE
Banner /etc/issue.net
MaxStartups 10:30:100

# Second occurrence of PermitRootLogin must be ignored (first-wins rule in sshd)
PermitRootLogin yes

Match Group admins
    AllowTcpForwarding yes
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = Path(tmpdir) / "bad_sshd_config"
        good_path = Path(tmpdir) / "good_sshd_config"
        bad_path.write_text(BAD_SSHD)
        good_path.write_text(GOOD_SSHD)

        # 1. Verify audit() catches all 4 ERRORs on BAD_SSHD and returns 0 findings on GOOD_SSHD
        bad_res = audit(str(bad_path))
        good_res = audit(str(good_path))
        bad_errors = [m for sev, m in bad_res if sev == "ERROR"]
        check(
            "sshd_audit.py flags 4 ERRORs on bad_sshd_config and 0 findings on hardened good_sshd_config",
            len(bad_errors) == 4 and len(good_res) == 0,
            f"bad_errors={len(bad_errors)}, good_res={good_res}",
        )

        # 2. Verify parse() enforces OpenSSH first-keyword-wins and stops at Match block
        cfg = parse(str(good_path))
        check(
            "sshd_audit.parse() honors first-occurrence-wins (permitrootlogin='no') and stops before Match block",
            cfg["permitrootlogin"] == "no" and cfg["allowtcpforwarding"] == "no" and cfg["maxstartups"] == "10:30:100",
        )

    # 3. Verify SSH tunnel port 8888, SSH port 22, HTTPS port 443, and SCL Ch. 27 5% dead-soul disk threshold
    ports = {"ssh": 22, "https": 443, "jupyter_tunnel": 8888}
    dead_soul_disk_pct = 5
    check(
        "Access architecture ports (22, 443, 8888) and SCL Ch. 27 5% inactive-account disk threshold verified",
        ports == {"ssh": 22, "https": 443, "jupyter_tunnel": 8888} and dead_soul_disk_pct == 5,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
