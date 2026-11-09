import net06_mtu_math as m

def test_ping_default_size_matches_book():
    # How Linux Works ch 9: 56-byte payload is 84 bytes with headers
    assert 56 + m.ICMP + m.IP == 84

def test_mss_and_ping():
    assert m.tcp_mss(1500) == 1460
    assert m.ping_payload_for(1500) == 1472
    assert m.ping_payload_for(1450) == 1422

def test_vxlan_inner_mtu():
    assert m.inner_mtu(1500, 50) == 1450
    assert m.inner_mtu(9216, 50) == 9166

def test_blackhole():
    assert m.blackhole_risk(1450, 1500, False) == "BLACK HOLE"
    assert m.blackhole_risk(1450, 1500, True) == "shrinks via PMTUD"
    assert m.blackhole_risk(1500, 1450, False) == "fits"
