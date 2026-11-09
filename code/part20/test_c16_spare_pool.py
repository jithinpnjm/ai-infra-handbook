# code/part20/test_c16_spare_pool.py
import math
from c16_spare_pool import (effective_capacity, expected_in_repair,
                            poisson_cdf, spares_needed, x_plus_k)


def test_expected_in_repair():
    assert math.isclose(expected_in_repair(512, 0.10, 72), 512 * 0.1 / 8760 * 72)


def test_poisson_cdf_sums_to_one():
    assert math.isclose(poisson_cdf(60, 3.0), 1.0, rel_tol=1e-9)
    assert math.isclose(poisson_cdf(0, 2.0), math.exp(-2.0))


def test_spares_grow_with_repair_time():
    a = spares_needed(512, 0.10, 24)
    b = spares_needed(512, 0.10, 72)
    c = spares_needed(512, 0.10, 336)
    assert a <= b < c


def test_spares_cover_target():
    s = spares_needed(512, 0.10, 336, 0.999)
    mean = expected_in_repair(512, 0.10, 336)
    assert poisson_cdf(s, mean) >= 0.999 > poisson_cdf(s - 1, mean)


def test_x_plus_k():
    assert x_plus_k(30, 2, 3) == 63


def test_stuck_nodes_reduce_capacity():
    assert effective_capacity(100, 3, 2, 1) == 94
