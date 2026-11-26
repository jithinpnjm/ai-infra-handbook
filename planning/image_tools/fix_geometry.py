# Let's write an updated geometry check with adjusted sizes
# Box 1: x = 76, width = 264 (x = 76 to 340).
# Arrow 1: x1 = 340, x2 = 388 (length = 48).
# Box 2: x = 388, width = 540 (x = 388 to 928).
# Arrow 2: x1 = 928, x2 = 976 (length = 48).
# Box 3: x = 976, width = 548 (x = 976 to 1524).

# Banner: y = 610 to 684 (height = 74). Line 1 y = 650, Line 2 y = 678.
# (ty=650 - fsize=24 - by1=610 = 16 px top pad! by2=684 - ty2=678 = 6 px bottom pad, or height = 80: y = 608 to 688 -> top pad 18 px, bottom pad 10 px!)

# Let's test this in check_geometry:
lines_to_check = [
    # 1. bytes arrive
    ("bytes_arrive", 76, 340, 140, 276, 208, 248, "bytes arrive", "sans", 30, "center"),
    # 2. decode
    ("decode_l1", 388, 928, 140, 276, 460, 180, "decode into a UTF-8 string,", "sans", 24, "left"),
    ("decode_l2", 388, 928, 140, 276, 406, 222, "for example {\"vendors\":[", "mono", 24, "left"),
    ("decode_l3", 388, 928, 140, 276, 406, 252, "\"Cisco\",\"Juniper\",\"Arista\"]}", "mono", 24, "left"),
    # 3. deserialize
    ("deser_l1", 976, 1524, 140, 276, 1058, 180, "deserialize with json.loads()", "mono", 24, "left"),
    ("deser_l2", 976, 1524, 140, 276, 994, 222, "into native structures:", "sans", 24, "left"),
    ("deser_l3", 976, 1524, 140, 276, 994, 252, "a Python dict and list", "sans", 24, "left"),
    # 4. serialize first
    ("serialize", 976, 1524, 304, 438, 1080, 382, "serialize first", "sans", 30, "left"),
    # 5. encode
    ("encode", 388, 928, 304, 438, 640, 382, "encode", "sans", 30, "left"),
    # 6. strip
    ("strip_l1", 50, 1550, 482, 584, 140, 524, "screen scraping show interfaces em0 breaks when a vendor changes the spacing;", "mono", 24, "left"),
    ("strip_l2", 50, 1550, 482, 584, 140, 558, "ask for structured output: show interfaces em0 | display xml, or JSON", "mono", 24, "left"),
    # 7. comparison banner (y: 606 to 686, height=80)
    ("banner_l1", 68, 1532, 606, 686, 90, 646, "Markup languages like HTML annotate documents for rendering;", "sans", 24, "left"),
    ("banner_l2", 68, 1532, 606, 686, 90, 676, "data serialization formats represent typed data structures across languages", "sans", 24, "left"),
    # 8. XML (y: 698 to 782, height=84)
    ("xml_l1", 68, 1532, 698, 782, 150, 734, "XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model", "mono", 24, "left"),
    ("xml_l2", 68, 1532, 698, 782, 150, 766, "or //device[@name=\"leaf\"]/model, or XQuery; validate with XSD (xmlschema)", "mono", 24, "left"),
    # 9. JSON (y: 792 to 904, height=112)
    ("json_l1", 68, 1532, 792, 904, 150, 826, "JSON: lighter; validate with JSON Schema:", "mono", 24, "left"),
    ("json_l2", 68, 1532, 792, 904, 150, 856, "$schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength,", "mono", 24, "left"),
    ("json_l3", 68, 1532, 792, 904, 150, 886, "minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()", "mono", 24, "left"),
    # 10. Protobuf (y: 914 to 1026, height=112)
    ("pb_l1", 68, 1532, 914, 1026, 150, 948, "Protocol Buffers: binary, .proto files compiled with protoc,", "mono", 24, "left"),
    ("pb_l2", 68, 1532, 914, 1026, 150, 978, "validated with protoc-gen-validate; FlatBuffers: read fields straight", "mono", 24, "left"),
    ("pb_l3", 68, 1532, 914, 1026, 150, 1008, "from the byte buffer; for high-throughput RPCs such as gRPC telemetry", "mono", 24, "left"),
    # 11. pickle (y: 1034 to 1094, height=60)
    ("pickle", 68, 1532, 1034, 1094, 150, 1072, "pickle: Python only, unsafe on untrusted bytes", "mono", 24, "left"),
    # 12. Takeaway bar (y: 1114 to 1180, height=66)
    ("takeaway", 50, 1550, 1114, 1180, 800, 1157, "Structured data beats fragile screen scraping", "sans", 30, "center")
]

all_ok = True
for name, bx1, bx2, by1, by2, tx, ty, text, ftype, fsize, align in lines_to_check:
    char_w = 0.62 * fsize if ftype == "mono" else 0.6 * fsize
    text_w = len(text) * char_w
    if align == "center":
        x_left = tx - text_w / 2
        x_right = tx + text_w / 2
    else:
        x_left = tx
        x_right = tx + text_w
    
    pad_left = x_left - bx1
    pad_right = bx2 - x_right
    pad_top = ty - fsize - by1
    pad_bottom = by2 - ty
    
    min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
    
    status = "OK"
    if min_pad < 8:
        status = "FAIL"
        all_ok = False
    
    print(f"{name:15s} | pad_L: {pad_left:5.1f} | pad_R: {pad_right:5.1f} | pad_T: {pad_top:4.1f} | pad_B: {pad_bottom:4.1f} | {status}")

print("\nOverall geometry check:", "PASSED" if all_ok else "FAILED")
