"""Chapter 1.11 model: ELF startup sequence (execve -> PT_INTERP ld.so -> _start ->
main), shared-library SONAME and GLIBC symbol-version forward compatibility,
demand-paging VIRT vs RSS and minor page faults, and USE method software resource
metrics (thread pools and file descriptors).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 8
  (strace and ltrace) and Chapter 15 (dynamic linker ld.so, ldd, RPATH vs RUNPATH,
  shared libraries).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 5 ("Applications": CPU profiling, off-CPU analysis, syscall analysis,
  USE method for software resources, thread-state analysis, 70x strace dd overhead).
- nvidia-devops/volume-01/01-linux-compute-memory-masterclass.md (1 GiB mmap
  demand-paging 262,144 minor page faults, Python arena retention).
"""
from typing import Dict, List, Tuple


ELF_STARTUP_STAGES: List[str] = [
    "1_fork_and_execve",
    "2_kernel_format_check_elf_or_shebang",
    "3_map_load_segments_and_stack_auxv",
    "4_map_pt_interp_dynamic_linker",
    "5_ld_so_maps_dt_needed_and_relocates",
    "6_start_and_libc_start_main_to_main",
    "7_exit_group_and_parent_wait4",
]


def parse_version_tuple(ver_str: str) -> Tuple[int, ...]:
    """Parse 'GLIBC_2.34' or '3.4.30' into an integer tuple (2, 34) or (3, 4, 30)."""
    numeric = ver_str.split("_")[-1]
    return tuple(int(p) for p in numeric.split("."))


def check_glibc_symbol_compatibility(binary_required_ver: str, host_glibc_ver: str) -> Dict[str, object]:
    """Check whether host glibc satisfies a binary's required GLIBC_x.y symbol version."""
    req = parse_version_tuple(binary_required_ver)
    host = parse_version_tuple(host_glibc_ver)
    ok = host >= req
    return {
        "compatible": ok,
        "required": binary_required_ver,
        "host": host_glibc_ver,
        "error": None if ok else f"version `{binary_required_ver}' not found",
    }


def classify_library_names(real_filename: str) -> Dict[str, str]:
    """Derive linker_name (libfoo.so), soname (libfoo.so.MAJOR), and real_name from 'libfoo.so.1.2.3'."""
    if ".so." not in real_filename:
        raise ValueError(f"Expected versioned shared library name, got: {real_filename}")
    prefix, ver = real_filename.split(".so.", 1)
    major = ver.split(".")[0]
    return {
        "linker_name": f"{prefix}.so",
        "soname": f"{prefix}.so.{major}",
        "real_name": real_filename,
    }


def simulate_demand_paging_mmap(
    reserved_bytes: int,
    pages_touched: int,
    page_size: int = 4096,
) -> Dict[str, int]:
    """Compute VIRT, RSS, and minor page faults after mmap() and touching pages_touched pages."""
    if reserved_bytes < 0 or pages_touched < 0 or page_size <= 0:
        raise ValueError("Invalid paging parameters")
    max_pages = reserved_bytes // page_size
    actual_pages = min(pages_touched, max_pages)
    return {
        "virt_bytes": reserved_bytes,
        "rss_bytes": actual_pages * page_size,
        "minor_page_faults": actual_pages,
    }


def evaluate_software_use_metrics(
    active_units: int,
    capacity_units: int,
    queued_waiters: int,
    rejected_errors: int,
) -> Dict[str, object]:
    """Compute USE (Utilization, Saturation, Errors) metrics for a thread pool or file-descriptor table."""
    if capacity_units <= 0:
        raise ValueError("capacity_units must be positive")
    return {
        "utilization_pct": round(100.0 * active_units / capacity_units, 1),
        "saturation_queue": queued_waiters,
        "errors": rejected_errors,
        "saturated": queued_waiters > 0 or active_units >= capacity_units,
    }
