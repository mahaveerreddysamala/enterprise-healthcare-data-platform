# Local Windows Spark Development

This repository uses two execution environments for different purposes:

| Environment | Purpose |
|---|---|
| Windows 11 | Local development, unit tests, linting, and lightweight validation |
| Amazon Linux 2023 on AWS EC2 | Spark integration testing and large-scale AWS benchmarks |

## Tested local stack

- Python 3.11
- PySpark 3.5.3
- Java 17
- Hadoop client libraries bundled with PySpark

Use the `portfolio311` Conda environment or another Python 3.11 environment. The AWS benchmark environment also uses Python 3.11.

## Install dependencies

```powershell
conda activate portfolio311
python -m pip install -r requirements.txt
```

Verify:

```powershell
python --version
python -c "import pyspark; print(pyspark.__version__)"
java -version
```

Expected versions are Python 3.11.x, PySpark 3.5.3, and Java 17.x.

## Configure PySpark Python

Spark needs to launch Python workers using the same interpreter as the active environment:

```powershell
$pythonPath = (python -c "import sys; print(sys.executable)").Trim()
$env:PYSPARK_PYTHON = $pythonPath
$env:PYSPARK_DRIVER_PYTHON = $pythonPath
```

## Windows Hadoop native support

Some local Spark filesystem operations use Hadoop's Windows native filesystem integration. A matching `winutils.exe` may be required on Windows. Keep it outside the repository; do not commit the executable.

Example environment setup:

```powershell
$env:HADOOP_HOME = "$env:USERPROFILE\hadoop-3.3.4"
$env:Path = "$env:HADOOP_HOME\bin;$env:Path"
```

If Spark reports `NativeIO$Windows.access0`, verify that `winutils.exe` exists at:

```text
%HADOOP_HOME%\bin\winutils.exe
```

The repository does not depend on a Windows Hadoop binary for AWS execution.

## Local validation

Run the Python test suite:

```powershell
python -m pytest -q
```

Run linting:

```powershell
ruff check src tests dags scripts
```

Validate the Airflow DAG syntax:

```powershell
python -m py_compile .\dags\healthcare_pipeline.py
```

## Sample Spark workflow

The ingestion generator writes a Parquet dataset directory rather than a single manifest file:

```powershell
python -m src.ingestion.generate_data `
  --rows 10000 `
  --chunk-size 10000 `
  --output data/sample/events.parquet
```

The resulting path contains one or more Parquet part files and can be supplied directly to Spark:

```powershell
spark-submit src/transformations/silver.py `
  --input data/sample/events.parquet `
  --output data/sample/silver
```

## Why AWS is the reference Spark environment

Windows-specific filesystem and native Hadoop differences can affect local Spark execution. The project's measured distributed benchmarks were executed on Amazon Linux using Spark 3.5.3 and Python 3.11 through AWS Systems Manager, with Parquet results written to Amazon S3.

The AWS environment is therefore the reference environment for integration and performance measurements, while Windows remains a convenient development environment for code and tests.