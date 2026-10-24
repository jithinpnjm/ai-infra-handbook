// Data race versus atomic versus reduction, and false sharing.
#include <omp.h>
#include <stdio.h>

#define PAD 16  // 16 doubles = 128 bytes: one cache line on Apple M-series (64 B on most x86 and Arm servers)

int main(void) {
    const long n = 20L * 1000 * 1000;
    volatile long racy = 0;  // volatile forces real loads/stores so the race is not optimised away
    long atomic_count = 0, reduced = 0;
    #pragma omp parallel for
    for (long i = 0; i < n; i++) racy++;                 // data race: lost updates
    #pragma omp parallel for
    for (long i = 0; i < n; i++) {
        #pragma omp atomic
        atomic_count++;                                   // correct but serialises
    }
    #pragma omp parallel for reduction(+ : reduced)
    for (long i = 0; i < n; i++) reduced++;               // correct and fast
    printf("expected %ld | racy %ld | atomic %ld | reduction %ld\n", n, racy, atomic_count, reduced);

    int T = omp_get_max_threads();
    volatile double packed[64] = {0}, padded[64 * PAD] = {0};  // volatile: keep updates in memory
    double t0 = omp_get_wtime();
    #pragma omp parallel num_threads(T)
    {
        int id = omp_get_thread_num();
        for (long i = 0; i < 200000000L / T; i++) packed[id] += 1.0;
    }
    double t_packed = omp_get_wtime() - t0;
    t0 = omp_get_wtime();
    #pragma omp parallel num_threads(T)
    {
        int id = omp_get_thread_num();
        for (long i = 0; i < 200000000L / T; i++) padded[id * PAD] += 1.0;
    }
    double t_padded = omp_get_wtime() - t0;
    printf("false sharing (%d threads): packed %.3f s, padded %.3f s\n", T, t_packed, t_padded);
    return 0;
}
