"""Latency/bandwidth between rank 0 and rank 1: fits T(m) = alpha + m/beta."""
import numpy as np
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
assert comm.Get_size() >= 2, "run with at least 2 ranks"
reps = 200
results = []
for exp in range(0, 25, 2):
    m = 1 << exp
    buf = np.zeros(m, dtype=np.uint8)
    comm.Barrier()
    t = MPI.Wtime()
    for _ in range(reps):
        if rank == 0:
            comm.Send(buf, dest=1, tag=1); comm.Recv(buf, source=1, tag=2)
        elif rank == 1:
            comm.Recv(buf, source=0, tag=1); comm.Send(buf, dest=0, tag=2)
    one_way = (MPI.Wtime() - t) / reps / 2
    results.append((m, one_way))
if rank == 0:
    print(f"{'bytes':>10} {'one-way us':>12} {'MB/s':>10}")
    for m, s in results:
        print(f"{m:>10} {s*1e6:>12.2f} {m/s/1e6:>10.1f}")
