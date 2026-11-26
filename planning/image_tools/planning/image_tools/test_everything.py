#!/usr/bin/env python3

def test_everything():
    # Define every box and its lines:
    # (box_name, (bx, by, bw, bh), [ (line_text, font_type, font_size, anchor, x, y) ])
    
    boxes = [
        # 1. Section 1 Container (x=40, y=125, w=1520, h=200)
        (
            "section-anatomy-format",
            (40, 125, 1520, 200),
            [
                ("name-version-pythontag-abitag-platformtag", "mono", 24, "middle", 800, 165),
                ("numpy-1.26.4-cp311-cp311-manylinux_2_17_x86_64.whl", "mono", 24, "middle", 800, 195)
            ]
        ),
        # 2. Piece 1
        (
            "piece-1",
            (60, 208, 190, 105),
            [
                ("numpy:", "mono", 24, "middle", 155, 248),
                ("name", "sans", 24, "middle", 155, 276)
            ]
        ),
        # 3. Piece 2
        (
            "piece-2",
            (265, 208, 190, 105),
            [
                ("1.26.4:", "mono", 24, "middle", 360, 248),
                ("version", "sans", 24, "middle", 360, 276)
            ]
        ),
        # 4. Piece 3
        (
            "piece-3",
            (470, 208, 310, 105),
            [
                ("cp311: Python tag", "sans", 24, "middle", 625, 248),
                ("(CPython 3.11)", "sans", 24, "middle", 625, 276)
            ]
        ),
        # 5. Piece 4
        (
            "piece-4",
            (795, 208, 190, 105),
            [
                ("cp311:", "mono", 24, "middle", 890, 248),
                ("ABI tag", "sans", 24, "middle", 890, 276)
            ]
        ),
        # 6. Piece 5
        (
            "piece-5",
            (1000, 208, 540, 105),
            [
                ("manylinux_2_17_x86_64: platform tag", "sans", 24, "middle", 1270, 248),
                ("(x86_64 Linux, glibc-compatible)", "sans", 24, "middle", 1270, 276)
            ]
        ),

        # Section 2: y = 365, h = 275 (ends at 640)
        # 7. Var 1
        (
            "var-1",
            (125, 373, 700, 84),
            [
                ("py3-none-any:", "mono", 24, "middle", 475, 413),
                ("pure Python, installs anywhere", "sans", 24, "middle", 475, 437)
            ]
        ),
        # 8. Var 2
        (
            "var-2",
            (845, 373, 700, 84),
            [
                ("manylinux: runs on most Linux distributions", "sans", 24, "middle", 1195, 413),
                ("with a compatible glibc", "sans", 24, "middle", 1195, 437)
            ]
        ),
        # 9. Var 3
        (
            "var-3",
            (125, 463, 700, 84),
            [
                ("musllinux:", "mono", 24, "middle", 475, 503),
                ("Alpine, which uses musl instead", "sans", 24, "middle", 475, 527)
            ]
        ),
        # 10. Var 4
        (
            "var-4",
            (845, 463, 700, 84),
            [
                ("abi3:", "mono", 24, "middle", 1195, 503),
                ("the stable ABI", "sans", 24, "middle", 1195, 527)
            ]
        ),
        # 11. Var 5
        (
            "var-5",
            (125, 553, 700, 84),
            [
                ("+cu121: local version label (PEP 440) marking", "sans", 24, "middle", 475, 593),
                ("a CUDA build, used by PyTorch index wheels", "sans", 24, "middle", 475, 617)
            ]
        ),
        # 12. Var 6
        (
            "var-6",
            (845, 553, 700, 84),
            [
                ("aarch64: Grace and other ARM hosts,", "sans", 24, "middle", 1195, 593),
                ("some packages have no wheels", "sans", 24, "middle", 1195, 617)
            ]
        ),

        # Section 3: y = 680 to 865 (h = 185)
        # 13. Decision Box (Question)
        (
            "box-decision",
            (40, 680, 450, 185),
            [
                ("pip finds a", "sans", 30, "middle", 280, 760),
                ("compatible wheel?", "sans", 30, "middle", 280, 796)
            ]
        ),
        # 14. Box YES
        (
            "box-yes",
            (620, 680, 940, 75),
            [
                ("unzip, no build step, fast", "sans", 28, "middle", 1100, 727)
            ]
        ),
        # 15. Box NO
        (
            "box-no",
            (620, 765, 940, 100),
            [
                ("builds from the sdist: needs compilers and headers;", "sans", 24, "middle", 1100, 805),
                ("the usual reason an install takes 10 minutes or fails in a slim container", "sans", 24, "middle", 1100, 833)
                # wait! Check length of line 2: 73 chars * 24 * 0.6 = 1051.2px > 940px!
                # It MUST be 3 lines!
            ]
        ),

        # Section 4: Tool line & early check (y = 905 to 1055, h = 150)
        # Tool 1
        (
            "tool-1",
            (56, 915, 1488, 60),
            [
                ("python -m build makes dist/myops-0.3.1.tar.gz (sdist) and dist/myops-0.3.1-py3-none-any.whl (wheel)", "mono", 24, "middle", 800, 955)
                # wait! Len=99 chars * 24 * 0.62 = 1473.1px. Inside 1488: pad = (1488 - 1473.1)/2 = 7.45 < 16!
                # Must be 2 lines!
            ]
        ),
        # Tool 2
        (
            "tool-2",
            (56, 985, 734, 60),
            [
                ("python -m pip debug --verbose lists the supported tags", "mono", 24, "middle", 423, 1025)
                # wait! Len=54 chars * 24 * 0.62 = 803.5px > 734px!
                # Must be 2 lines!
            ]
        ),
        # Tool 3
        (
            "tool-3",
            (810, 985, 734, 60),
            [
                ("pip download --only-binary=:all: --platform manylinux2014_aarch64 ...", "mono", 24, "middle", 1177, 1025)
                # wait! Len=69 chars * 24 * 0.62 = 1026.7px > 734px!
                # Must be 2 lines!
            ]
        ),

        # Section 5: Bottom bar
        (
            "bottom-bar",
            (40, 1095, 1520, 65),
            [
                ("Check the tags of every wheel you plan to ship against the machines that will install it", "sans", 26, "middle", 800, 1137)
            ]
        )
    ]
    
    print("Boxes defined")

test_everything()
