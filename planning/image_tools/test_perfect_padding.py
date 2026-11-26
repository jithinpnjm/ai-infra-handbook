nodes = [
    {
        'id': 'U1', 'box': (120, 115, 650, 95),
        'lines': [('sbatch, srun, salloc,', 212, 150, 24, 'mono'),
                  ('squeue, sinfo, scancel', 212, 182, 24, 'mono')]
    },
    {
        'id': 'U2', 'box': (800, 115, 720, 95),
        'lines': [('sacct, sacctmgr, sreport', 892, 150, 24, 'mono'),
                  ('(accounting queries)', 892, 182, 24, 'sans')]
    },
    {
        'id': 'REST', 'box': (120, 330, 280, 135),
        'lines': [('slurmrestd', 202, 368, 24, 'mono'),
                  ('(optional)', 202, 398, 24, 'sans'),
                  ('REST API', 202, 432, 24, 'sans')]
    },
    {
        'id': 'BACKUP', 'box': (120, 480, 280, 145),
        'lines': [('backup slurmctld', 136, 516, 24, 'mono'),
                  ('(optional)', 136, 544, 24, 'sans'),
                  ('shared', 136, 578, 24, 'mono'),
                  ('StateSaveLocation', 136, 606, 24, 'mono')]
    },
    {
        'id': 'CTLD', 'box': (430, 325, 410, 300),
        'lines': [('slurmctld', 525, 385, 34, 'mono'),
                  ('controller, port 6817', 455, 445, 24, 'sans'),
                  ('queue, scheduler,', 455, 485, 24, 'sans'),
                  ('node and job state', 455, 520, 24, 'sans')]
    },
    {
        'id': 'DBD', 'box': (880, 330, 320, 160),
        'lines': [('slurmdbd, port 6819', 898, 435, 24, 'mono'),
                  ('accounting daemon', 898, 468, 24, 'sans')]
    },
    {
        'id': 'DB', 'box': (1230, 330, 290, 160),
        'lines': [('MariaDB / MySQL', 1248, 435, 26, 'sans'),
                  ('accounting database', 1248, 468, 24, 'sans')]
    },
    {
        'id': 'D1', 'box': (120, 735, 400, 95),
        'lines': [('slurmd, port 6818', 206, 792, 24, 'mono')]
    },
    {
        'id': 'D2', 'box': (550, 735, 185, 95),
        'lines': [('slurmd', 625, 792, 26, 'mono')]
    },
    {
        'id': 'D3', 'box': (765, 735, 185, 95),
        'lines': [('slurmd', 840, 792, 26, 'mono')]
    },
    {
        'id': 'STEPD', 'box': (120, 885, 400, 115),
        'lines': [('slurmstepd', 196, 928, 28, 'mono'),
                  ('one per job step', 196, 960, 24, 'sans'),
                  ('per node', 196, 988, 24, 'sans')]
    },
    {
        'id': 'JOB', 'box': (120, 1045, 400, 95),
        'lines': [('application processes', 196, 1102, 24, 'sans')]
    },
    {
        'id': 'MUNGE', 'box': (990, 725, 530, 165),
        'lines': [('munge on every node', 1070, 775, 30, 'mono'),
                  ('(shared key, authenticates', 1070, 818, 24, 'sans'),
                  ('every request)', 1070, 852, 24, 'sans')]
    }
]

all_pass = True
for n in nodes:
    bx, by, bw, bh = n['box']
    box_r = bx + bw
    box_b = by + bh
    
    for text, tx, ty, fs, ftype in n['lines']:
        char_w = 0.62 * fs if ftype == 'mono' else 0.6 * fs
        est_w = len(text) * char_w
        text_r = tx + est_w
        pad_l = tx - bx
        pad_r = box_r - text_r
        pad_t = ty - fs - by
        pad_b = box_b - ty
        
        if pad_r < 16 or pad_l < 16 or pad_t < 10 or pad_b < 10:
            all_pass = False
            print(f"FAILED: [{n['id']}] '{text}' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
        else:
            print(f"PASS:   [{n['id']:6}] '{text[:22]:22}' pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f}")

if all_pass:
    print("\nALL NODES PASS WITH PADDING >= 16px HORIZONTALLY AND AMPLE VERTICAL CLEARANCE!")
