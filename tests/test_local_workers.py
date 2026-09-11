import pytest

from scripts.run_local_workers import retry_evidence, run_experiment


def task(stage, partition, attempt, reason, description=''):
    return {'Event': 'SparkListenerTaskEnd', 'Stage ID': stage,
            'Task Info': {'Index': partition, 'Attempt': attempt},
            'Task End Reason': {'Reason': reason, 'Description': description}}


def test_retry_requires_same_stage_partition_and_success():
    failed = task(0, 0, 0, 'ExceptionFailure', 'controlled-local-task-failure')
    unrelated = [task(1, 0, 1, 'Success'), task(0, 1, 1, 'Success'),
                 task(0, 0, 1, 'ExceptionFailure')]
    assert retry_evidence([failed, *unrelated]) == []
    matched = retry_evidence([failed, *unrelated, task(0, 0, 1, 'Success')])
    assert matched[0]['successful_attempt'] == 1


def test_existing_output_is_preserved(tmp_path):
    existing = tmp_path / 'important.txt'
    existing.write_text('keep')
    with pytest.raises(ValueError, match='fresh output'):
        run_experiment(tmp_path)
    assert existing.read_text() == 'keep'
