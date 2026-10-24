"""Allreduce correctness plus timing vs message size and rank count."""
import numpy as np
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank, size = comm.Get_rank(), comm.Get_size()
x = np.full(1, rank + 1, dtype=np.float64)
total = np.empty_like(x)
comm.Allreduce(x, total, op=MPI.SUM)
assert total[0] == size * (size + 1) / 2
if rank == 0:
    print(f"ranks={size} sum check ok: {total[0]:.0f}")
    print(f"{'floats':>10} {'ms':>9}")
for n in (1, 1_000, 1_000_000, 8_000_000):
    a = np.ones(n, dtype=np.float32); b = np.empty_like(a)
    comm.Barrier(); t = MPI.Wtime()
    for _ in range(20):
        comm.Allreduce(a, b, op=MPI.SUM)
    dt = (MPI.Wtime() - t) / 20
    if rank == 0:
        print(f"{n:>10} {dt*1e3:>9.3f}")
