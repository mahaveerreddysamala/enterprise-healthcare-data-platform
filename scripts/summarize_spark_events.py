"""Summarize one uncompressed Spark event log; do not infer a cluster from partitions."""
import argparse
import json
from pathlib import Path


def summarize(events):
    hosts, executors = set(), set()
    failed_tasks = retried_tasks = removed = failed_jobs = 0
    started = ended = None
    for event in events:
        kind = event.get("Event")
        if kind == "SparkListenerApplicationStart":
            if started is not None:
                raise ValueError("Supply exactly one application event log")
            started = event["Timestamp"]
        elif kind == "SparkListenerApplicationEnd":
            ended = event["Timestamp"]
        elif kind == "SparkListenerExecutorAdded" and event["Executor ID"] != "driver":
            executors.add(event["Executor ID"])
            hosts.add(event["Executor Info"]["Host"])
        elif kind == "SparkListenerExecutorRemoved":
            removed += 1
        elif kind == "SparkListenerTaskEnd":
            failed_tasks += event["Task End Reason"].get("Reason") != "Success"
            retried_tasks += event["Task Info"].get("Attempt", 0) > 0
        elif kind == "SparkListenerJobEnd":
            failed_jobs += event["Job Result"].get("Result") != "JobSucceeded"
    return {"executor_hosts": sorted(hosts), "executor_count": len(executors),
            "multiple_executor_hosts_observed": len(hosts) >= 2,
            "executor_removals": removed, "non_success_task_ends": failed_tasks,
            "task_attempts_above_zero": retried_tasks, "failed_jobs": failed_jobs,
            "application_ended": ended is not None,
            "application_seconds": (ended - started) / 1000
                if ended is not None and started is not None else None,
            "limits": "Hosts are reported identities, not proof of separate physical machines; "
                      "higher task attempts may include speculation. An ended app can still fail."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("event_log", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/spark-execution.json"))
    parser.add_argument("--require-multiple-hosts", action="store_true")
    parser.add_argument("--allocated-hourly-cost", type=float)
    args = parser.parse_args()
    with args.event_log.open() as source:
        result = summarize(json.loads(line) for line in source if line.strip())
    if args.allocated_hourly_cost is not None:
        if args.allocated_hourly_cost < 0:
            parser.error("Cost rate must be nonnegative")
        result["allocated_hourly_cost"] = args.allocated_hourly_cost
        result["application_compute_cost_estimate"] = (
            args.allocated_hourly_cost * result["application_seconds"] / 3600
            if result["application_seconds"] is not None else None)
        result["cost_exclusions"] = "Provisioning/idle time, storage, network, tax and service fees"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.require_multiple_hosts and not result["multiple_executor_hosts_observed"]:
        raise SystemExit("Multiple executor hosts were not observed; report preserved")


if __name__ == "__main__":
    main()
