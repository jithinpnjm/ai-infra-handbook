#!/usr/bin/env python3

def full_simulation():
    # We will define all boxes and their text lines, and verify all paddings >= 16.0
    boxes = {}
    
    # ---------------------------------------------------------
    # SECTION 1: Filename Anatomy
    # Container: x=40, y=125, w=1520, h=200
    # ---------------------------------------------------------
    boxes["section-anatomy"] = {
        "box": (40, 125, 1520, 200),
        "texts": [
            {
                "text": "name-version-pythontag-abitag-platformtag",
                "fs": 24, "ff": "mono", "anchor": "middle",
                "lines": [("name-version-pythontag-abitag-platformtag", 800, 165)]
            },
            {
                "text": "numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl",
                "fs": 24, "ff": "mono", "anchor": "middle",
                "lines": [("numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl", 800, 195)]
            }
        ]
    }
    
    # Five piece boxes inside Section 1: y = 208, h = 105
    # Piece 1: numpy: name (x=60, w=190, y=208, h=105)
    boxes["piece-1"] = {
        "box": (60, 208, 190, 105),
        "texts": [{
            "text": "numpy: name", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("numpy:", 155, 248), ("name", 155, 276)]
        }]
    }
    # Piece 2: 1.26.4: version (x=265, w=190, y=208, h=105)
    boxes["piece-2"] = {
        "box": (265, 208, 190, 105),
        "texts": [{
            "text": "1.26.4: version", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("1.26.4:", 360, 248), ("version", 360, 276)]
        }]
    }
    # Piece 3: cp311: Python tag (CPython 3.11) (x=470, w=310, y=208, h=105)
    boxes["piece-3"] = {
        "box": (470, 208, 310, 105),
        "texts": [{
            "text": "cp311: Python tag (CPython 3.11)", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("cp311: Python tag", 625, 248), ("(CPython 3.11)", 625, 276)]
        }]
    }
    # Piece 4: cp311: ABI tag (x=795, w=190, y=208, h=105)
    boxes["piece-4"] = {
        "box": (795, 208, 190, 105),
        "texts": [{
            "text": "cp311: ABI tag", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("cp311:", 890, 248), ("ABI tag", 890, 276)]
        }]
    }
    # Piece 5: manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible) (x=1000, w=540, y=208, h=105)
    boxes["piece-5"] = {
        "box": (1000, 208, 540, 105),
        "texts": [{
            "text": "manylinux_2_17_x86_64: platform tag (x86_64 Linux, glibc-compatible)", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [
                ("manylinux_2_17_x86_64: platform tag", 1270, 248),
                ("(x86_64 Linux, glibc-compatible)", 1270, 276)
            ]
        }]
    }

    # ---------------------------------------------------------
    # SECTION 2: Variants Strip (y = 365, h = 210)
    # Container: x=40, y=365, w=1520, h=210
    # 6 variants in 2 columns x 3 rows:
    # Col 1: x = 125, w = 700
    # Col 2: x = 845, w = 700
    # Row 1: y = 377, h = 58
    # Row 2: y = 441, h = 58
    # Row 3: y = 505, h = 58
    # ---------------------------------------------------------
    boxes["var-1"] = {
        "box": (125, 377, 700, 58),
        "texts": [{
            "text": "py3-none-any: pure Python, installs anywhere", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("py3-none-any: pure Python, installs anywhere", 475, 417)]
        }]
    }
    boxes["var-2"] = {
        "box": (845, 377, 700, 58),
        "texts": [{
            "text": "manylinux: runs on most Linux distributions with a compatible glibc", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("manylinux: runs on most Linux distributions with a compatible glibc", 1195, 417)]
        }]
    }
    boxes["var-3"] = {
        "box": (125, 441, 700, 58),
        "texts": [{
            "text": "musllinux: Alpine, which uses musl instead", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("musllinux: Alpine, which uses musl instead", 475, 481)]
        }]
    }
    boxes["var-4"] = {
        "box": (845, 441, 700, 58),
        "texts": [{
            "text": "abi3: the stable ABI", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("abi3: the stable ABI", 1195, 481)]
        }]
    }
    boxes["var-5"] = {
        "box": (125, 505, 700, 58),
        "texts": [{
            "text": "+cu121: local version label (PEP 440) marking a CUDA build, used by PyTorch index wheels", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [
                ("+cu121: local version label (PEP 440) marking", 475, 533),
                ("a CUDA build, used by PyTorch index wheels", 475, 555) # wait, inside h=58 2 lines?
            ]
        }]
    }
    boxes["var-6"] = {
        "box": (845, 505, 700, 58),
        "texts": [{
            "text": "aarch64: Grace and other ARM hosts, some packages have no wheels", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [("aarch64: Grace and other ARM hosts, some packages have no wheels", 1195, 545)]
        }]
    }

    # ---------------------------------------------------------
    # SECTION 3: Decision Flow (y = 615, h = 205)
    # ---------------------------------------------------------
    boxes["box-decision"] = {
        "box": (40, 642, 450, 150),
        "texts": [{
            "text": "pip finds a compatible wheel?", "fs": 30, "ff": "sans", "anchor": "middle",
            "lines": [("pip finds a compatible wheel?", 265, 727)]
        }]
    }
    boxes["box-yes"] = {
        "box": (620, 615, 940, 85),
        "texts": [{
            "text": "unzip, no build step, fast", "fs": 28, "ff": "sans", "anchor": "middle",
            "lines": [("unzip, no build step, fast", 1100, 667)]
        }]
    }
    boxes["box-no"] = {
        "box": (620, 715, 940, 105),
        "texts": [{
            "text": "builds from the sdist: needs compilers and headers; the usual reason an install takes 10 minutes or fails in a slim container", "fs": 24, "ff": "sans", "anchor": "middle",
            "lines": [
                ("builds from the sdist: needs compilers and headers;", 1100, 755),
                ("the usual reason an install takes 10 minutes or fails in a slim container", 1100, 783) # wait, line 2 len=73?
            ]
        }]
    }

    # ---------------------------------------------------------
    # SECTION 4: Tool Line & Early Check (y = 860, h = 195)
    # ---------------------------------------------------------
    boxes["tool-1"] = {
        "box": (56, 872, 1488, 85),
        "texts": [{
            "text": "python -m build makes dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)", "fs": 24, "ff": "mono", "anchor": "middle",
            "lines": [
                ("python -m build makes dist/myops-0.3.1.tar.gz (sdist)", 800, 912),
                ("and dist/myops-0.3.1-py3-none-any.whl (wheel)", 800, 938)
            ]
        }]
    }
    boxes["tool-2"] = {
        "box": (56, 965, 734, 80),
        "texts": [{
            "text": "python -m pip debug --verbose lists the supported tags", "fs": 24, "ff": "mono", "anchor": "middle",
            "lines": [
                ("python -m pip debug --verbose", 423, 1005),
                ("lists the supported tags", 423, 1031)
            ]
        }]
    }
    boxes["tool-3"] = {
        "box": (810, 965, 734, 80),
        "texts": [{
            "text": "pip download --only-binary=:all: --platform manylinux2014_aarch64 ...", "fs": 24, "ff": "mono", "anchor": "middle",
            "lines": [
                ("pip download --only-binary=:all:", 1177, 1005),
                ("--platform manylinux2014_aarch64 ...", 1177, 1031)
            ]
        }]
    }

    # ---------------------------------------------------------
    # SECTION 5: Bottom Bar (y = 1095, h = 65)
    # ---------------------------------------------------------
    boxes["bottom-bar"] = {
        "box": (40, 1095, 1520, 65),
        "texts": [{
            "text": "Check the tags of every wheel you plan to ship against the machines that will install it", "fs": 26, "ff": "sans", "anchor": "middle",
            "lines": [("Check the tags of every wheel you plan to ship against the machines that will install it", 800, 1137)]
        }]
    }

    all_passed = True
    for bid, bdata in boxes.items():
        bx, by, bw, bh = bdata["box"]
        b_right = bx + bw
        b_bot = by + bh
        for tdata in bdata["texts"]:
            fs = tdata["fs"]
            ff = tdata["ff"]
            mult = 0.62 if ff == "mono" else 0.60
            lines = tdata["lines"]
            for i, (l_text, lx, ly) in enumerate(lines):
                lw = len(l_text) * fs * mult
                if tdata["anchor"] == "middle":
                    l_start = lx - lw / 2
                    l_end = lx + lw / 2
                elif tdata["anchor"] == "end":
                    l_start = lx - lw
                    l_end = lx
                else:
                    l_start = lx
                    l_end = lx + lw
                
                l_top = ly - fs
                l_bot = ly + 0.25 * fs # 6px for fs=24
                
                pad_l = l_start - bx
                pad_r = b_right - l_end
                pad_t = l_top - by
                pad_b = b_bot - l_bot
                
                status = "OK"
                reasons = []
                if pad_l < 16.0: reasons.append(f"L={pad_l:.1f}<16")
                if pad_r < 16.0: reasons.append(f"R={pad_r:.1f}<16")
                # Top pad only matters for first line
                if i == 0 and pad_t < 16.0: reasons.append(f"T={pad_t:.1f}<16")
                # Bot pad only matters for last line
                if i == len(lines) - 1 and pad_b < 16.0: reasons.append(f"B={pad_b:.1f}<16")
                
                if reasons:
                    status = "FAIL: " + ", ".join(reasons)
                    all_passed = False
                print(f"[{bid:15s}] '{l_text[:28]:28s}' -> L:{pad_l:5.1f} R:{pad_r:5.1f} T:{pad_t:5.1f} B:{pad_b:5.1f} | {status}")

    print(f"\nFinal result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")

full_simulation()
