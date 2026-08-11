"""Tests for kb.metadata — regex + override table metadata extraction from Vietnamese doc headers."""

from __future__ import annotations

from kb.metadata import parse_metadata_line

# ---------------------------------------------------------------------------
# POL-01 v2 — full metadata line with supersession signal
# ---------------------------------------------------------------------------

POL01_V2_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · Thay thế phiên bản trước"

POL01_V1_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 1.0 · Ban hành: 06/2025"

FAQ01_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 07/2026"

SOP01_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 03/2026 · Người duyệt: Trưởng phòng Vận hành"

POL02_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 1.1 · Ban hành: 02/2026"

GUIDE01_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 06/2026"

RUN01_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 05/2026"

SOP02_LINE = "**Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 04/2026"


def test_pol01_v2_version_extracted() -> None:
    """POL-01 v2 bold line yields version '2.0'."""
    meta = parse_metadata_line(POL01_V2_LINE)
    assert meta["version"] == "2.0"


def test_pol01_v2_effective_date_extracted() -> None:
    """POL-01 v2 bold line yields effective_date '2026-05'."""
    meta = parse_metadata_line(POL01_V2_LINE)
    assert meta["effective_date"] == "2026-05"


def test_pol01_v2_department_extracted() -> None:
    """POL-01 v2 bold line yields department containing 'CNTT'."""
    meta = parse_metadata_line(POL01_V2_LINE)
    assert meta["department"] is not None
    assert "CNTT" in meta["department"]


def test_pol01_v2_supersedes_previous_detected() -> None:
    """POL-01 v2 bold line sets supersedes_previous=True."""
    meta = parse_metadata_line(POL01_V2_LINE)
    assert meta["supersedes_previous"] is True


def test_pol01_v2_approver_is_none() -> None:
    """POL-01 v2 bold line has no 'Người duyệt' field — approver is None."""
    meta = parse_metadata_line(POL01_V2_LINE)
    assert meta["approver"] is None


def test_pol01_v1_version_extracted() -> None:
    """POL-01 v1 bold line yields version '1.0'."""
    meta = parse_metadata_line(POL01_V1_LINE)
    assert meta["version"] == "1.0"


def test_pol01_v1_effective_date_extracted() -> None:
    """POL-01 v1 bold line yields effective_date '2025-06'."""
    meta = parse_metadata_line(POL01_V1_LINE)
    assert meta["effective_date"] == "2025-06"


def test_pol01_v1_no_supersession() -> None:
    """POL-01 v1 bold line does not contain the supersession phrase."""
    meta = parse_metadata_line(POL01_V1_LINE)
    assert meta["supersedes_previous"] is False


def test_pol01_v1_approver_none() -> None:
    """POL-01 v1 has no approver field."""
    meta = parse_metadata_line(POL01_V1_LINE)
    assert meta["approver"] is None


def test_faq01_no_version() -> None:
    """FAQ-01 line has no Phiên bản field — version is None."""
    meta = parse_metadata_line(FAQ01_LINE)
    assert meta["version"] is None


def test_faq01_effective_date_from_cap_nhat() -> None:
    """FAQ-01 uses 'Cập nhật: MM/YYYY' — effective_date is '2026-07'."""
    meta = parse_metadata_line(FAQ01_LINE)
    assert meta["effective_date"] == "2026-07"


def test_faq01_approver_is_none() -> None:
    """FAQ-01 has no approver field."""
    meta = parse_metadata_line(FAQ01_LINE)
    assert meta["approver"] is None


def test_sop01_approver_extracted() -> None:
    """SOP-01 bold line with 'Người duyệt: Trưởng phòng Vận hành' yields approver string."""
    meta = parse_metadata_line(SOP01_LINE)
    assert meta["approver"] is not None
    assert "Trưởng phòng Vận hành" in meta["approver"]


def test_sop01_effective_date() -> None:
    """SOP-01 uses 'Ban hành: 03/2026' — effective_date is '2026-03'."""
    meta = parse_metadata_line(SOP01_LINE)
    assert meta["effective_date"] == "2026-03"


def test_sop01_no_version() -> None:
    """SOP-01 has no Phiên bản field — version is None."""
    meta = parse_metadata_line(SOP01_LINE)
    assert meta["version"] is None


def test_pol02_version_with_minor() -> None:
    """POL-02 'Phiên bản 1.1' is extracted correctly."""
    meta = parse_metadata_line(POL02_LINE)
    assert meta["version"] == "1.1"


def test_guide01_no_approver() -> None:
    """GUIDE-01 has no approver."""
    meta = parse_metadata_line(GUIDE01_LINE)
    assert meta["approver"] is None


def test_guide01_effective_date() -> None:
    """GUIDE-01 'Cập nhật: 06/2026' → effective_date '2026-06'."""
    meta = parse_metadata_line(GUIDE01_LINE)
    assert meta["effective_date"] == "2026-06"


def test_run01_effective_date() -> None:
    """RUN-01 'Cập nhật: 05/2026' → effective_date '2026-05'."""
    meta = parse_metadata_line(RUN01_LINE)
    assert meta["effective_date"] == "2026-05"


def test_sop02_effective_date() -> None:
    """SOP-02 'Ban hành: 04/2026' → effective_date '2026-04'."""
    meta = parse_metadata_line(SOP02_LINE)
    assert meta["effective_date"] == "2026-04"


def test_no_supersession_on_sop02() -> None:
    """SOP-02 has no supersession phrase."""
    meta = parse_metadata_line(SOP02_LINE)
    assert meta["supersedes_previous"] is False


def test_all_keys_present() -> None:
    """parse_metadata_line always returns all expected keys."""
    expected_keys = {"version", "effective_date", "department", "approver", "supersedes_previous"}
    meta = parse_metadata_line(FAQ01_LINE)
    assert set(meta.keys()) >= expected_keys
