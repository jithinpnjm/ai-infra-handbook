import xml.etree.ElementTree as ET
import re

# Expected labels exactly as in prompt:
expected_labels = [
    "Reading data off the wire: decode, then deserialize",
    "bytes arrive",
    'decode into a UTF-8 string, for example {"vendors":["Cisco","Juniper","Arista"]}',
    "deserialize with json.loads() into native structures: a Python dict and list",
    "serialize first",
    "encode",
    "Markup languages like HTML annotate documents for rendering; data serialization formats represent typed data structures across languages",
    'XML: tags, attributes, xmlns namespaces; query with XPath such as //device/model or //device[@name="leaf"]/model, or XQuery; validate with XSD (xmlschema)',
    "JSON: lighter; validate with JSON Schema: $schema https://json-schema.org/draft/2020-12/schema, minLength, maxLength, minimum 1, maximum 4094, IPv4 pattern regexes through jsonschema.validate()",
    "Protocol Buffers: binary, .proto files compiled with protoc, validated with protoc-gen-validate; FlatBuffers: read fields straight from the byte buffer; for high-throughput RPCs such as gRPC telemetry",
    "pickle: Python only, unsafe on untrusted bytes",
    "screen scraping show interfaces em0 breaks when a vendor changes the spacing; ask for structured output: show interfaces em0 | display xml, or JSON",
    "Network Programmability and Automation chapter 8",
    "Structured data beats fragile screen scraping"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. {l}")
