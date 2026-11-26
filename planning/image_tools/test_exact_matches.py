#!/usr/bin/env python3
import xml.etree.ElementTree as ET

cases = [
    ('<text><tspan x="800" dy="0">Reading the sample trace </tspan><tspan x="800" dy="54">line by line as a conversation</tspan></text>',
     'Reading the sample trace line by line as a conversation'),
    ('<text><tspan x="485" dy="0">duplex.example.com </tspan><tspan x="485" dy="36">(client)</tspan></text>',
     'duplex.example.com (client)'),
    ('<text><tspan x="1145" dy="0">mikado.example.com </tspan><tspan x="1145" dy="36">(server)</tspan></text>',
     'mikado.example.com (server)'),
    ('<text><tspan x="225" dy="0">lines 1-2: finding the link </tspan><tspan x="225" dy="26">address because the client </tspan><tspan x="225" dy="26">needs the server\'s MAC </tspan><tspan x="225" dy="26">before it can send a frame</tspan></text>',
     "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame"),
    ('<text><tspan x="225" dy="0">lines 3-5: </tspan><tspan x="225" dy="32">three-way handshake</tspan></text>',
     'lines 3-5: three-way handshake'),
    ('<text><tspan x="800" dy="0">Read the flags in order; a SYN with no reply stops the story at the first line, </tspan><tspan x="800" dy="36">and the next question is who stayed silent</tspan></text>',
     'Read the flags in order; a SYN with no reply stops the story at the first line, and the next question is who stayed silent')
]

for xml_str, expected in cases:
    elem = ET.fromstring(xml_str)
    raw_joined = "".join(elem.itertext()).strip()
    assert raw_joined == expected, f"FAIL: '{raw_joined}' != '{expected}'"
    print(f"PASS: '{raw_joined}'")
