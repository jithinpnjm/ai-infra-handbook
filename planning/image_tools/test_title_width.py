#!/usr/bin/env python3

# Let's verify every single element's coordinates and paddings:

# 1. Title:
# text: "Reading the sample trace line by line as a conversation"
# size: 48 bold, sans-serif
# width = 55 chars * 0.6 * 48 = 1584 px?
# WAIT! 55 * 0.6 * 48 = 1584 px!
# If width is 1584 px, on a 1600 px canvas, left margin is (1600 - 1584) / 2 = 8 px!
# The rule says: "Leave at least 40 px between boxes and 40 px outside margin."
# If title is 55 chars, does it wrap onto 2 lines?
title_len = len("Reading the sample trace line by line as a conversation")
print(f"Title length: {title_len} chars. At 48px: 55 * 0.6 * 48 = {title_len * 0.6 * 48}px")
