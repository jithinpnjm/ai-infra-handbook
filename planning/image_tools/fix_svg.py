with open("test_output.svg") as f:
    text = f.read()

# Fix Card Left:
# <tspan font-family="'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace" font-size="25" font-weight="bold" fill="#207448">--gpus-per-node=4</tspan><tspan font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24">): per node; with </tspan>

# Fix Card Right:
# <tspan font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24"> (</tspan><tspan font-family="'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace" font-size="25" font-weight="bold" fill="#db8129">-G 4</tspan><tspan font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="24">): total for the job; Slurm decides</tspan>

# Fix Note 3:
# <tspan font-family="'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace" font-weight="bold" fill="#207448">--mem-per-cpu</tspan><tspan font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif">, default is the partition DefMemPerGPU</tspan>

