#!/bin/bash
set -euxo pipefail

LOG=/var/log/healthcare-benchmark-bootstrap.log
exec > >(tee -a "$LOG") 2>&1

# Keep package-install temp files on the large encrypted root volume rather than /tmp.
mkdir -p /opt/pip-tmp /opt/healthcare-benchmark /opt/healthcare-benchmark/results
chmod 1777 /opt/pip-tmp

# Use the standard Amazon Linux package manager.
dnf update -y
dnf install -y git python3.11 java-17-amazon-corretto-headless

python3.11 -m ensurepip --upgrade || true
python3.11 -m pip install --upgrade pip

# Avoid pip cache growth and the small default /tmp filesystem.
TMPDIR=/opt/pip-tmp python3.11 -m pip install --no-cache-dir --prefer-binary \
  numpy==2.1.3 pandas==2.2.3 pyarrow==18.1.0

TMPDIR=/opt/pip-tmp python3.11 -m pip install --no-cache-dir --prefer-binary \
  pyspark==3.5.3

chown -R ec2-user:ec2-user /opt/healthcare-benchmark /opt/pip-tmp
