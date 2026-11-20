#!/bin/bash
# svg_sheet.sh out.png name1 name2 ... : contact sheet of /tmp/svgcheck/NAME.png (2 columns) for fast review
out=$1; shift
h=/tmp/svgcheck/sheet.html
echo '<body style="margin:0;background:#888"><div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;width:1600px">' > $h
for n in "$@"; do echo "<div><div style='color:#fff;font:14px sans-serif'>$n</div><img src='/tmp/svgcheck/$n.png' style='width:100%'></div>" >> $h; done
echo '</div></body>' >> $h
rows=$(( ($# + 1) / 2 ))
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1600,$((rows*480+40)) --screenshot=$out file://$h >/dev/null 2>&1
