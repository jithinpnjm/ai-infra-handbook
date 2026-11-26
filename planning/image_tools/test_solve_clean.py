import re
import xml.etree.ElementTree as ET

# Centers of the 9 participants
centers = {
    "U": 148.0,
    "A": 311.0,
    "S": 474.0,
    "K": 637.0,
    "R": 800.0,
    "C": 963.0,
    "V": 1126.0,
    "D": 1289.0,
    "X": 1452.0
}

# We need all step circles and step cards to have ZERO collisions.
# Let's specify the placement of each step:
# For each step:
# num: step number
# src: source participant
# dst: target participant
# type: "msg_r", "dash_r", "msg_l", "self_r"
# card_pos: "above" or "below" the arrow line
# card_x: X coordinate of card rect
# card_w: width of card rect
# card_h: height of card rect
# lines: list of text lines or single text
