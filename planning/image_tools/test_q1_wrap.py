q1 = "Is there a purpose-built module (package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?"

# At font-size 24: char width = 14.4 px.
# 606 / 14.4 = 42 chars per line!

# Line 1: Is there a purpose-built module (package,
# Length = 41 chars * 14.4 = 590.4 px <= 606 px!
# Line 2: service, user, file, lineinfile, template,
# Length = 42 chars * 14.4 = 604.8 px <= 606 px!
# Line 3: sysctl, systemd, mount, cron)?
# Length = 30 chars * 14.4 = 432.0 px <= 606 px!

print("Line 1:", len("Is there a purpose-built module (package,"), len("Is there a purpose-built module (package,") * 14.4)
print("Line 2:", len("service, user, file, lineinfile, template,"), len("service, user, file, lineinfile, template,") * 14.4)
print("Line 3:", len("sysctl, systemd, mount, cron)?"), len("sysctl, systemd, mount, cron)?") * 14.4)
