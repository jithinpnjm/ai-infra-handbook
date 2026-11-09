import net06_ss_parser as m

# First two lines are from Systems Performance 2nd ed, ch 10 (ss output).
# The rest are synthetic, built to show a full accept queue and TIME-WAIT.
FIXTURE = """State Recv-Q Send-Q Local Address:Port Peer Address:Port
ESTAB 0 0 100.85.142.69:65264 100.82.166.11:6001
ESTAB 0 0 100.85.142.69:6028 100.82.16.200:6101
LISTEN 129 128 0.0.0.0:8000 0.0.0.0:*
LISTEN 0 4096 0.0.0.0:9000 0.0.0.0:*
TIME-WAIT 0 0 10.0.0.5:40001 10.0.0.9:443
TIME-WAIT 0 0 10.0.0.5:40002 10.0.0.9:443
CLOSE-WAIT 5 0 10.0.0.5:8000 10.0.1.7:51000
"""

def test_counts():
    s = m.summarize(m.parse(FIXTURE))
    assert s["counts"]["ESTABLISHED"] == 2
    assert s["counts"]["TIME-WAIT"] == 2
    assert s["counts"]["CLOSE-WAIT"] == 1

def test_full_listener_found_and_healthy_one_ignored():
    s = m.summarize(m.parse(FIXTURE))
    assert s["full_listeners"] == ["0.0.0.0:8000"]

def test_header_and_junk_skipped():
    assert len(m.parse(FIXTURE)) == 7
    assert m.parse("garbage line\n\n") == []

def test_port_budget():
    # Systems Performance: 65,536 ports and a 60 s TIME_WAIT
    assert round(m.max_new_conn_rate(0, 65535, 60)) == 1092
    # Netflix tuning in the same book: ip_local_port_range 10240 65535
    assert round(m.max_new_conn_rate(10240, 65535, 60)) == 922
