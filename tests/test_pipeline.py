
import json
import logging

import pandas as pd

import src.pipeline as pipeline


def prepare_test_environment(tmp_path, monkeypatch):

    source_file = tmp_path / "source.csv"
    destination_file = tmp_path / "processed.csv"
    skipped_file = tmp_path / "skipped.csv"
    report_file = tmp_path / "report.json"

    # Redirect pipeline output to temporary directories
    monkeypatch.setattr(pipeline, "SOURCE_FILE", source_file)
    monkeypatch.setattr(pipeline, "DESTINATION_FILE", destination_file)
    monkeypatch.setattr(pipeline, "LOG_FILE", skipped_file)
    monkeypatch.setattr(pipeline, "REPORT_FILE", report_file)

    # Avoid writing test execution logs into the real project
    test_logger = logging.getLogger("test_pipeline")
    test_logger.handlers = []
    test_logger.propagate = False

    monkeypatch.setattr(
        pipeline,
        "setup_logger",
        lambda: test_logger
    )

    return source_file, destination_file, skipped_file, report_file


def test_pipeline_with_skipped_records(
    tmp_path, monkeypatch
):

    source, destination, skipped, report = prepare_test_environment(
        tmp_path, monkeypatch
    )

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", "Priya"],
        "amount": [1500, "ABC"],
        "city": ["Delhi", "Mumbai"]
    })

    df.to_csv(source, index=False)

    alert_calls = []

    monkeypatch.setattr(
        pipeline,
        "notify_partial_failure",
        lambda details: alert_calls.append(details)
    )

    monkeypatch.setattr(
        pipeline,
        "notify_success",
        lambda details: None
    )

    result = pipeline.run_pipeline()

    assert result["status"] == "SUCCESS_WITH_SKIPS"
    assert result["total_records"] == 2
    assert result["successful_records"] == 1
    assert result["skipped_records"] == 1

    assert len(pd.read_csv(destination)) == 1
    assert len(pd.read_csv(skipped)) == 1

    assert report.exists()
    assert len(alert_calls) == 1


def test_pipeline_without_skipped_records(
    tmp_path, monkeypatch
):

    source, destination, skipped, report = prepare_test_environment(
        tmp_path, monkeypatch
    )

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", "Priya"],
        "amount": [1500, 2500],
        "city": ["Delhi", "Mumbai"]
    })

    df.to_csv(source, index=False)

    success_calls = []

    monkeypatch.setattr(
        pipeline,
        "notify_success",
        lambda details: success_calls.append(details)
    )

    result = pipeline.run_pipeline()

    assert result["status"] == "SUCCESS"
    assert result["successful_records"] == 2
    assert result["skipped_records"] == 0

    assert len(pd.read_csv(destination)) == 2
    assert len(pd.read_csv(skipped)) == 0

    assert report.exists()
    assert len(success_calls) == 1


def test_pipeline_failure_triggers_error_alert(
    tmp_path, monkeypatch
):

    source, destination, skipped, report = prepare_test_environment(
        tmp_path, monkeypatch
    )

    # Deliberately do not create the source file
    failure_calls = []

    monkeypatch.setattr(
        pipeline,
        "notify_failure",
        lambda details: failure_calls.append(details)
    )

    try:
        pipeline.run_pipeline()
        assert False, "Expected pipeline execution to fail"

    except FileNotFoundError:
        pass

    assert len(failure_calls) == 1

    assert report.exists()

    failure_report = json.loads(
        report.read_text(encoding="utf-8")
    )

    assert failure_report["status"] == "FAILED"
