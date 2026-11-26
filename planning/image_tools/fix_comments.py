with open("generate_svg.py") as f:
    code = f.read()

code = code.replace("NVML --> Sched", "NVML to Sched")
code = code.replace("SConf --> Sched", "SConf to Sched")
code = code.replace("Sched --> Cgroup", "Sched to Cgroup")
code = code.replace("Cgroup --> Bind", "Cgroup to Bind")

with open("generate_svg.py", "w") as f:
    f.write(code)

