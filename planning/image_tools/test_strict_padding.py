lines_to_check = [
    # (name, bx1, bx2, by1, by2, tx, ty, text, ftype, fsize, align)
    ("bytes_arrive", 76, 340, 140, 276, 208, 246, "bytes arrive", "sans", 30, "center"),
    ("decode_l1", 388, 928, 140, 276, 460, 180, "decode into a UTF-8 string,", "sans", 24, "left"),
    ("decode_l2", 388, 928, 140, 276, 406, 222, "for example {\"vendors\":[", "mono", 24, "left"),
    ("decode_l3", 388, 928, 140, 276, 406, 252, "\"Cisco\",\"Juniper\",\"Arista\"]}", "mono", 24, "left"),
    ("deser_l1", 976, 1524, 140, 276, 1058, 180, "deserialize with json.loads()", "mono", 24, "left"),
    ("deser_l2", 976, 1524, 140, 276, 994, 222, "into native structures:", "sans", 24, "left"),
    ("deser_l3", 976, 1524, 140, 276, 994, 252, "a Python dict and list", "sans", 24, "left"),
    ("serialize", 976, 1524, 304, 438, 1080, 382, "serialize first", "sans", 30, "left"),
    ("encode", 388, 928, 304, 438, 640, 382, "encode", "sans", 30, "left"),
    ("strip_l1", 50, 1550, 480, 584, 140, 524, "screen scraping show interfaces em0 breaks when a vendor changes the spacing;", "mono", 24, "left"),
    ("strip_l2", 50, 1550, 480, 584, 140, 558, "ask for structured output: show interfaces em0 | display xml, or JSON", "mono", 24, "left"),
    ("banner_l1", 68, 1532, 604, 692, 90, 644, "Markup languages like HTML annotate documents for rendering;", "sans", 24, "left"),
    ("banner_l2", 68, 1532, 604, 692, 90, 672, "data serialization formats represent typed data structures across languages", "sans", 24, "left"),
    ("xml_l1", 68, 1532, 700, 788, 150, 740, "XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model", "mono", 24, "left"),
    ("xml_l2", 68, 1532, 700, 788, 150, 770, "or //device[@name=\"leaf\"]/model, or XQuery; validate with XSD (xmlschema)", "mono", 24, "left"),
    ("json_l1", 68, 1532, 796, 910, 150, 836, "JSON: lighter; validate with JSON Schema:", "mono", 24, "left"),
    ("json_l2", 68, 1532, 796, 910, 150, 866, "$schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength,", "mono", 24, "left"),
    ("json_l3", 68, 1532, 796, 910, 150, 894, "minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()", "mono", 24, "left"),
    ("pb_l1", 68, 1532, 918, 1032, 150, 958, "Protocol Buffers: binary, .proto files compiled with protoc,", "mono", 24, "left"),
    ("pb_l2", 68, 1532, 918, 1032, 150, 988, "validated with protoc-gen-validate; FlatBuffers: read fields straight", "mono", 24, "left"),
    ("pb_l3", 68, 1532, 918, 1032, 150, 1016, "from the byte buffer; for high-throughput RPCs such as gRPC telemetry", "mono", 24, "left"),
    ("pickle", 68, 1532, 1040, 1102, 150, 1080, "pickle: Python only, unsafe on untrusted bytes", "mono", 24, "left"),
    ("takeaway", 50, 1550, 1114, 1184, 800, 1162, "Structured data beats fragile screen scraping", "sans", 30, "center")
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
    if min_pad < 16:
        status = "FAIL (<16px)"
        all_ok = False
    
    print(f"{name:15s} | L:{pad_left:5.1f} R:{pad_right:5.1f} T:{pad_top:4.1f} B:{pad_bottom:4.1f} | min:{min_pad:4.1f} | {status}")

print("\nStrict (>=16px) padding check:", "ALL PASSED" if all_ok else "FAILED")
