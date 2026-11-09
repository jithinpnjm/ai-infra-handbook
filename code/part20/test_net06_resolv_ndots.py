import net06_resolv_ndots as m

# Example pod resolv.conf from kubernetes.io "DNS for Services and Pods"
CONF = """nameserver 10.32.0.10
search ml.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
"""

def test_parse():
    s, n = m.parse_conf(CONF)
    assert n == 5 and s[0] == "ml.svc.cluster.local" and len(s) == 3

def test_external_name_searches_first():
    s, n = m.parse_conf(CONF)
    c = m.candidates("api.example.com", s, n)
    assert c[-1] == "api.example.com" and len(c) == 4

def test_trailing_dot_skips_search():
    s, n = m.parse_conf(CONF)
    assert m.candidates("api.example.com.", s, n) == ["api.example.com."]

def test_ndots_2_goes_direct():
    s, n = m.parse_conf(CONF.replace("ndots:5", "ndots:2"))
    assert m.candidates("api.example.com", s, n)[0] == "api.example.com"

def test_query_cost():
    # external name that only resolves as written: 3 search misses + 1 hit
    assert m.queries_until_hit("api.example.com", CONF, {"api.example.com"}) == 8
    assert m.queries_until_hit("api.example.com.", CONF, {"api.example.com."}) == 2
