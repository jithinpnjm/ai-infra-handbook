#!/bin/bash
# usage: decode_latest.sh name1 name2 ...  (oldest grab first). Finds newest browser-tool result files in the CURRENT project's tool-results dir.
S="$(cd "$(dirname "$0")" && pwd)"
D=$(ls -dt /Users/jithinpjoseph/.claude/projects/-Users-jithinpjoseph-Documents-GitHub-trading-bot/*/tool-results | head -1)
n=$#
files=($(ls -t $D/mcp-Claude_Browser-javascript_tool-*.txt | head -$n | tac))
i=0
for name in "$@"; do python3 $S/decode_result.py "${files[$i]}" "$name"; i=$((i+1)); done
