#!/bin/bash
# svg_render.sh part name [H]  -> /tmp/svgcheck/name.png
H=${3:-$(grep -o 'viewBox="0 0 1600 [0-9]*"' ~/Documents/GitHub/ai-infra-handbook/docs/$1/img/$2.svg | grep -o '[0-9]*"$' | tr -d '"')}
mkdir -p /tmp/svgcheck
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1600,${H:-900} --screenshot=/tmp/svgcheck/$2.png file://$HOME/Documents/GitHub/ai-infra-handbook/docs/$1/img/$2.svg >/dev/null 2>&1
