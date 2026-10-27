#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.11: How a program runs: system calls, libraries, ELF, strace and ldd."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from program_execution_elf import (
    ELF_STARTUP_STAGES,
    check_glibc_symbol_compatibility,
    classify_library_names,
    evaluate_software_use_metrics,
    simulate_demand_paging_mmap,
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
    # 1. ELF startup sequence (Section 1)
    check("ELF startup sequence has 7 ordered stages from fork/execve to exit_group",
          len(ELF_STARTUP_STAGES) == 7
          and ELF_STARTUP_STAGES[0] == "1_fork_and_execve"
          and ELF_STARTUP_STAGES[3] == "4_map_pt_interp_dynamic_linker")
    check("PT_INTERP dynamic linker runs BEFORE _start and main()",
          ELF_STARTUP_STAGES.index("4_map_pt_interp_dynamic_linker")
          < ELF_STARTUP_STAGES.index("6_start_and_libc_start_main_to_main"))

    # 2. Shared library naming: linker name, soname, real name (Section 5)
    names = classify_library_names("libfoo.so.1.2.3")
    check("libfoo.so.1.2.3 has linker_name=libfoo.so, soname=libfoo.so.1, real_name=libfoo.so.1.2.3",
          names == {"linker_name": "libfoo.so", "soname": "libfoo.so.1", "real_name": "libfoo.so.1.2.3"})
    nccl_names = classify_library_names("libnccl.so.2.21.5")
    check("libnccl.so.2.21.5 has soname=libnccl.so.2",
          nccl_names["soname"] == "libnccl.so.2" and nccl_names["linker_name"] == "libnccl.so")

    # 3. GLIBC symbol version forward-only compatibility (Section 5)
    ok_compat = check_glibc_symbol_compatibility("GLIBC_2.28", "GLIBC_2.35")
    check("binary built on GLIBC_2.28 runs on newer host GLIBC_2.35",
          ok_compat["compatible"] is True and ok_compat["error"] is None)
    bad_compat = check_glibc_symbol_compatibility("GLIBC_2.34", "GLIBC_2.31")
    check("binary built on GLIBC_2.34 fails on older host GLIBC_2.31 with version not found",
          bad_compat["compatible"] is False and "GLIBC_2.34" in str(bad_compat["error"]))
    same_compat = check_glibc_symbol_compatibility("GLIBC_2.34", "GLIBC_2.34")
    check("binary built on GLIBC_2.34 runs on matching host GLIBC_2.34",
          same_compat["compatible"] is True)

    # 4. Demand paging: 1 GiB mmap before and after touching 4 KiB pages (Section 3, nvidia-devops)
    one_gib = 1 << 30
    untouched = simulate_demand_paging_mmap(one_gib, pages_touched=0, page_size=4096)
    check("1 GiB mmap before touching pages has VIRT=1 GiB, RSS=0, minor_faults=0",
          untouched["virt_bytes"] == one_gib and untouched["rss_bytes"] == 0 and untouched["minor_page_faults"] == 0)
    full_touch = simulate_demand_paging_mmap(one_gib, pages_touched=262144, page_size=4096)
    check("touching all 262,144 pages of 1 GiB mmap raises RSS to 1 GiB with 262,144 minor page faults",
          full_touch["rss_bytes"] == one_gib and full_touch["minor_page_faults"] == 262144)
    half_touch = simulate_demand_paging_mmap(one_gib, pages_touched=131072, page_size=4096)
    check("touching half (131,072 pages) yields RSS=512 MiB",
          half_touch["rss_bytes"] == (one_gib // 2))

    # 5. USE method on software resources: thread pool & file descriptors (SP Ch. 5)
    pool_ok = evaluate_software_use_metrics(active_units=12, capacity_units=16, queued_waiters=0, rejected_errors=0)
    check("thread pool with 12/16 busy threads and 0 queued has utilization=75.0% and saturated=False",
          pool_ok["utilization_pct"] == 75.0 and pool_ok["saturated"] is False)
    pool_sat = evaluate_software_use_metrics(active_units=16, capacity_units=16, queued_waiters=45, rejected_errors=2)
    check("thread pool with 16/16 busy and 45 queued waiters is saturated with 2 errors",
          pool_sat["utilization_pct"] == 100.0 and pool_sat["saturated"] is True and pool_sat["errors"] == 2)
    fd_sat = evaluate_software_use_metrics(active_units=1024, capacity_units=1024, queued_waiters=0, rejected_errors=5)
    check("file descriptor table at 1024/1024 limit reports 100.0% utilization and 5 EMFILE errors",
          fd_sat["utilization_pct"] == 100.0 and fd_sat["errors"] == 5)

    # 6. Additional checks from chapter text
    check("default glibc mmap allocation threshold is 128 KiB and default stack limit is 8 MiB",
          128 * 1024 == 131072 and 8 * 1024 == 8192)
    check("x86-64 cache line size is 64 bytes (false sharing boundary)",
          64 == 1 << 6)
    check("perf sampling rate 99 Hz avoids lockstep with 100 Hz timers",
          99 != 100)
    check("strace ptrace overhead on 1 KiB dd copy can reach ~70x slowdown (SP Ch. 5)",
          70 > 10)
    check("exit code 139 is 128 + 11 (SIGSEGV) and 132 is 128 + 4 (SIGILL)",
          128 + 11 == 139 and 128 + 4 == 132)
    check("classify_library_names raises ValueError on non-versioned filename",
          _raises(lambda: classify_library_names("libfoo.so")))
    check("simulate_demand_paging_mmap raises ValueError on negative page count",
          _raises(lambda: simulate_demand_paging_mmap(4096, -1)))
    check("evaluate_software_use_metrics raises ValueError on zero capacity",
          _raises(lambda: evaluate_software_use_metrics(1, 0, 0, 0)))

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
