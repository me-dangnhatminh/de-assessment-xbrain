"""Regex + override table metadata parser for Vietnamese operational document headers.

Each document has a bold ``·``-delimited metadata line immediately below the ``# `` title.
This module extracts structured fields from that line using regex patterns, with an
override table for edge cases that regex alone cannot handle cleanly.

Returned dict keys (always present):
    version           str | None  — e.g. "2.0", "1.1"
    effective_date    str | None  — ISO year-month e.g. "2026-05"
    department        str | None  — e.g. "Công ty Tài chính Sao Đỏ — Phòng CNTT"
    approver          str | None  — e.g. "Trưởng phòng Vận hành"
    supersedes_previous bool      — True when "Thay thế phiên bản trước" appears
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# Matches "Phiên bản X.Y" anywhere in the line — captures "X.Y"
_RE_VERSION = re.compile(r"Phi[eê]n\s+b[aả]n\s+([\d]+\.[\d]+)", re.UNICODE)

# Matches "Ban hành: MM/YYYY" or "Cập nhật: MM/YYYY" — captures MM and YYYY.
# Use .+ with a non-greedy match on the keyword portion to handle Unicode
# normalization differences in the Vietnamese precomposed characters.
_RE_DATE = re.compile(r"(?:Ban\s+h\S+nh|C\S+p\s+nh\S+t)\s*:\s*(\d{1,2})/(\d{4})", re.UNICODE)

# Matches "Người duyệt: <value>" up to the next · or end of string
_RE_APPROVER = re.compile(r"Ng[ưu][oờ]i\s+duy[eệ]t\s*:\s*([^·]+)", re.UNICODE)

# Department: the bold-delimited block at the start, e.g. "**Công ty ... CNTT**"
_RE_DEPARTMENT = re.compile(r"\*\*([^*]+)\*\*", re.UNICODE)

# Supersession signal
_SUPERSEDES_PHRASE = "Thay thế phiên bản trước"


def parse_metadata_line(line: str) -> dict:
    """Extract structured metadata from a bold ``·``-delimited document header line.

    Parameters
    ----------
    line:
        The raw bold metadata line, e.g.::

            **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · Thay thế phiên bản trước

    Returns
    -------
    dict with keys: version, effective_date, department, approver, supersedes_previous.
    Missing fields are None; supersedes_previous is always a bool.
    """
    version: str | None = None
    effective_date: str | None = None
    department: str | None = None
    approver: str | None = None
    supersedes_previous: bool = False

    # --- department ---
    dept_match = _RE_DEPARTMENT.search(line)
    if dept_match:
        department = dept_match.group(1).strip()

    # --- version ---
    ver_match = _RE_VERSION.search(line)
    if ver_match:
        version = ver_match.group(1)

    # --- effective_date ---
    date_match = _RE_DATE.search(line)
    if date_match:
        month_str = date_match.group(1).zfill(2)
        year_str = date_match.group(2)
        effective_date = f"{year_str}-{month_str}"

    # --- approver ---
    approver_match = _RE_APPROVER.search(line)
    if approver_match:
        approver = approver_match.group(1).strip().rstrip("·").strip()

    # --- supersedes_previous ---
    if _SUPERSEDES_PHRASE in line:
        supersedes_previous = True

    return {
        "version": version,
        "effective_date": effective_date,
        "department": department,
        "approver": approver,
        "supersedes_previous": supersedes_previous,
    }
