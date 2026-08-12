"""Fixture integrity tests for design.cases.CASES."""

from design.cases import CASES


def test_cases_count() -> None:
    assert len(CASES) == 5


def test_case_ids_are_unique() -> None:
    ids = [c.case_id for c in CASES]
    assert len(ids) == len(set(ids))


def test_all_cases_have_required_fields() -> None:
    required_expected_keys = {"event_type", "component", "parameters", "confidence", "parse_status"}
    for case in CASES:
        assert case.case_id, f"{case.case_id} has empty case_id"
        assert case.message, f"{case.case_id} has empty message"
        assert case.note, f"{case.case_id} has empty note"
        assert set(case.expected.keys()) == required_expected_keys, (
            f"{case.case_id} expected keys mismatch: {set(case.expected.keys())}"
        )


def test_confidence_values_are_valid() -> None:
    valid = {"high", "medium", "low"}
    for case in CASES:
        assert case.expected["confidence"] in valid, (
            f"{case.case_id} confidence={case.expected['confidence']!r} not in {valid}"
        )


def test_parse_status_values_are_valid() -> None:
    valid = {"success", "partial", "failed"}
    for case in CASES:
        assert case.expected["parse_status"] in valid, (
            f"{case.case_id} parse_status={case.expected['parse_status']!r} not in {valid}"
        )


def test_specific_case_ids() -> None:
    ids = {c.case_id for c in CASES}
    assert ids == {"tc01", "tc02", "tc03", "tc04", "tc05"}
