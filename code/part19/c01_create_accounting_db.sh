#!/bin/bash
# Controller: create the accounting database (Chapter 6.7 installs the packages)
sudo mysql -e "CREATE DATABASE slurm_acct_db;"
sudo mysql -e "CREATE USER 'slurm'@'localhost' IDENTIFIED BY '<strong-password>';"
sudo mysql -e "GRANT ALL ON slurm_acct_db.* TO 'slurm'@'localhost';"

# After /etc/slurm/slurmdbd.conf is written, lock it down
sudo chown slurm:slurm /etc/slurm/slurmdbd.conf
sudo chmod 600 /etc/slurm/slurmdbd.conf
