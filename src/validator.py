
import pandas as pd


REQUIRED_COLUMNS = [
    "record_id",
    "customer_name",
    "amount",
    "city"
]


def validate_records(df: pd.DataFrame):
    """
    Validate incoming records.

    Returns:
        valid_records: Records that pass all validation rules.
        rejected_records: Records that fail validation,
                          including their rejection reasons.
    """

    # Check whether all required columns exist
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Work on a copy to preserve the original DataFrame
    data = df.copy()

    # Convert amount into numeric format for validation
    numeric_amount = pd.to_numeric(
        data["amount"],
        errors="coerce"
    )

    # Store validation errors for each record
    errors = []

    for index, row in data.iterrows():

        record_errors = []

        # Validate record ID
        if pd.isna(row["record_id"]) or str(row["record_id"]).strip() == "":
            record_errors.append("missing_record_id")

        # Validate customer name
        if pd.isna(row["customer_name"]) or str(row["customer_name"]).strip() == "":
            record_errors.append("missing_customer_name")

        # Validate amount
        if pd.isna(row["amount"]) or str(row["amount"]).strip() == "":
            record_errors.append("missing_amount")

        elif pd.isna(numeric_amount.loc[index]):
            record_errors.append("non_numeric_amount")

        # Validate city
        if pd.isna(row["city"]) or str(row["city"]).strip() == "":
            record_errors.append("missing_city")

        errors.append(", ".join(record_errors))

    # Attach validation results
    data["error_reason"] = errors

    # Separate accepted and rejected records
    valid_records = data[
        data["error_reason"] == ""
    ].copy()

    rejected_records = data[
        data["error_reason"] != ""
    ].copy()

    # Convert accepted amounts into numeric values
    valid_records["amount"] = pd.to_numeric(
        valid_records["amount"]
    )

    # Return both datasets
    return valid_records.drop(columns=["error_reason"]), rejected_records
