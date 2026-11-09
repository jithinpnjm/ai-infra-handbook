import net06_tcpdump_reader as m

# Lines 1-2 follow the tcpdump output printed in Systems Performance 2nd ed ch 10.
# Lines 3-6 are synthetic: a repeated segment and an unanswered SYN.
FIXTURE = """01:20:46.769073 IP 10.2.203.2.22 > 10.2.0.2.33771: Flags [P.], seq 4235343542:4235343734, ack 4053030377, win 132, length 192
01:20:46.769470 IP 10.2.0.2.33771 > 10.2.203.2.22: Flags [.], ack 4235343734, win 501, length 0
01:20:47.100000 IP 10.2.203.2.22 > 10.2.0.2.33771: Flags [P.], seq 4235343542:4235343734, ack 4053030377, win 132, length 192
01:21:00.000000 IP 10.1.1.1.50000 > 10.9.9.9.443: Flags [S], seq 100, win 64240, length 0
01:21:01.000000 IP 10.1.1.1.50000 > 10.9.9.9.443: Flags [S], seq 100, win 64240, length 0
01:21:02.000000 IP 10.1.1.2.50001 > 10.9.9.9.443: Flags [S], seq 200, win 64240, length 0
01:21:02.001000 IP 10.9.9.9.443 > 10.1.1.2.50001: Flags [S.], seq 900, ack 201, win 65535, length 0
"""

def test_parse_count():
    assert len(m.parse(FIXTURE)) == 7

def test_retransmit_found():
    r = m.retransmits(m.parse(FIXTURE))
    assert r == [("10.2.203.2.22", "10.2.0.2.33771", 4235343542, 192)]

def test_unanswered_syn():
    u = m.unanswered_syns(m.parse(FIXTURE))
    assert u == [("10.1.1.1.50000", "10.9.9.9.443")] * 2
