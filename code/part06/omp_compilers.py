#!/usr/bin/env python3
"""OpenMP triad bandwidth, floating-point reassociation error, and FlexLM quorum/lease models for Chapter 6.5."""


def triad_bandwidth_gbps(num_elements: int, bytes_per_element: int, elapsed_ms: float) -> float:
    """Return STREAM triad (a[i] = b[i] + s * c[i], 3 arrays = 2 reads + 1 write) bandwidth in GB/s."""
    total_bytes = 3.0 * num_elements * bytes_per_element
    elapsed_sec = elapsed_ms / 1000.0
    return round(total_bytes / elapsed_sec / 1e9, 1)


def fp_relative_error_pct(measured_sum: float, fp64_reference: float) -> float:
    """Return percentage relative error |measured - ref| / ref * 100."""
    return round(abs(measured_sum - fp64_reference) / fp64_reference * 100.0, 2)


def check_hybrid_oversubscription(
    mpi_ranks_per_node: int, omp_threads_per_rank: int, physical_cores_per_node: int
) -> dict[str, int | bool]:
    """Check whether a hybrid MPI + OpenMP node configuration oversubscribes physical cores."""
    total_threads = mpi_ranks_per_node * omp_threads_per_rank
    return {
        "total_threads": total_threads,
        "physical_cores": physical_cores_per_node,
        "oversubscribed": total_threads > physical_cores_per_node,
        "oversubscription_ratio": round(total_threads / physical_cores_per_node, 2),
    }


def flexlm_quorum_and_seat_availability(
    total_servers: int, online_servers: int, total_seats: int, recent_calls_within_15m: int
) -> dict[str, int | bool]:
    """Model SCL Chapter 21 FlexLM >=50% server quorum and 15-minute floating seat hold."""
    has_quorum = online_servers >= (total_servers / 2.0)
    free_seats = max(0, total_seats - recent_calls_within_15m) if has_quorum else 0
    return {
        "has_quorum": has_quorum,
        "free_seats": free_seats,
        "lease_hold_minutes": 15,
    }


if __name__ == "__main__":
    # Reference omp_scaling.c (n = 50,000,000 doubles):
    # 1t: 18.1 ms (66.3 GB/s), 2t: 15.3 ms (78.4 GB/s), 4t: 14.2 ms (84.4 GB/s),
    # 6t: 14.1 ms (85.0 GB/s), 8t: 14.1 ms (85.4 GB/s), checksum 4.498e+08; sin 86.3->13.3->11.3->7.8->7.3 ms (26 ms warm); sum 37.7->18.9->12.9->8.9->9.4 ms (no warm-up: 20 GB/s).
    # Reference omp_race.c (n = 20,000,000): racy 6215980 & 3487814 vs 20000000 (17,500,000 at -O2; 0.09 s packed/padded).
    # Reference flags_kernel.c (n = 20,000,000, 20 reps, FP64 ref 2446257.2):
    # -O0/-O1/-O2/-O3: dot=2293365.000000 (2.02, 2.01, 2.69, 2.71, 2.68 GFLOP/s, 6.25% error);
    # -O3 -ffast-math: dot=2445485.500000 (16.05, 16.29 GFLOP/s, 0.03% error); gfortran harmonic(1e6)=14.392726722865611.
    print("1-thread triad GB/s:", triad_bandwidth_gbps(50_000_000, 8, 18.1))
    print("8-thread triad GB/s:", triad_bandwidth_gbps(50_000_000, 8, 14.1))
    print("Strict FP32 error %:", fp_relative_error_pct(2293365.0, 2446257.2))
    print("Fast-math FP32 error %:", fp_relative_error_pct(2445485.5, 2446257.2))
