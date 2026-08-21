#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y git python3.11 java-17-amazon-corretto-headless
python3.11 -m ensurepip --upgrade || true
python3.11 -m pip install --upgrade pip
python3.11 -m pip install pyspark==3.5.3 pandas==2.2.3 numpy==2.1.3 pyarrow==18.1.0
mkdir -p /opt/healthcare-benchmark /opt/healthcare-benchmark/results
chown -R ec2-user:ec2-user /opt/healthcare-benchmark
