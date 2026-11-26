with open("make_perfect_keda.py") as f:
    code = f.read()

code = code.replace('<rect x="65" y="480" width="717" height="56"', '<rect x="65" y="480" width="717" height="58"')
with open("make_perfect_keda.py", "w") as f:
    f.write(code)

with open("test_final_audit.py") as f:
    audit_code = f.read()

audit_code = audit_code.replace('("pollingInterval", "pollingInterval 15", 24, "mono", 423 - len("pollingInterval 15")*0.62*24/2, 516, 65, 480, 717, 56)', '("pollingInterval", "pollingInterval 15", 24, "mono", 423 - len("pollingInterval 15")*0.62*24/2, 516, 65, 480, 717, 58)')
with open("test_final_audit.py", "w") as f:
    f.write(audit_code)

import subprocess
subprocess.run(["python3", "make_perfect_keda.py"], check=True)
subprocess.run(["python3", "test_final_audit.py"], check=True)
