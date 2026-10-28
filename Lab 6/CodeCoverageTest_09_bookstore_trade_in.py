import pytest

from bookstore_trade_in import (
    process_book_buybacks,
    inspect_scanner_calibration,
)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        process_book_buybacks("invalid", 5)

    with pytest.raises(ValueError):
        process_book_buybacks([], -1)


def test_empty_and_unapproved_batches():
    assert process_book_buybacks([], 5)["status"] == "ZERO_CREDIT"

    batches = [{"intake_approved": False}]
    assert process_book_buybacks(batches, 5)["status"] == "ZERO_CREDIT"


def test_all_book_formats_and_conditions():
    batches = [
        {
            "intake_approved": True,
            "format": "textbook",
            "books": [
                {"condition": "mint"},
                {"condition": "poor"},
                {"condition": "good"},
            ],
        },
        {
            "intake_approved": True,
            "format": "hardcover",
            "books": [
                {"condition": "mint"},
                {"condition": "poor"},
            ],
        },
        {
            "intake_approved": True,
            "format": "paperback",
            "books": [
                {"condition": "mint"},
                {"condition": "poor"},
            ],
        },
    ]

    result = process_book_buybacks(batches, 5)
    assert result["total_payout"] == 143.95
    assert result["status"] == "COMPLETED"


def test_default_values_and_missing_pages():
    batches = [
        {
            "intake_approved": True,
            "books": [{}, {"missing_pages": 2}],
        }
    ]

    result = process_book_buybacks(batches, 5)
    assert result["total_payout"] == 8
    assert result["status"] == "COMPLETED"


def test_unknown_format():
    batches = [
        {"intake_approved": True, "format": "unknown", "books": []}
    ]

    result = process_book_buybacks(batches, 5)
    assert result["status"] == "ZERO_CREDIT"


def test_counterfeit_textbook_cancels_batch_credit():
    batches = [
        {
            "intake_approved": True,
            "format": "textbook",
            "books": [
                {"condition": "mint"},
                {"counterfeit": True},
                {"condition": "good"},
            ],
        }
    ]

    result = process_book_buybacks(batches, 5)
    assert result["total_payout"] == 0
    assert result["status"] == "ZERO_CREDIT"


def test_counterfeit_non_textbook():
    batches = [
        {
            "intake_approved": True,
            "format": "paperback",
            "books": [{"counterfeit": True}, {"condition": "good"}],
        }
    ]

    result = process_book_buybacks(batches, 5)
    assert result["total_payout"] == 8
    assert result["status"] == "COMPLETED"


def test_store_credit_bonus():
    batches = [
        {
            "intake_approved": True,
            "format": "paperback",
            "payout_in_credit": True,
            "books": [{"condition": "good"}],
        }
    ]

    result = process_book_buybacks(batches, 5)
    assert result["total_payout"] == 13


def test_audit_rejected():
    batches = [
        {"intake_approved": True, "format": "unknown"}
        for _ in range(5)
    ]

    result = process_book_buybacks(batches, 5)
    assert result["status"] == "AUDIT_REJECTED"


def test_scanner_no_data():
    assert inspect_scanner_calibration([]) == "NO_DATA"
    assert inspect_scanner_calibration(None) == "NO_DATA"


def test_scanner_recalibration():
    assert inspect_scanner_calibration([[6, 7]]) == "RECALIBRATE"


def test_scanner_calibrated_and_streak_reset():
    assert inspect_scanner_calibration([[6, 5, 7]]) == "CALIBRATED"
    assert inspect_scanner_calibration([[1, 2, 3]]) == "CALIBRATED"


def test_scanner_separate_devices():
    assert inspect_scanner_calibration([[6], [7]]) == "CALIBRATED"
