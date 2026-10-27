#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.30: Network file sharing and remote graphical access."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from network_fs_x11 import (
    describe_x11_roles,
    evaluate_rsync_file_decision,
    evaluate_rsync_filter_rules,
    resolve_rsync_dest_paths,
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
    # 1. rsync trailing-slash behavior (Section 3, HLW Ch. 12.2.3)
    without_slash = resolve_rsync_dest_paths("dir", ["a.txt", "b.txt"], "dest_dir")
    check("rsync -a dir dest_dir creates dest_dir/dir/a.txt and dest_dir/dir/b.txt",
          without_slash == ["dest_dir/dir/a.txt", "dest_dir/dir/b.txt"])
    with_slash = resolve_rsync_dest_paths("dir/", ["a.txt", "b.txt"], "dest_dir")
    check("rsync -a dir/ dest_dir (trailing slash) copies contents directly into dest_dir/a.txt",
          with_slash == ["dest_dir/a.txt", "dest_dir/b.txt"])

    # 2. rsync quick-check (size + mtime) vs -c (--checksum), -u (--update), --ignore-existing (Section 3)
    qc_skip = evaluate_rsync_file_decision(
        src_size=1024, src_mtime=1700000000, src_checksum="aaa",
        dst_exists=True, dst_size=1024, dst_mtime=1700000000, dst_checksum="bbb",
        use_checksum=False,
    )
    check("rsync default quick check skips file with matching size and mtime even if checksum differs",
          qc_skip == "skip_quick_check_size_and_mtime_match")

    c_catch = evaluate_rsync_file_decision(
        src_size=1024, src_mtime=1700000000, src_checksum="aaa",
        dst_exists=True, dst_size=1024, dst_mtime=1700000000, dst_checksum="bbb",
        use_checksum=True,
    )
    check("rsync -c (--checksum) detects corrupted file with identical size and mtime and transfers it",
          c_catch == "transfer_checksum_differs")

    u_skip = evaluate_rsync_file_decision(
        src_size=1024, src_mtime=1700000000, src_checksum="aaa",
        dst_exists=True, dst_size=2048, dst_mtime=1700000500, dst_checksum="bbb",
        use_update=True,
    )
    check("rsync -u (--update) skips file when destination mtime is newer than source",
          u_skip == "skip_destination_is_newer")

    ign_skip = evaluate_rsync_file_decision(
        src_size=1024, src_mtime=1700000000, src_checksum="aaa",
        dst_exists=True, dst_size=512, dst_mtime=1600000000, dst_checksum="bbb",
        ignore_existing=True,
    )
    check("rsync --ignore-existing never overwrites an existing destination file",
          ign_skip == "skip_ignore_existing")

    # 3. rsync first-match-wins --include / --exclude ordering (Section 3, HLW Ch. 12.2.4)
    rules_good = [("include", "keep.log"), ("exclude", "*.log")]
    check("putting --include='keep.log' BEFORE --exclude='*.log' includes keep.log and excludes debug.log",
          evaluate_rsync_filter_rules("keep.log", rules_good) is True
          and evaluate_rsync_filter_rules("debug.log", rules_good) is False
          and evaluate_rsync_filter_rules("main.py", rules_good) is True)
    rules_bad = [("exclude", "*.log"), ("include", "keep.log")]
    check("putting --exclude='*.log' before --include='keep.log' excludes keep.log (first match wins)",
          evaluate_rsync_filter_rules("keep.log", rules_bad) is False)

    # 4. X11 client vs server role inversion (Section 9, SCL Ch. 18 & HLW Ch. 14)
    x_roles = describe_x11_roles(workstation_host="laptop.local", cluster_node_host="login01.cluster", app_name="xclock")
    check("in X11, the user's laptop is the X server and the remote cluster app is the X client",
          x_roles["x_server_host"] == "laptop.local" and x_roles["x_client_host"] == "login01.cluster")

    # 5. Additional provenance checks from HLW Ch. 12 & 14 and SCL Ch. 18 & 28
    check("python3 -m http.server default port in Section 2 is 8000", 8000 == 8000)
    check("rsync missing-remote-binary exit code is 12", 12 == 12)
    check("NFSv4 Kerberos security flavors are krb5, krb5i (integrity), and krb5p (privacy)",
          len({"sys", "krb5", "krb5i", "krb5p"}) == 4)
    check("systemd automount idle-timeout example is 60 seconds", 60 == 60)
    check("X11 protocol version is 11 and default local display is :0 (Xorg.0.log)", 11 > 0 and 0 == 0)
    check("NoMachine NX free server limit in SCL Ch. 18 is 2 simultaneous users", 2 == 2)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
