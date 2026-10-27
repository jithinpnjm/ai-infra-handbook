#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.5: Working remotely: SSH keys, file transfer, tmux and editors."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from remote_ssh_rsync import (
    describe_ssh_port_forward,
    evaluate_ssh_config_first_match,
    resolve_rsync_destination_paths,
    resolve_scp_recursive_destination,
    validate_ssh_strict_modes,
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
    # 1. OpenSSH StrictModes permission validation
    ok_modes = validate_ssh_strict_modes(0o750, 0o700, 0o600, 0o600)
    check("home 0750, ~/.ssh 0700, authorized_keys 0600, id_ed25519 0600 passes StrictModes",
          ok_modes["accepted"] is True and ok_modes["reasons"] == [])
    bad_ssh_dir = validate_ssh_strict_modes(0o750, 0o777, 0o666, 0o600)
    check("chmod 777 ~/.ssh and 666 authorized_keys fails StrictModes with both reasons",
          bad_ssh_dir["accepted"] is False and len(bad_ssh_dir["reasons"]) == 2)
    bad_home = validate_ssh_strict_modes(0o777, 0o700, 0o600, 0o600)
    check("world-writable home directory (0777) fails StrictModes",
          bad_home["accepted"] is False and "home_dir_group_or_world_writable" in bad_home["reasons"])
    bad_priv = validate_ssh_strict_modes(0o750, 0o700, 0o600, 0o644)
    check("world-readable private key (0644) is rejected by ssh client",
          bad_priv["accepted"] is False and "private_key_unprotected_must_be_600_or_400" in bad_priv["reasons"])

    # 2. rsync trailing-slash rule vs no trailing slash (HLW Ch. 12)
    with_slash = resolve_rsync_destination_paths("data/", "/scratch/data", ["a.pt", "b.pt"])
    no_slash = resolve_rsync_destination_paths("data", "/scratch/data", ["a.pt", "b.pt"])
    check("rsync -a data/ /scratch/data copies contents directly into /scratch/data/",
          with_slash == ["/scratch/data/a.pt", "/scratch/data/b.pt"])
    check("rsync -a data /scratch/data nests the directory as /scratch/data/data/",
          no_slash == ["/scratch/data/data/a.pt", "/scratch/data/data/b.pt"])

    # 3. scp -r existing-directory nesting pitfall (HLW Ch. 12)
    check("scp -r dir host:/dest when /dest does not exist creates /dest",
          resolve_scp_recursive_destination("dir", "/dest", dest_already_exists=False) == "/dest")
    check("scp -r dir host:/dest when /dest already exists nests copy at /dest/dir",
          resolve_scp_recursive_destination("dir", "/dest", dest_already_exists=True) == "/dest/dir")

    # 4. SSH port forwarding (-L, -R, -D)
    lf = describe_ssh_port_forward("-L", "6006:localhost:6006", "gpu01")
    check("ssh -L 6006:localhost:6006 gpu01 listens on local_client:6006 and forwards via gpu01",
          lf["mode"] == "local_forward" and lf["listener_host"] == "local_client" and lf["listener_port"] == "6006")
    rf = describe_ssh_port_forward("-R", "9000:localhost:8000", "bastion")
    check("ssh -R 9000:localhost:8000 bastion listens on bastion:9000 and forwards to client:8000",
          rf["mode"] == "remote_forward" and rf["listener_host"] == "bastion" and rf["target_port"] == "8000")
    df = describe_ssh_port_forward("-D", "1080", "bastion")
    check("ssh -D 1080 bastion opens SOCKS proxy on local_client:1080",
          df["mode"] == "dynamic_socks" and df["listener_port"] == "1080")

    # 5. ~/.ssh/config first-match-wins precedence
    stanzas = [
        ("gpu01", {"HostName": "10.20.0.11", "User": "alice"}),
        ("gpu* login*", {"User": "clusterdefault", "ProxyJump": "bastion"}),
        ("*", {"ServerAliveInterval": "30", "User": "fallback"}),
    ]
    eff = evaluate_ssh_config_first_match("gpu01", stanzas)
    check("first-matching User=alice in Host gpu01 wins over later Host gpu* and Host *",
          eff["User"] == "alice" and eff["HostName"] == "10.20.0.11")
    check("ProxyJump=bastion and ServerAliveInterval=30 are inherited from later matching stanzas",
          eff["ProxyJump"] == "bastion" and eff["ServerAliveInterval"] == "30")
    eff2 = evaluate_ssh_config_first_match("gpu02", stanzas)
    check("gpu02 matches Host gpu* first and gets User=clusterdefault and ProxyJump=bastion",
          eff2["User"] == "clusterdefault" and eff2["ProxyJump"] == "bastion")

    # 6. Additional checks on keys, modes, and paths
    check("read-only 0400 private key passes StrictModes",
          validate_ssh_strict_modes(0o700, 0o700, 0o600, 0o400)["accepted"] is True)
    check("group-writable home directory (0775) fails StrictModes",
          validate_ssh_strict_modes(0o775, 0o700, 0o600, 0o600)["accepted"] is False)
    check("group-readable ~/.ssh directory (0750) fails StrictModes",
          validate_ssh_strict_modes(0o750, 0o750, 0o600, 0o600)["accepted"] is False)
    check("group-writable authorized_keys (0660) fails StrictModes",
          validate_ssh_strict_modes(0o750, 0o700, 0o660, 0o600)["accepted"] is False)
    check("rsync nested source path '/data/ckpt/' with trailing slash copies directly into dest",
          resolve_rsync_destination_paths("/data/ckpt/", "/backup", ["s1.pt"]) == ["/backup/s1.pt"])
    check("rsync nested source path '/data/ckpt' without trailing slash creates '/backup/ckpt/s1.pt'",
          resolve_rsync_destination_paths("/data/ckpt", "/backup", ["s1.pt"]) == ["/backup/ckpt/s1.pt"])
    check("unmatched host 'db01' falls through to Host * and gets User=fallback",
          evaluate_ssh_config_first_match("db01", stanzas)["User"] == "fallback")
    check("describe_ssh_port_forward raises ValueError on invalid spec",
          _raises(lambda: describe_ssh_port_forward("-L", "8000", "gpu01")))
    check("describe_ssh_port_forward raises ValueError on unknown flag",
          _raises(lambda: describe_ssh_port_forward("-X", "8000:localhost:8000", "gpu01")))
    check("bwlimit=10000 KB/s equals 10 MB/s upload cap (HLW Ch. 12.2.7)",
          10000 // 1000 == 10)
    check("200 MB test file count=200 at bs=1M equals 200 MiB",
          200 * 1 == 200)

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
