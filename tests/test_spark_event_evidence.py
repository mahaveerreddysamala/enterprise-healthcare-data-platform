from scripts.summarize_spark_events import summarize


def test_partitions_and_multiple_executors_do_not_prove_multiple_hosts():
    events = [{"Event": "SparkListenerExecutorAdded", "Executor ID": str(i),
               "Executor Info": {"Host": "same-host"}} for i in range(3)]
    result = summarize(events)
    assert result["executor_count"] == 3
    assert not result["multiple_executor_hosts_observed"]


def test_failure_and_retry_evidence_remains_visible():
    events = [
        {"Event": "SparkListenerApplicationStart", "Timestamp": 1000},
        {"Event": "SparkListenerTaskEnd", "Task End Reason": {"Reason": "ExceptionFailure"},
         "Task Info": {"Attempt": 0}},
        {"Event": "SparkListenerTaskEnd", "Task End Reason": {"Reason": "Success"},
         "Task Info": {"Attempt": 1}},
        {"Event": "SparkListenerApplicationEnd", "Timestamp": 3000},
    ]
    result = summarize(events)
    assert result["non_success_task_ends"] == 1
    assert result["task_attempts_above_zero"] == 1
    assert result["application_seconds"] == 2
