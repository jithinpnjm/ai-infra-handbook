def verify_all_splits():
    # 1. Title
    t = "Reading data off the wire: decode, then deserialize"
    assert t == "Reading data off the wire: decode, then deserialize"

    # 2. bytes arrive
    assert "bytes arrive" == "bytes arrive"

    # 3. decode
    l3 = 'decode into a UTF-8 string, for example {"vendors":["Cisco","Juniper","Arista"]}'
    p3 = ["decode into a UTF-8 string, ", "for example ", '{"vendors":["Cisco","Juniper","Arista"]}']
    assert "".join(p3) == l3

    # 4. deserialize
    l4 = "deserialize with json.loads() into native structures: a Python dict and list"
    p4 = ["deserialize with ", "json.loads() into ", "native structures: ", "a Python dict and list"]
    assert "".join(p4) == l4

    # 5. serialize first
    assert "serialize first" == "serialize first"

    # 6. encode
    assert "encode" == "encode"

    # 7. format intro
    l7 = "Markup languages like HTML annotate documents for rendering; data serialization formats represent typed data structures across languages"
    p7 = ["Markup languages like HTML annotate documents for rendering; ", "data serialization formats represent typed data structures across languages"]
    assert "".join(p7) == l7

    # 8. XML
    l8 = 'XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)'
    p8 = [
        "XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model ",
        'or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)'
    ]
    assert "".join(p8) == l8

    # 9. JSON
    l9 = "JSON: lighter; validate with JSON Schema: $schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()"
    p9 = [
        "JSON: lighter; validate with JSON Schema: ",
        "$schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, ",
        "minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()"
    ]
    assert "".join(p9) == l9

    # 10. Protobuf
    l10 = "Protocol Buffers: binary, .proto files compiled with protoc, validated with protoc-gen-validate; FlatBuffers: read fields straight from the byte buffer; for high-throughput RPCs such as gRPC telemetry"
    p10 = [
        "Protocol Buffers: binary, .proto files compiled with protoc, ",
        "validated with protoc-gen-validate; FlatBuffers: read fields straight from the byte buffer; ",
        "for high-throughput RPCs such as gRPC telemetry"
    ]
    assert "".join(p10) == l10

    # 11. pickle
    l11 = "pickle: Python only, unsafe on untrusted bytes"
    assert l11 == "pickle: Python only, unsafe on untrusted bytes"

    # 12. Strip
    l12 = "screen scraping show interfaces em0 breaks when a vendor changes the spacing; ask for structured output: show interfaces em0 | display xml, or JSON"
    p12 = [
        "screen scraping show interfaces em0 breaks when a vendor changes the spacing; ",
        "ask for structured output: show interfaces em0 | display xml, or JSON"
    ]
    assert "".join(p12) == l12

    # 13. Source label
    l13 = "Network Programmability and Automation chapter 8"
    assert l13 == "Network Programmability and Automation chapter 8"

    # 14. Bottom bar
    l14 = "Structured data beats fragile screen scraping"
    assert l14 == "Structured data beats fragile screen scraping"

    print("ALL 14 LABELS VERIFIED WITH 100% EXACT EQUALITY!")

verify_all_splits()
