"""Run isolated Spark standalone workers on one Linux machine; no cloud resources."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler

import pyspark

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.summarize_spark_events import summarize


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def retry_evidence(events):
    tasks = [e for e in events if e.get("Event") == "SparkListenerTaskEnd"]
    failures = [e for e in tasks if "controlled-local-task-failure" in
                e.get("Task End Reason", {}).get("Description", "")]
    matched = []
    for failed in failures:
        for retried in tasks:
            if (retried["Stage ID"] == failed["Stage ID"]
                    and retried["Task Info"]["Index"] == failed["Task Info"]["Index"]
                    and retried["Task Info"]["Attempt"] > failed["Task Info"]["Attempt"]
                    and retried["Task End Reason"]["Reason"] == "Success"):
                matched.append({"stage": failed["Stage ID"], "partition": failed["Task Info"]["Index"],
                                "failed_attempt": failed["Task Info"]["Attempt"],
                                "successful_attempt": retried["Task Info"]["Attempt"],
                                "failure": "controlled-local-task-failure"})
    return matched


def run_experiment(output, rows=100000, workers=2, inject_failure=False):
    if rows <= 0 or workers not in (1, 2):
        raise ValueError("Use positive rows and one or two local workers")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a fresh output directory")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    events = output / "events"
    events.mkdir()
    spark_home = Path(pyspark.__file__).parent
    env = {**os.environ, "SPARK_LOCAL_IP": "127.0.0.1", "PYSPARK_PYTHON": sys.executable,
           "SPARK_DAEMON_MEMORY": "256m", "SPARK_MASTER_OPTS": "-Dspark.master.rest.enabled=false"}
    port, ui = free_port(), free_port()
    master = f"spark://127.0.0.1:{port}"
    processes, logs = [], []
    started = time.perf_counter()
    report = {"single_machine": True, "workers_requested": workers, "rows": rows,
              "injected_failure": inject_failure, "status": "running"}

    def launch(command, name):
        log = (output / f"{name}.log").open("w")
        logs.append(log)
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        processes.append(process)
        return process

    try:
        launch([str(spark_home / "bin/spark-class"), "org.apache.spark.deploy.master.Master",
                "--host", "127.0.0.1", "--port", str(port), "--webui-port", str(ui)], "master")
        for index in range(workers):
            launch([str(spark_home / "bin/spark-class"), "org.apache.spark.deploy.worker.Worker",
                    "--host", "127.0.0.1", "--port", str(free_port()),
                    "--webui-port", str(free_port()), "--cores", "1", "--memory", "1g",
                    "--work-dir", str(output / f"worker-{index}"), master], f"worker-{index}")
        opener = build_opener(ProxyHandler({}))
        deadline = time.monotonic() + 60
        while True:
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("Spark daemon exited; inspect logs")
            try:
                with opener.open(f"http://127.0.0.1:{ui}/json/", timeout=2) as response:
                    inventory = json.load(response)
                alive = [w for w in inventory["workers"] if w["state"] == "ALIVE"]
                if len(alive) == workers:
                    report["registered_workers"] = [{k: w[k] for k in ("id", "host", "cores", "memory")}
                                                      for w in alive]
                    break
            except (OSError, ValueError, KeyError):
                pass
            if time.monotonic() > deadline:
                raise TimeoutError("Workers did not register in 60 seconds")
            time.sleep(.5)
        command = [str(spark_home / "bin/spark-submit"), "--master", master,
                   "--executor-memory", "512m", "--driver-memory", "512m"]
        for key, value in {"spark.cores.max": workers, "spark.executor.cores": 1,
                           "spark.task.maxFailures": 2, "spark.speculation": "false",
                           "spark.driver.host": "127.0.0.1", "spark.driver.bindAddress": "127.0.0.1",
                           "spark.eventLog.enabled": "true", "spark.eventLog.compress": "false",
                           "spark.eventLog.rolling.enabled": "false",
                           "spark.eventLog.dir": events.as_uri()}.items():
            command.extend(["--conf", f"{key}={value}"])
        command.extend([str(Path(__file__).resolve().parents[1] / "benchmark/spark_healthcare_benchmark.py"),
                        "--rows", str(rows), "--partitions", "8", "--verify-output",
                        "--output", str(output / "data"), "--local-dir", str(output / "scratch"),
                        "--metrics-output", str(output / "metrics.json"),
                        "--report-output", str(output / "benchmark.md")])
        if inject_failure:
            command.append("--inject-task-failure")
        job = launch(command, "application")
        code = job.wait(timeout=240)
        if code:
            raise RuntimeError(f"Spark job exited {code}; inspect application.log")
        event_files = [p for p in events.iterdir() if p.is_file() and not p.name.startswith(".")
                       and not p.name.endswith(".inprogress")]
        if len(event_files) != 1:
            raise ValueError("Expected one completed Spark event log")
        with event_files[0].open() as source:
            recorded = [json.loads(line) for line in source if line.strip()]
        report["execution"] = summarize(recorded)
        report["recovered_tasks"] = retry_evidence(recorded)
        report["event_log_sha256"] = hashlib.sha256(event_files[0].read_bytes()).hexdigest()
        report["benchmark"] = json.loads((output / "metrics.json").read_text())
        evidence = report["execution"]
        if evidence["executor_count"] != workers or evidence["failed_jobs"]:
            raise ValueError("Expected worker executors and successful jobs were not observed")
        if not evidence["application_ended"]:
            raise ValueError("Application completion was not observed")
        if inject_failure and not report["recovered_tasks"]:
            raise ValueError("Injected failure and task retry were not observed")
        report["status"] = "passed"
        return report
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        for process in reversed(processes):
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        for log in logs:
            log.close()
        report["wall_seconds_including_startup_cleanup"] = round(time.perf_counter() - started, 3)
        (output / "execution.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=100000)
    parser.add_argument("--workers", type=int, choices=[1, 2], default=2)
    parser.add_argument("--inject-failure", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_experiment(args.output, args.rows, args.workers, args.inject_failure)
    print(json.dumps({"status": result["status"], "evidence": str(args.output / "execution.json")}))


if __name__ == "__main__":
    main()
