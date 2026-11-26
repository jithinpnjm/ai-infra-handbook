import xml.etree.ElementTree as ET
import re

def check_paddings_and_clearances():
    # Conservative character width multipliers:
    # sans: 0.60 * font_size
    # mono: 0.62 * font_size

    # List of all boxes and their text lines:
    items = [
        {
            "name": "Title",
            "box": (0, 0, 1600, 120),
            "lines": [
                ("One blocking call freezes every task,", 48, False, 800, 48, "middle"),
                ("and how to route work off the loop", 48, False, 800, 96, "middle")
            ]
        },
        {
            "name": "Top Lane: Task B (calls blocking function)",
            "box": (320, 146, 940, 72),
            "lines": [
                ("time.sleep, requests.get, subprocess.run or heavy CPU", 24, True, 412, 191, "start")
            ],
            "icon_x": (336, 336 + 56)
        },
        {
            "name": "Top Lane: Stall warning box",
            "box": (60, 236, 1480, 92),
            "lines": [
                ("a task is never paused except at an await, ", 26, False, 160, 273, "start"),
                ("so all other tasks stall; timeouts fire everywhere", 26, False, 160, 307, "start")
            ],
            "icon_x": (80, 80 + 56)
        },
        {
            "name": "Routing Row 1 Left: blocking function",
            "box": (40, 378, 500, 84),
            "lines": [
                ("blocking function", 28, False, 135, 431, "start")
            ],
            "icon_x": (56, 56 + 56)
        },
        {
            "name": "Routing Row 1 Right: await asyncio.to_thread...",
            "box": (620, 378, 940, 84),
            "lines": [
                ("await asyncio.to_thread(blocking_fn, args) (3.9) ", 24, True, 710, 414, "start"),
                ("or loop.run_in_executor(executor, fn, *args)", 24, True, 710, 446, "start")
            ],
            "icon_x": (636, 636 + 56)
        },
        {
            "name": "Routing Row 2 Left: CPU-bound function",
            "box": (40, 482, 500, 84),
            "lines": [
                ("CPU-bound function", 28, False, 135, 535, "start")
            ],
            "icon_x": (56, 56 + 56)
        },
        {
            "name": "Routing Row 2 Right: run_in_executor...",
            "box": (620, 482, 940, 84),
            "lines": [
                ("run_in_executor with a ProcessPoolExecutor", 25, True, 710, 534, "start")
            ],
            "icon_x": (636, 636 + 56)
        },
        {
            "name": "Routing Row 3 Left: sync libraries...",
            "box": (40, 586, 500, 84),
            "lines": [
                ("sync libraries ", 24, True, 125, 622, "start"),
                ("requests, paramiko, boto3", 24, True, 125, 654, "start")
            ],
            "icon_x": (56, 56 + 56)
        },
        {
            "name": "Routing Row 3 Right: wrap with to_thread",
            "box": (620, 586, 940, 84),
            "lines": [
                ("wrap with to_thread", 26, True, 710, 638, "start")
            ],
            "icon_x": (636, 636 + 56)
        },
        {
            "name": "Async Libraries Panel",
            "box": (40, 694, 960, 176),
            "lines": [
                ("async libraries: aiohttp, httpx, asyncssh, ", 24, True, 130, 732, "start"),
                ("aiofiles (uses threads under the hood), asyncpg, ", 24, True, 130, 768, "start"),
                ("redis.asyncio, aiokafka, kubernetes_asyncio, ", 24, True, 130, 804, "start"),
                ("aioboto3, aiobotocore, grpc.aio", 24, True, 130, 840, "start")
            ],
            "icon_x": (58, 58 + 56)
        },
        {
            "name": "Side Note (uvloop)",
            "box": (1040, 694, 520, 176),
            "lines": [
                ("uvloop: faster drop-in loop ", 25, False, 1140, 766, "start"),
                ("on Linux and macOS", 25, False, 1140, 804, "start")
            ],
            "icon_x": (1065, 1065 + 56)
        },
        {
            "name": "Debug Strip",
            "box": (40, 894, 1520, 196),
            "lines": [
                ("asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms ", 24, True, 135, 934, "start"),
                ("(loop.slow_callback_duration), coroutines never awaited and tasks destroyed while pending; ", 24, True, 135, 974, "start"),
                ("asyncio.all_tasks() and task.print_stack() show where tasks are stuck; ", 24, True, 135, 1014, "start"),
                ("py-spy dump --pid when the loop itself is blocked", 24, True, 135, 1054, "start")
            ],
            "icon_x": (62, 62 + 56)
        },
        {
            "name": "Bottom Bar",
            "box": (40, 1114, 1520, 62),
            "lines": [
                ("Keep the loop free", 28, False, 800, 1155, "middle")
            ]
        }
    ]

    print("Checking text paddings and clearances (minimum 16px required everywhere):")
    all_ok = True
    for it in items:
        name = it["name"]
        bx, by, bw, bh = it["box"]
        right_box = bx + bw
        bottom_box = by + bh
        
        print(f"\n[{name}] box=({bx}, {by}, {bw}, {bh})")
        icon_end = it.get("icon_x", (0, 0))[1]
        
        for text, fs, is_mono, tx, ty, anchor in it["lines"]:
            factor = 0.62 if is_mono else 0.60
            w = len(text) * factor * fs
            if anchor == "middle":
                x1 = tx - w / 2
                x2 = tx + w / 2
            else:
                x1 = tx
                x2 = tx + w
            
            top_pad = (ty - fs * 0.8) - by
            bottom_pad = bottom_box - ty
            left_pad = x1 - bx
            right_pad = right_box - x2
            
            # If icon on left:
            if icon_end > 0:
                icon_gap = x1 - icon_end
            else:
                icon_gap = 999
            
            print(f"  Line: '{text[:30]}...' w={w:5.1f} | L_pad={left_pad:5.1f}, R_pad={right_pad:5.1f}, T_pad={top_pad:5.1f}, B_pad={bottom_pad:5.1f}, Icon_gap={icon_gap:5.1f}")
            
            if left_pad < 16 or right_pad < 16 or top_pad < 10 or bottom_pad < 10:
                print(f"    WARNING: Low padding in {name} line '{text}'!")
                all_ok = False
            if icon_gap < 14:
                print(f"    WARNING: Icon gap too small ({icon_gap}) in {name} line '{text}'!")
                all_ok = False

    print(f"\nOverall Paddings Check: {'PASSED' if all_ok else 'FAILED'}")
    assert all_ok

if __name__ == "__main__":
    check_paddings_and_clearances()
