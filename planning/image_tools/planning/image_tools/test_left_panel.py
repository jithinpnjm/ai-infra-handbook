def calc_left_panel():
    y_start = 480
    row_h = 55
    row_gap = 12
    # Row 1: request counts | in-flight requests
    # Row 2: queue time | error and retry rates
    # Row 3: TTFT and ITL percentiles | ejection events
    # Row 4: hot-backend alerts (full width or col 1) | trace each request...
    print("Row 1:", y_start)
    print("Row 2:", y_start + row_h + row_gap)
    print("Row 3:", y_start + 2*(row_h + row_gap))
    print("Row 4:", y_start + 3*(row_h + row_gap))
    print("Row 5:", y_start + 4*(row_h + row_gap))

calc_left_panel()
