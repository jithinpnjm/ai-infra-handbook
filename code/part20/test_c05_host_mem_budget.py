import pytest
from c05_host_mem_budget import weights_gib, budget, explain


def test_weights_arithmetic():
    # 8 billion parameters at 2 bytes each is 16e9 bytes.
    assert weights_gib(8e9, 2) == pytest.approx(14.9, abs=0.05)
    assert weights_gib(70e9, 2) == pytest.approx(130.4, abs=0.05)


def test_pinned_memory_kills_even_when_cache_is_reclaimable():
    # Hypothetical pod: limit 24 GiB, 4 workers, 4 GiB pinned + 3 GiB anon each.
    result = budget(24, 4, 4, 3, 15)
    assert result["unreclaimable_gib"] == 28
    assert result["fits"] is False
    assert explain(result).startswith("OOM kill expected")


def test_fits_with_cache_pressure():
    result = budget(40, 4, 4, 3, 15)
    assert result["fits"] and result["cache_pressure"]
    assert result["headroom_gib"] == 12
    assert "page cache will be reclaimed" in explain(result)


def test_fits_cleanly():
    assert explain(budget(64, 4, 4, 3, 15)) == "fits with 36.0 GiB headroom"
