#!/usr/bin/env python3

# Let's test if we can wrap text or choose fonts and box sizes
# First, let's examine the exact text of every label:

labels = {
    't1_head': 'Root directory /',
    't1_row': 'home -> inode A',
    't2_head': 'Directory /home (inode A)',
    't2_row': 'alice -> inode B',
    't3_head': 'Directory /home/alice (inode B)',
    't3_row': 'train.py -> inode C',
    'inode_c': 'Inode C: type, permissions, owner, size, times, link count, pointers to data blocks',
    'data_blocks': 'Data blocks on the device',
    'arr1': 'look up home',
    'arr2': 'look up alice',
    'arr3': 'look up train.py',
    'arr4': 'read the inode and its data',
    'path': '/home/alice/train.py',
    'callout': 'The name lives in the directory; everything else lives in the inode',
    'bottom': 'rename = change one table row, so it is instant on one filesystem'
}

for k, v in labels.items():
    print(f"{k:12s}: len={len(v):2d} | '{v}'")
