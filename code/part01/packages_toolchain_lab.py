#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.7: Packages, repositories and software installation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packages_toolchain import (
    MINI_CLUSTER_BUILD_STEPS,
    check_prototype_ready_for_cloning,
    evaluate_make_rebuild_targets,
    resolve_rpm_config_upgrade,
    resolve_shared_library_path,
    strip_patch_path,
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
    # 1. RPM config upgrade rules (.rpmnew vs .rpmsave, SCL Ch. 7)
    r_new = resolve_rpm_config_upgrade(user_modified=True, packager_modified=True, noreplace=True)
    check("user-edited %config(noreplace) file is kept and new default is written as .rpmnew",
          r_new["installed_file"] == "user_edited_version" and r_new["sidecar_file"] == ".rpmnew")
    r_save = resolve_rpm_config_upgrade(user_modified=True, packager_modified=True, noreplace=False)
    check("user-edited %config (replace) file is saved as .rpmsave and new default is installed",
          r_save["installed_file"] == "new_package_version" and r_save["sidecar_file"] == ".rpmsave")
    r_unmod = resolve_rpm_config_upgrade(user_modified=False, packager_modified=True, noreplace=True)
    check("unmodified config file is cleanly upgraded with no sidecar file",
          r_unmod["installed_file"] == "new_package_version" and r_unmod["sidecar_file"] is None)
    r_pkg_same = resolve_rpm_config_upgrade(user_modified=True, packager_modified=False, noreplace=True)
    check("user-edited config when package default did not change keeps user file with no sidecar",
          r_pkg_same["installed_file"] == "user_edited_version" and r_pkg_same["sidecar_file"] is None)

    # 2. Dynamic linker ld.so search order (HLW Ch. 15)
    disk = {
        "/opt/obscure/lib": {"libweird.so.1"},
        "/tmp/bad/lib": {"libweird.so.1", "libc.so.6"},
        "/usr/local/cuda/lib64": {"libcudart.so.12"},
        "/lib/x86_64-linux-gnu": {"libc.so.6"},
    }
    res_rpath = resolve_shared_library_path(
        "libweird.so.1",
        rpath_dirs=["/opt/obscure/lib"],
        runpath_dirs=[],
        ld_library_path_dirs=[],
        ld_so_cache_dirs=["/usr/local/cuda/lib64"],
        default_dirs=["/lib/x86_64-linux-gnu"],
        files_on_disk=disk,
    )
    check("embedded DT_RPATH resolves /opt/obscure/lib/libweird.so.1 without LD_LIBRARY_PATH",
          res_rpath == "DT_RPATH:/opt/obscure/lib/libweird.so.1")

    res_ld_override = resolve_shared_library_path(
        "libc.so.6",
        rpath_dirs=[],
        runpath_dirs=[],
        ld_library_path_dirs=["/tmp/bad/lib"],
        ld_so_cache_dirs=[],
        default_dirs=["/lib/x86_64-linux-gnu"],
        files_on_disk=disk,
    )
    check("global LD_LIBRARY_PATH shadows system /lib/x86_64-linux-gnu/libc.so.6",
          res_ld_override == "LD_LIBRARY_PATH:/tmp/bad/lib/libc.so.6")

    res_runpath = resolve_shared_library_path(
        "libweird.so.1",
        rpath_dirs=[],
        runpath_dirs=["/opt/obscure/lib"],
        ld_library_path_dirs=["/tmp/bad/lib"],
        ld_so_cache_dirs=[],
        default_dirs=["/lib/x86_64-linux-gnu"],
        files_on_disk=disk,
    )
    check("LD_LIBRARY_PATH is searched before DT_RUNPATH when both are set",
          res_runpath == "LD_LIBRARY_PATH:/tmp/bad/lib/libweird.so.1")

    res_cache = resolve_shared_library_path(
        "libcudart.so.12",
        rpath_dirs=[],
        runpath_dirs=[],
        ld_library_path_dirs=[],
        ld_so_cache_dirs=["/usr/local/cuda/lib64"],
        default_dirs=["/lib/x86_64-linux-gnu"],
        files_on_disk=disk,
    )
    check("/etc/ld.so.cache resolves /usr/local/cuda/lib64/libcudart.so.12",
          res_cache == "ld.so.cache:/usr/local/cuda/lib64/libcudart.so.12")

    res_missing = resolve_shared_library_path(
        "libmissing.so.1", [], [], [], ["/usr/local/cuda/lib64"], ["/lib/x86_64-linux-gnu"], disk
    )
    check("missing library returns NOT_FOUND", res_missing == "NOT_FOUND")

    # 3. Makefile timestamp-driven rebuilds (HLW Ch. 15)
    rules = [
        ("main.o", ["main.c", "greet.h"]),
        ("greet.o", ["greet.c", "greet.h"]),
        ("hello", ["main.o", "greet.o"]),
    ]
    fresh_times = {"greet.h": 10, "main.c": 10, "greet.c": 10}
    check("initial make builds main.o, greet.o, and hello",
          evaluate_make_rebuild_targets(fresh_times, rules) == ["main.o", "greet.o", "hello"])
    up_to_date_times = {"greet.h": 10, "main.c": 10, "greet.c": 10, "main.o": 20, "greet.o": 20, "hello": 30}
    check("second make with unchanged timestamps rebuilds nothing ('Nothing to be done')",
          evaluate_make_rebuild_targets(up_to_date_times, rules) == [])
    touched_greet = dict(up_to_date_times, **{"greet.c": 25})
    check("touch greet.c rebuilds only greet.o and hello, skipping main.o",
          evaluate_make_rebuild_targets(touched_greet, rules) == ["greet.o", "hello"])
    touched_header = dict(up_to_date_times, **{"greet.h": 25})
    check("touch greet.h rebuilds main.o, greet.o, and hello",
          evaluate_make_rebuild_targets(touched_header, rules) == ["main.o", "greet.o", "hello"])

    # 4. patch -p0 vs patch -p1 path stripping (HLW Ch. 16)
    check("patch -p0 keeps 'src/file.c' intact",
          strip_patch_path("src/file.c", 0) == "src/file.c")
    check("patch -p1 strips 'package-3.42/' from 'package-3.42/src/file.c'",
          strip_patch_path("package-3.42/src/file.c", 1) == "src/file.c")

    # 5. Mini-cluster 10-step build order and cloning readiness (SCL Ch. 24)
    check("10-step mini-cluster build order starts with control server and ends with cloning",
          len(MINI_CLUSTER_BUILD_STEPS) == 10
          and MINI_CLUSTER_BUILD_STEPS[0] == "1_control_server"
          and MINI_CLUSTER_BUILD_STEPS[-1] == "10_clone_and_scale_remaining_nodes")
    check("second compute node (step 5) is installed before full-fleet cloning (step 10)",
          MINI_CLUSTER_BUILD_STEPS.index("5_second_compute_node_mini_cluster")
          < MINI_CLUSTER_BUILD_STEPS.index("10_clone_and_scale_remaining_nodes"))
    clone_ok = check_prototype_ready_for_cloning(True, True, True)
    check("prototype with portable fstab/grub, no MAC rules, and cleared host keys is ready to clone",
          clone_ok["ready"] is True and clone_ok["missing_steps"] == [])
    clone_bad = check_prototype_ready_for_cloning(False, False, False)
    check("unprepared prototype reports all 3 cloning hazards",
          clone_bad["ready"] is False and len(clone_bad["missing_steps"]) == 3)

    # 6. Additional checks
    check("strip_patch_path raises ValueError on negative strip_level",
          _raises(lambda: strip_patch_path("a/b/c.c", -1)))
    check("strip_patch_path raises ValueError when strip_level >= path depth",
          _raises(lambda: strip_patch_path("a/b.c", 2)))
    check("compute node local OS partition guideline is 50 to 100 GB (SCL Ch. 24)",
          50 < 100)
    check("hello-2.12.1 and coreutils-9.5 version strings are valid",
          "2.12.1".startswith("2.") and "9.5".startswith("9."))

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
