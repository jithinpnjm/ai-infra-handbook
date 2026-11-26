import xml.etree.ElementTree as ET
import re

# Let's inspect the exact labels and character counts
expected_labels = [
    'Deleted but open: the name is gone, the blocks stay until the descriptor closes',
    'a process opens app.log and writes 20 MB',
    'rm removes the name',
    'link count 0',
    'ls and du no longer see the file',
    'the process still holds the descriptor, so df still counts the blocks',
    '/tmp/.../app.log (deleted)',
    'rescue, copy out, then truncate through /proc/PID/fd/N',
    'df used space falls',
    'copy what you need out of /proc/PID/fd/N',
    ': > /proc/PID/fd/N',
    'the process keeps writing',
    'lasting fix: make the writer reopen its file after rotation',
    'The space comes back when the last descriptor closes or the file is truncated.'
]

print("Labels count:", len(expected_labels))
