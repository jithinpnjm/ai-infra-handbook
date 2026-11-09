import pytest
import net06_conntrack_check as m

def test_ok():
    t = "net.netfilter.nf_conntrack_count = 1000\nnet.netfilter.nf_conntrack_max = 262144"
    assert m.verdict(m.usage(t)) == "ok"

def test_hot_and_full():
    hot = "nf_conntrack_count = 210000\nnf_conntrack_max = 262144"
    assert m.verdict(m.usage(hot)).startswith("HOT")
    full = "nf_conntrack_count = 262144\nnf_conntrack_max = 262144"
    assert m.verdict(m.usage(full)).startswith("FULL")

def test_missing_value_raises():
    with pytest.raises(ValueError):
        m.usage("nf_conntrack_count = 5")
