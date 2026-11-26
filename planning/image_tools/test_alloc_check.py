#!/usr/bin/env python3

def test_allocation():
    # Total width = 1600
    # Left margin = 40, Right margin = 40. Usable = 1520.
    # 3 gaps between 4 columns.
    # If gap = 24 px:
    # 3 * 24 = 72 px. Usable for columns = 1520 - 72 = 1448 px.
    
    # Col 1: pre_tasks
    # Col 2: tasks
    # Col 3: handlers
    # Col 4: post_tasks
    
    # In Col 2, if we have two sub-columns of tasks:
    # Sub-col A (left) and Sub-col B (right).
    # Then Col 2 needs ~640 px width.
    # Remaining for Col 1, Col 3, Col 4: 1448 - 640 = 808 px.
    # Col 1 (pre_tasks): 320 px
    # Col 3 (handlers): 244 px
    # Col 4 (post_tasks): 244 px
    # Total = 320 + 640 + 244 + 244 = 1448 px!
    
    print(f"Col 1: 320 px (avail {320-32} px)")
    print(f"Col 2: 640 px (two sub-cols of { (640 - 24 - 32)/2 } px)")
    print(f"Col 3: 244 px (avail {244-32} px)")
    print(f"Col 4: 244 px (avail {244-32} px)")

test_allocation()
