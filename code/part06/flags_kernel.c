// Dot product + saxpy-style loop for comparing optimisation flags.
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static double wall(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + 1e-9 * t.tv_nsec; }

int main(void) {
    const long n = 20L * 1000 * 1000;
    float *x = malloc(n * sizeof(float)), *y = malloc(n * sizeof(float));
    for (long i = 0; i < n; i++) { x[i] = 1.0f / (1 + i % 13); y[i] = 0.5f; }
    double t0 = wall();
    float dot = 0.0f;
    for (int rep = 0; rep < 20; rep++) {
        dot = 0.0f;
        for (long i = 0; i < n; i++) dot += x[i] * y[i];
        y[rep] = dot * 1e-12f;  // makes each repetition depend on the previous one so the compiler cannot hoist the loop
    }
    double t = wall() - t0;
    printf("dot=%.6f  time=%.3f s  (%.2f GFLOP/s)\n", dot, t, 2.0 * n * 20 / t / 1e9);
    free(x); free(y);
    return 0;
}
