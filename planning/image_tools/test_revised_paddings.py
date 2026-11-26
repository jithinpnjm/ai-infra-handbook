def check_line(text, fs, font_type, box_w, text_x_offset=0):
    w_factor = 0.62 if font_type == 'mono' else 0.6
    w = len(text) * w_factor * fs
    pad_left = text_x_offset
    pad_right = box_w - (pad_left + w)
    min_pad = min(pad_left, pad_right)
    return w, pad_left, pad_right, min_pad

items = [
    # Left Panel
    ("Detect throttling", 32, "sans", 690, 160-65),
    # Card 1:
    ("usage_usec, user_usec, system_usec,", 24, "mono", 690, 160-65),
    ("nr_periods, nr_throttled,", 24, "mono", 690, 160-65),
    ("throttled_usec, nr_bursts, burst_usec", 24, "mono", 690, 160-65),
    # Card 2:
    ("compare nr_throttled with nr_periods", 25, "sans", 690, 160-65),
    ("and check throttled_usec", 25, "sans", 690, 160-65),
    # Card 3:
    ("container_cpu_cfs_throttled_periods_total", 24, "mono", 690, 85-65),
    ("and container_cpu_cfs_periods_total", 24, "mono", 690, 85-65),
    # Card 4:
    ("cpu.pressure (PSI)", 28, "mono", 690, 160-65),
    # Right Panel
    ("The oversubscription trap", 32, "sans", 690, 940-845),
    ("64 CPUs", 30, "sans", 690, 935-845),
    ("cpu.max = 200000 100000 (2 CPUs)", 24, "mono", 650, 885-865),
    ("nproc = 64", 24, "mono", 210, (210 - len("nproc = 64")*0.62*24)/2),
    # Result Card:
    ("the quota is burned early", 24, "sans", 690, 940-845),
    ("in each period, then every", 24, "sans", 690, 940-845),
    ("thread pauses even though", 24, "sans", 690, 940-845),
    ("other CPUs are idle", 24, "sans", 690, 940-845),
    # Fix Table:
    ("Go: automaxprocs (GOMAXPROCS)", 24, "mono", 660, 20),
    ("Java: -XX:ActiveProcessorCount", 24, "mono", 660, 20),
    ("OpenMP: OMP_NUM_THREADS", 24, "mono", 660, 20),
    ("Python: os.cpu_count()", 24, "mono", 660, 20),
    ("reports the host, pass the limit in", 24, "mono", 660, 20),
    # Footer Card 1:
    ("Kernels before 5.4", 24, "sans", 486, 130-40),
    ("(slice-expiry fix) could", 24, "sans", 486, 60-40),
    ("throttle even with unused", 24, "sans", 486, 60-40),
    ("quota: use a recent kernel", 24, "sans", 486, 60-40),
    # Footer Card 2:
    ("cpu.max.burst", 24, "mono", 486, 647-557),
    ("(kernel 5.14 and later)", 24, "sans", 486, 577-557),
    ("lets a group save unused", 24, "sans", 486, 577-557),
    ("quota for short bursts", 24, "sans", 486, 577-557),
    # Footer Card 3:
    ("Inside a container,", 24, "sans", 486, 1164-1074),
    ("nproc and /proc/cpuinfo", 24, "sans", 486, 1094-1074),
    ("still show the host unless", 24, "sans", 486, 1094-1074),
    ("you use lxcfs or a runtime", 24, "sans", 486, 1094-1074),
    ("that understands limits", 24, "sans", 486, 1094-1074),
    # Bottom bar:
    ("Average usage can look healthy while the pauses hide inside each period", 25, "sans", 1520, (1520 - len("Average usage can look healthy while the pauses hide inside each period")*0.6*25)/2)
]

print("Checking paddings for all lines:")
all_pass = True
for line, fs, ftype, box_w, offset in items:
    w, pl, pr, min_pad = check_line(line, fs, ftype, box_w, offset)
    status = "PASS" if min_pad >= 16 else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"[{status}] min_pad={min_pad:5.1f}px (pl={pl:5.1f}, pr={pr:5.1f}, w={w:5.1f}, box={box_w}) '{line}'")

print("\nALL LINES PADDING >= 16px:", all_pass)
