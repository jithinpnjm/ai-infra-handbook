#!/bin/bash
# Controller
sudo apt-get install -y munge mariadb-server slurm-wlm slurmdbd
sudo mysql -e "CREATE DATABASE slurm_acct_db;"
sudo mysql -e "CREATE USER 'slurm'@'localhost' IDENTIFIED BY '<strong-password>';"
sudo mysql -e "GRANT ALL ON slurm_acct_db.* TO 'slurm'@'localhost';"

# /etc/slurm/slurmdbd.conf per Section 2, mode 600
sudo systemctl enable --now slurmdbd
