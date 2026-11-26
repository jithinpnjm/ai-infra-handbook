from test_card_text import check_lines

lines_example_3 = [
    "ChainMap({retries: 5},",
    "{retries: 3, timeout: 10}):",
    "cfg[retries] is 5, cfg[timeout] is 10"
]
check_lines("Small example 3 lines with icon", lines_example_3, 640, 24, is_mono=True)
