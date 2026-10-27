"""Chapter 1.7 model: Package manager two-layer resolution (dpkg/rpm vs apt/dnf),
config-file upgrade resolution (.rpmnew, .rpmsave, .dpkg-old), dynamic linker ld.so
search order (RPATH vs LD_LIBRARY_PATH vsRUNPATH vs ld.so.cache), Makefile
timestamp-driven rebuild DAG, and 10-step mini-cluster installation order.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 15
  ("Development Tools": cc/gcc, static vs shared libraries, ld.so search order,
  rpath, LD_LIBRARY_PATH, headers/cpp, make DAG, Lex/Yacc, scripting languages,
  Java JRE/JDK) and Chapter 16 ("Introduction to Compiling Software from C Source
  Code": tar inspection, GNU autoconf ./configure --prefix, config.log, pkg-config,
  checkinstall/rpmbuild/DESTDIR, patch -p0/-p1).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7 (packages,
  dependencies, checksums, config files, repositories, yum/dnf and rpm) and
  Chapter 24 ("Node Setup and Software Installation": OFED, 10-step mini-cluster
  build order, NFS /etc/exports and /etc/fstab, kickstart, cloning pitfalls,
  NFS-root).
"""
from typing import Dict, List, Optional, Set, Tuple


MINI_CLUSTER_BUILD_STEPS: List[str] = [
    "1_control_server",
    "2_network_filesystem",
    "3_first_compute_node",
    "4_communication_software_ofed",
    "5_second_compute_node_mini_cluster",
    "6_compilers_and_test_packages",
    "7_test_communication_hardware",
    "8_job_scheduler_slurm",
    "9_test_job_completion_end_to_end",
    "10_clone_and_scale_remaining_nodes",
]


def resolve_rpm_config_upgrade(
    user_modified: bool,
    packager_modified: bool,
    noreplace: bool = True,
) -> Dict[str, Optional[str]]:
    """Model how RPM handles a %config(noreplace) or %config file during an upgrade."""
    if not user_modified:
        return {"installed_file": "new_package_version", "sidecar_file": None}
    if not packager_modified:
        return {"installed_file": "user_edited_version", "sidecar_file": None}
    if noreplace:
        return {"installed_file": "user_edited_version", "sidecar_file": ".rpmnew"}
    return {"installed_file": "new_package_version", "sidecar_file": ".rpmsave"}


def resolve_shared_library_path(
    lib_name: str,
    rpath_dirs: List[str],
    runpath_dirs: List[str],
    ld_library_path_dirs: List[str],
    ld_so_cache_dirs: List[str],
    default_dirs: List[str],
    files_on_disk: Dict[str, Set[str]],
) -> str:
    """Resolve a shared library following ELF DT_RPATH -> LD_LIBRARY_PATH -> DT_RUNPATH -> ld.so.cache -> default (/lib, /usr/lib)."""
    search_sequence: List[Tuple[str, List[str]]] = []
    if rpath_dirs and not runpath_dirs:
        search_sequence.append(("DT_RPATH", rpath_dirs))
    if ld_library_path_dirs:
        search_sequence.append(("LD_LIBRARY_PATH", ld_library_path_dirs))
    if runpath_dirs:
        search_sequence.append(("DT_RUNPATH", runpath_dirs))
    search_sequence.append(("ld.so.cache", ld_so_cache_dirs))
    search_sequence.append(("default_dirs", default_dirs))

    for source_tag, dirs in search_sequence:
        for d in dirs:
            if lib_name in files_on_disk.get(d, set()):
                return f"{source_tag}:{d}/{lib_name}"
    return "NOT_FOUND"


def evaluate_make_rebuild_targets(
    mtimes: Dict[str, int],
    rules: List[Tuple[str, List[str]]],
) -> List[str]:
    """Simulate make timestamp dependency graph in bottom-up rule order."""
    sim_times = dict(mtimes)
    rebuilt: List[str] = []
    current_clock = max(sim_times.values(), default=0) + 1
    for target, deps in rules:
        target_time = sim_times.get(target, -1)
        needs_build = target_time < 0 or any(sim_times.get(dep, 0) > target_time for dep in deps)
        if needs_build:
            rebuilt.append(target)
            sim_times[target] = current_clock
            current_clock += 1
    return rebuilt


def strip_patch_path(patch_header_path: str, strip_level: int) -> str:
    """Model 'patch -pN' stripping N leading slash-separated components from a diff path."""
    if strip_level < 0:
        raise ValueError("strip_level must be >= 0")
    parts = patch_header_path.split("/")
    if strip_level >= len(parts):
        raise ValueError("strip_level exceeds path depth")
    return "/".join(parts[strip_level:])


def check_prototype_ready_for_cloning(
    uses_uuid_or_portable_fstab: bool,
    removed_persistent_mac_rules: bool,
    cleared_ssh_host_keys_and_machine_id: bool,
) -> Dict[str, object]:
    """Verify the 3 prototype preparation steps before disk cloning (SCL Ch. 24)."""
    missing: List[str] = []
    if not uses_uuid_or_portable_fstab:
        missing.append("replace_disk_by_id_in_grub_and_fstab")
    if not removed_persistent_mac_rules:
        missing.append("remove_mac_bound_udev_net_rules")
    if not cleared_ssh_host_keys_and_machine_id:
        missing.append("clear_ssh_host_keys_and_machine_id")
    return {"ready": len(missing) == 0, "missing_steps": missing}
