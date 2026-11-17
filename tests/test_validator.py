
import pandas as pd
import pytest

from src.validator import validate_records


def test_valid_records_are_accepted():

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", "Priya"],
        "amount": [1500, 2500],
        "city": ["Delhi", "Mumbai"]
    })

    valid, rejected = validate_records(df)

    assert len(valid) == 2
    assert len(rejected) == 0


def test_missing_values_are_rejected():

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", None],
        "amount": [1500, 2500],
        "city": ["Delhi", "Mumbai"]
    })

    valid, rejected = validate_records(df)

    assert len(valid) == 1
    assert len(rejected) == 1

    assert "missing_customer_name" in rejected.iloc[0]["error_reason"]


def test_non_numeric_amount_is_rejected():

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", "Priya"],
        "amount": [1500, "ABC"],
        "city": ["Delhi", "Mumbai"]
    })

    valid, rejected = validate_records(df)

    assert len(valid) == 1
    assert len(rejected) == 1

    assert "non_numeric_amount" in rejected.iloc[0]["error_reason"]


def test_missing_required_column_raises_error():

    df = pd.DataFrame({
        "record_id": [1],
        "customer_name": ["Rahul"],
        "amount": [1500]
    })

    with pytest.raises(ValueError, match="Missing required columns"):
        validate_records(df)


def test_original_dataframe_remains_unchanged():

    df = pd.DataFrame({
        "record_id": [1, 2],
        "customer_name": ["Rahul", "Priya"],
        "amount": [1500, "ABC"],
        "city": ["Delhi", "Mumbai"]
    })

    original = df.copy(deep=True)

    validate_records(df)

    pd.testing.assert_frame_equal(df, original)


def test_mixed_dataset_returns_expected_counts():

    df = pd.read_csv("data/source/input_data.csv")

    valid, rejected = validate_records(df)

    assert len(df) == 10
    assert len(valid) == 5
    assert len(rejected) == 5

    assert valid["amount"].dtype.kind in "if"
