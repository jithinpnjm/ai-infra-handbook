nodes = [
    {
        'id': 'U1', 'box': (120, 115, 650, 92),
        'icon': (138, 133, 56, 56),
        'lines': [('sbatch, srun, salloc,', 212, 148, 24, 'mono'),
                  ('squeue, sinfo, scancel', 212, 180, 24, 'mono')]
    },
    {
        'id': 'U2', 'box': (800, 115, 720, 92),
        'icon': (818, 133, 56, 56),
        'lines': [('sacct, sacctmgr, sreport', 892, 148, 24, 'mono'),
                  ('(accounting queries)', 892, 180, 24, 'sans')]
    },
    {
        'id': 'REST', 'box': (120, 330, 280, 125),
        'icon': (136, 345, 56, 56),
        'lines': [('slurmrestd', 202, 365, 24, 'mono'),
                  ('(optional)', 202, 393, 24, 'sans'),
                  ('REST API', 202, 425, 24, 'sans')]
    },
    {
        'id': 'BACKUP', 'box': (120, 480, 280, 135),
        'icon': (136, 498, 56, 56),
        'lines': [('backup slurmctld', 202, 515, 24, 'mono'),
                  ('(optional)', 202, 543, 24, 'sans'),
                  ('shared StateSaveLocation', 136, 585, 24, 'mono')]
    },
    {
        'id': 'CTLD', 'box': (440, 325, 410, 290),
        'icon': (465, 345, 56, 56),
        'lines': [('slurmctld', 540, 380, 34, 'mono'),
                  ('controller, port 6817', 465, 440, 24, 'sans'),
                  ('queue, scheduler,', 465, 480, 24, 'sans'),
                  ('node and job state', 465, 514, 24, 'sans')]
    },
    {
        'id': 'DBD', 'box': (910, 335, 310, 150),
        'icon': (928, 350, 56, 56),
        'lines': [('slurmdbd, port 6819', 1000, 380, 28, 'mono'),
                  ('accounting daemon', 1000, 422, 24, 'sans')]
    },
    {
        'id': 'DB', 'box': (1260, 335, 260, 150),
        'icon': (1276, 350, 56, 56),
        'lines': [('MariaDB / MySQL', 1348, 380, 26, 'sans'),
                  ('accounting database', 1348, 422, 24, 'sans')]
    },
    {
        'id': 'D1', 'box': (120, 735, 370, 95),
        'icon': (136, 752, 56, 56),
        'lines': [('slurmd, port 6818', 206, 792, 26, 'mono')]
    },
    {
        'id': 'D2', 'box': (530, 735, 190, 95),
        'icon': (546, 754, 40, 40),
        'lines': [('slurmd', 600, 792, 28, 'mono')]
    },
    {
        'id': 'D3', 'box': (755, 735, 190, 95),
        'icon': (771, 754, 40, 40),
        'lines': [('slurmd', 825, 792, 28, 'mono')]
    },
    {
        'id': 'STEPD', 'box': (120, 885, 370, 105),
        'icon': (136, 908, 40, 40),
        'lines': [('slurmstepd', 192, 928, 28, 'mono'),
                  ('one per job step per node', 192, 964, 24, 'sans')]
    },
    {
        'id': 'JOB', 'box': (120, 1045, 370, 90),
        'icon': (136, 1060, 56, 56),
        'lines': [('application processes', 206, 1101, 26, 'sans')]
    },
    {
        'id': 'MUNGE', 'box': (1000, 725, 540, 165),
        'icon': (1025, 750, 56, 56),
        'lines': [('munge on every node', 1100, 775, 30, 'mono'),
                  ('(shared key, authenticates', 1100, 817, 24, 'sans'),
                  ('every request)', 1100, 849, 24, 'sans')]
    }
]

for n in nodes:
    bx, by, bw, bh = n['box']
    box_r = bx + bw
    box_b = by + bh
    
    # Check lines
    for text, tx, ty, fs, ftype in n['lines']:
        char_w = 0.62 * fs if ftype == 'mono' else 0.6 * fs
        est_w = len(text) * char_w
        text_r = tx + est_w
        pad_l = tx - bx
        pad_r = box_r - text_r
        pad_t = ty - fs - by
        pad_b = box_b - ty
        
        status = "OK"
        if pad_r < 10 or pad_l < 10:
            status = "TIGHT"
        print(f"[{n['id']:6}] '{text[:20]:20}' text_r={text_r:6.1f}, box_r={box_r:6.1f}, pad_r={pad_r:5.1f} | {status}")
