import re

def test_wrap():
    text_dec = 'decode into a UTF-8 string, for example {"vendors":["Cisco","Juniper","Arista"]}'
    # split test
    p1 = 'decode into a UTF-8 string, '
    p2 = 'for example '
    p3 = '{"vendors":["Cisco",'
    p4 = '"Juniper","Arista"]}'
    joined = p1 + p2 + p3 + p4
    assert joined == text_dec, f"Mismatch: '{joined}' vs '{text_dec}'"
    print("Box 2 wrap matches perfectly!")

    text_des = 'deserialize with json.loads() into native structures: a Python dict and list'
    d1 = 'deserialize with json.loads() '
    d2 = 'into native structures: '
    d3 = 'a Python dict and list'
    joined_des = d1 + d2 + d3
    assert joined_des == text_des, f"Mismatch: '{joined_des}' vs '{text_des}'"
    print("Box 3 wrap matches perfectly!")

test_wrap()
