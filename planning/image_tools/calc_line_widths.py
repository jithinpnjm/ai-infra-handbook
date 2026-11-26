def check_lines():
    # Card boundaries:
    # Card x=60, width=1480 -> right edge 1540
    # Icon transform translate(74, y) -> width ~48 -> right edge 122
    # If text starts at x=144, padding from icon is 144 - 122 = 22px!
    # If reach track is on the far right:
    # Say reach track is at x=1380 to 1520 (width 140px).
    # Then text must end before x = 1380 - 20 = 1360!
    # Max text width = 1360 - 144 = 1216px!
    # At font-size 24px, sans-serif width is char * (24 * 0.6) = char * 14.4px.
    # At mono (0.62 * 24 = 14.88px).
    # Max chars per line = 1216 / 14.4 = ~84 chars.
    
    # Let's inspect Rung 5:
    # "vars_files: loads files at the start of the play; the file name can itself be a template, vars/{{ ansible_facts[os_family] | lower }}.yml, so Debian and RedHat hosts load different files with no if statement"
    # Total chars: 207.
    # If split into 3 lines:
    l1 = "vars_files: loads files at the start of the play; the file name can itself be a template, "
    l2 = "vars/{{ ansible_facts[os_family] | lower }}.yml, "
    l3 = "so Debian and RedHat hosts load different files with no if statement"
    print("Rung 5 l1:", len(l1), "chars ->", len(l1)*14.4, "px")
    print("Rung 5 l2 (mono):", len(l2), "chars ->", len(l2)*14.88, "px")
    print("Rung 5 l3:", len(l3), "chars ->", len(l3)*14.4, "px")

    # Placement rule:
    # "put a value where the people who own it will look: a cluster-wide default in group_vars/all, a rack's special case in the group for that rack, a one-off test on the command line where it vanishes when the run ends; which one wins when two disagree is in 4.5"
    p1 = "put a value where the people who own it will look: a cluster-wide default in group_vars/all, "
    p2 = "a rack's special case in the group for that rack, a one-off test on the command line "
    p3 = "where it vanishes when the run ends; which one wins when two disagree is in 4.5"
    print("Placement p1:", len(p1), "chars ->", len(p1)*14.4, "px")
    print("Placement p2:", len(p2), "chars ->", len(p2)*14.4, "px")
    print("Placement p3:", len(p3), "chars ->", len(p3)*14.4, "px")

    # Story strip:
    s1 = "late Tuesday: raising the NCCL debug level for the second cluster "
    s2 = "also turned on verbose logging on the first, filling its disk: "
    s3 = "the setting was written in a place that reached further than you thought"
    print("Story s1:", len(s1), "chars ->", len(s1)*14.4, "px")
    print("Story s2:", len(s2), "chars ->", len(s2)*14.4, "px")
    print("Story s3:", len(s3), "chars ->", len(s3)*14.4, "px")

check_lines()
