
import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

from src.validator import validate_records
from src.logger_config import setup_logger
from src.notifier import (
    notify_success,
    notify_partial_failure,
    notify_failure
)


# Project directories
BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_FILE = BASE_DIR / "data" / "source" / "input_data.csv"
DESTINATION_FILE = BASE_DIR / "data" / "destination" / "processed_data.csv"

LOG_FILE = BASE_DIR / "logs" / "skipped_records.csv"
REPORT_FILE = BASE_DIR / "reports" / "execution_report.json"


def run_pipeline():

    logger = setup_logger()

    start_time = datetime.now(timezone.utc)

    # Create required directories
    DESTINATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting fault-tolerant data pipeline")

    try:

        # Step 1: Read source data
        logger.info("Reading source CSV: %s", SOURCE_FILE)

        source_data = pd.read_csv(SOURCE_FILE)

        total_records = len(source_data)

        logger.info("Source records loaded: %s", total_records)

        # Step 2: Validate records
        logger.info("Starting record validation")

        valid_records, rejected_records = validate_records(
            source_data
        )

        successful_records = len(valid_records)
        skipped_records = len(rejected_records)

        logger.info(
            "Validation completed: %s valid, %s rejected",
            successful_records,
            skipped_records
        )

        # Step 3: Copy valid records
        valid_records.to_csv(
            DESTINATION_FILE,
            index=False
        )

        logger.info(
            "Valid records copied to: %s",
            DESTINATION_FILE
        )

        # Step 4: Log rejected records
        rejected_records.to_csv(
            LOG_FILE,
            index=False
        )

        logger.info(
            "Rejected records saved to: %s",
            LOG_FILE
        )

        if skipped_records > 0:

            logger.warning(
                "%s incompatible or incomplete records were skipped",
                skipped_records
            )

        # Step 5: Determine pipeline status
        pipeline_status = (
            "SUCCESS_WITH_SKIPS"
            if skipped_records > 0
            else "SUCCESS"
        )

        end_time = datetime.now(timezone.utc)

        # Step 6: Generate execution report
        report = {
            "pipeline_name": "fault_tolerance_pipeline",
            "status": pipeline_status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_records": total_records,
            "successful_records": successful_records,
            "skipped_records": skipped_records,
            "success_rate_percent": round(
                successful_records / total_records * 100, 2
            ) if total_records else 0,
            "source_file": str(SOURCE_FILE),
            "destination_file": str(DESTINATION_FILE),
            "skipped_records_log": str(LOG_FILE)
        }

        REPORT_FILE.write_text(
            json.dumps(report, indent=4),
            encoding="utf-8"
        )

        logger.info(
            "Execution report generated: %s",
            REPORT_FILE
        )

        logger.info(
            "Pipeline completed with status: %s",
            pipeline_status
        )

        # Step 7: Trigger appropriate alert notification
        alert_details = {
            "total_records": total_records,
            "successful_records": successful_records,
            "skipped_records": skipped_records,
            "pipeline_status": pipeline_status
        }

        if skipped_records > 0:

            notify_partial_failure(alert_details)

        else:

            notify_success(alert_details)

        # Step 8: Print execution summary
        print("\nPIPELINE EXECUTION SUMMARY")
        print("--------------------------------")
        print("Status:", pipeline_status)
        print("Total records:", total_records)
        print("Successful records:", successful_records)
        print("Skipped records:", skipped_records)

        print(
            "Success rate:",
            report["success_rate_percent"],
            "%"
        )

        print("\nOUTPUT FILES")
        print("--------------------------------")
        print("Destination:", DESTINATION_FILE)
        print("Skipped records log:", LOG_FILE)
        print("Execution report:", REPORT_FILE)

        return report

    except Exception as error:

        logger.exception("Pipeline execution failed")

        # Trigger failure notification
        notify_failure({
            "error": str(error),
            "pipeline_status": "FAILED"
        })

        # Generate failure report
        failure_report = {
            "pipeline_name": "fault_tolerance_pipeline",
            "status": "FAILED",
            "error": str(error),
            "start_time": start_time.isoformat(),
            "end_time": datetime.now(timezone.utc).isoformat()
        }

        REPORT_FILE.write_text(
            json.dumps(failure_report, indent=4),
            encoding="utf-8"
        )

        raise


if __name__ == "__main__":
    run_pipeline()
