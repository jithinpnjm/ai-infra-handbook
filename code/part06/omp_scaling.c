// Thread scaling of a memory-bound (triad) and compute-bound (sin) loop, plus a reduction.
#include <math.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>

static double now(void) { return omp_get_wtime(); }

int main(void) {
    const long n = 50L * 1000 * 1000;
    double *a = malloc(n * sizeof(double)), *b = malloc(n * sizeof(double)), *c = malloc(n * sizeof(double));
    // first-touch initialisation in parallel (NUMA-friendly placement on multi-socket machines)
    #pragma omp parallel for schedule(static)
    for (long i = 0; i < n; i++) { a[i] = 0.0; b[i] = 1.0 + i % 7; c[i] = 2.0; }

    // warm-up pass so page faults and frequency ramp-up are not charged to the 1-thread row
    #pragma omp parallel for schedule(static)
    for (long i = 0; i < n; i++) a[i] = b[i] + 3.0 * c[i];

    printf("threads  triad_ms  GB/s   sin_ms   sum_ms\n");
    int maxt = omp_get_max_threads();
    for (int t = 1; t <= maxt; t = (t < 4 ? t * 2 : t + 2)) {
        omp_set_num_threads(t);
        double t0 = now();
        #pragma omp parallel for schedule(static)
        for (long i = 0; i < n; i++) a[i] = b[i] + 3.0 * c[i];
        double triad = now() - t0;

        t0 = now();
        #pragma omp parallel for schedule(static)
        for (long i = 0; i < n / 10; i++) a[i] = sin(b[i]) * cos(c[i]);
        double sinw = now() - t0;

        t0 = now();
        double s = 0.0;
        #pragma omp parallel for reduction(+ : s) schedule(static)
        for (long i = 0; i < n; i++) s += a[i];
        double sum = now() - t0;

        printf("%7d  %8.1f  %5.1f  %7.1f  %7.1f  (checksum %.3e)\n", t, triad * 1e3,
               3.0 * n * sizeof(double) / triad / 1e9, sinw * 1e3, sum * 1e3, s);
    }
    free(a); free(b); free(c);
    return 0;
}
