"""Predeclared evaluation cases for the version-aware knowledge base.

Ten cases covering four question types as specified in KB-07 and KB-08:
  - direct_lookup (4): single-document factual retrieval
  - multi_source (3): synthesis across ≥2 documents
  - version_trap (2): POL-01 v1/v2 supersession proof
  - out_of_scope (1): question with no answer in the supplied documents

Each EvalCase carries:
  - question: the natural-language query (Vietnamese, matching document language)
  - question_type: one of the four types above
  - query_terms: key terms to pass to the FTS5 search function
  - search_mode: "current" (is_current=1 filter) or "all" (no filter)
  - expected_sources: list of (doc_id, section) tuples that should appear in results
  - expected_answer_keywords: specific words or phrases that must appear in retrieved
    content to demonstrate groundedness
  - pass_criteria: conditions under which the retrieval is scored as "pass"
  - partial_criteria: conditions for "partial"
  - fail_criteria: conditions for "fail"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    """A predeclared evaluation question with expected answer metadata.

    Fields
    ------
    case_id
        Short identifier, e.g. "Q01".
    question
        Full natural-language question in Vietnamese.
    question_type
        One of: direct_lookup | multi_source | version_trap | out_of_scope.
    query_terms
        Vietnamese terms to submit to the FTS5 search function.
    search_mode
        "current" for is_current=1 only; "all" for all versions including superseded.
    expected_sources
        List of (doc_id, section) pairs that should appear in top-k results.
    expected_answer_keywords
        Specific words or phrases that must appear in retrieved content.
    pass_criteria
        Human-readable description of the pass condition.
    partial_criteria
        Human-readable description of the partial condition.
    fail_criteria
        Human-readable description of the fail condition.
    """

    case_id: str
    question: str
    question_type: str  # direct_lookup | multi_source | version_trap | out_of_scope
    query_terms: str
    search_mode: str  # current | all
    expected_sources: tuple[tuple[str, str], ...]
    expected_answer_keywords: tuple[str, ...]
    pass_criteria: str
    partial_criteria: str
    fail_criteria: str


# ---------------------------------------------------------------------------
# Direct-lookup cases (Q01–Q04)
# Single-document factual retrieval — the answer lives in one chunk.
# ---------------------------------------------------------------------------

_Q01 = EvalCase(
    case_id="Q01",
    question="Thời gian sao lưu dữ liệu theo chính sách hiện hành là mấy giờ?",
    question_type="direct_lookup",
    query_terms="sao lưu",
    search_mode="current",
    expected_sources=(("POL-01", "Quy định"),),
    expected_answer_keywords=("23:30",),
    pass_criteria="Top-k contains a POL-01 v2 chunk (Quy định) with '23:30'.",
    partial_criteria="POL-01 v2 appears in results but the backup time is not in the snippet.",
    fail_criteria="No POL-01 v2 chunk appears, or only superseded v1 is returned.",
)

_Q02 = EvalCase(
    case_id="Q02",
    question="Ngưỡng CRITICAL của tỉ lệ ERROR trong 15 phút là bao nhiêu?",
    question_type="direct_lookup",
    query_terms="ngưỡng",
    search_mode="current",
    expected_sources=(("GUIDE-01", "Ngưỡng cảnh báo hiện hành"),),
    expected_answer_keywords=("5%",),
    pass_criteria="Top-k contains GUIDE-01 Ngưỡng cảnh báo chunk with '>5%' or '5%'.",
    partial_criteria="GUIDE-01 appears but the specific CRITICAL threshold is not visible.",
    fail_criteria="No GUIDE-01 chunk appears in top-k.",
)

_Q03 = EvalCase(
    case_id="Q03",
    question="Khi nào phải escalation lên cấp 3?",
    question_type="direct_lookup",
    query_terms="escalation",
    search_mode="current",
    expected_sources=(("SOP-02", "Luồng escalation"),),
    expected_answer_keywords=("P1", "P2", "4"),
    pass_criteria=(
        "Top-k contains SOP-02 Luồng escalation chunk with Level-3 trigger conditions "
        "(P1 any time, or P2 unresolved after 4 hours)."
    ),
    partial_criteria="SOP-02 appears but Level-3 specific conditions are absent from snippet.",
    fail_criteria="No SOP-02 escalation chunk appears.",
)

_Q04 = EvalCase(
    case_id="Q04",
    question="Job batch-report chạy lúc mấy giờ hàng ngày?",
    question_type="direct_lookup",
    query_terms="lịch chạy",
    search_mode="current",
    expected_sources=(("RUN-01", "Lịch chạy"),),
    expected_answer_keywords=("23:00",),
    pass_criteria="Top-k contains RUN-01 Lịch chạy chunk with '23:00'.",
    partial_criteria="RUN-01 appears but schedule time is not in the snippet.",
    fail_criteria="No RUN-01 chunk appears in top-k.",
)

# ---------------------------------------------------------------------------
# Multi-source synthesis cases (Q05–Q07)
# Answering fully requires information from ≥2 distinct doc_id sources.
# ---------------------------------------------------------------------------

_Q05 = EvalCase(
    case_id="Q05",
    question="Khi payment-api gặp lỗi HTTP 502, quy trình xử lý gồm những bước nào?",
    question_type="multi_source",
    query_terms="502",
    search_mode="current",
    expected_sources=(
        ("FAQ-01", "3. `ERR HTTP 502 upstream=payment-api`"),
        ("SOP-01", "Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước)"),
    ),
    expected_answer_keywords=("payment-api", "502"),
    pass_criteria=(
        "Top-k contains chunks from both FAQ-01 §3 and SOP-01 §Quy trình, "
        "enabling synthesis of root-cause diagnosis and restart procedure."
    ),
    partial_criteria=(
        "Only one of FAQ-01 or SOP-01 appears, providing partial procedure coverage. "
        "This is an expected limitation of single-query FTS5 lexical retrieval."
    ),
    fail_criteria="Neither FAQ-01 nor SOP-01 appears in top-k results.",
)

_Q06 = EvalCase(
    case_id="Q06",
    question="Yêu cầu bảo mật khi truy cập cơ sở dữ liệu production là gì?",
    question_type="multi_source",
    query_terms="log",
    search_mode="current",
    expected_sources=(
        ("POL-02", "Quy định chung"),
        ("GUIDE-01", "Quy ước log"),
    ),
    expected_answer_keywords=("DBA", "log"),
    pass_criteria=(
        "Top-k contains POL-02 Quy định chung (access control rules) and GUIDE-01 "
        "Quy ước log (monitoring/audit coverage), together covering who can access "
        "and how access is logged."
    ),
    partial_criteria=(
        "Only POL-02 or only GUIDE-01 appears, providing partial security coverage. "
        "This is an expected limitation of single-query FTS5 lexical retrieval."
    ),
    fail_criteria="Neither POL-02 access policy nor GUIDE-01 log chunk appears.",
)

_Q07 = EvalCase(
    case_id="Q07",
    question="Quy trình xử lý khi job báo cáo cuối ngày lỗi NullPointer?",
    question_type="multi_source",
    query_terms="NullPointer",
    search_mode="current",
    expected_sources=(
        ("RUN-01", "Khi job lỗi (`ERR NullPointer in ReportBuilder`)"),
        ("FAQ-01", "4. `ERR NullPointer in ReportBuilder`"),
    ),
    expected_answer_keywords=("NullPointer",),
    pass_criteria=(
        "Top-k contains chunks from both RUN-01 §Khi job lỗi and FAQ-01 §4, "
        "covering both the runbook re-run steps and the error context."
    ),
    partial_criteria=("Only one of RUN-01 or FAQ-01 appears — partial procedure coverage."),
    fail_criteria="Neither RUN-01 nor FAQ-01 NullPointer chunk appears in top-k.",
)

# ---------------------------------------------------------------------------
# Version-trap cases (Q08–Q09)
# Prove that current-policy search returns v2 and excludes v1, and that
# historical search can retrieve both for comparison.
# ---------------------------------------------------------------------------

_Q08 = EvalCase(
    case_id="Q08",
    question="Thời gian lưu giữ bản sao lưu theo chính sách hiện hành là bao lâu?",
    question_type="version_trap",
    query_terms="lưu trữ",
    search_mode="current",
    expected_sources=(("POL-01", "Quy định"),),
    expected_answer_keywords=("30",),
    pass_criteria=(
        "Top-k (current-mode) contains POL-01 v2 Quy định chunk with '30 ngày'. "
        "POL-01 v1 (answer: 7 ngày) must NOT be the top result."
    ),
    partial_criteria=(
        "POL-01 v2 appears in results but the retention period value is not in snippet."
    ),
    fail_criteria=(
        "No POL-01 v2 chunk appears, or only superseded POL-01 v1 is returned, "
        "incorrectly implying 7 ngày retention."
    ),
)

_Q09 = EvalCase(
    case_id="Q09",
    question="So sánh chính sách sao lưu phiên bản cũ và phiên bản mới khác nhau thế nào?",
    question_type="version_trap",
    query_terms="sao lưu",
    search_mode="all",
    expected_sources=(
        ("POL-01", "Quy định"),  # appears twice: v1 and v2 both expected
    ),
    expected_answer_keywords=("22:00", "23:30", "7", "30"),
    pass_criteria=(
        "Top-k (all-versions mode) contains POL-01 v1 Quy định AND POL-01 v2 Quy định "
        "chunks, enabling direct comparison of old vs new retention/schedule values."
    ),
    partial_criteria=("Only one version of POL-01 Quy định appears — cannot perform comparison."),
    fail_criteria="No POL-01 chunk appears in top-k at all.",
)

# ---------------------------------------------------------------------------
# Out-of-scope case (Q10)
# The question asks about information genuinely absent from all 8 documents.
# ---------------------------------------------------------------------------

_Q10 = EvalCase(
    case_id="Q10",
    question="Chi phí hàng tháng cho dịch vụ cloud backup là bao nhiêu?",
    question_type="out_of_scope",
    query_terms="chi phí cloud backup",
    search_mode="current",
    expected_sources=(),  # no expected sources — information not in the KB
    expected_answer_keywords=(),
    pass_criteria=(
        "No relevant chunk is retrieved (empty result or all chunks are off-topic), "
        "and the diagnosis explicitly states the information is not in the supplied documents."
    ),
    partial_criteria="N/A — this case has no partial outcome; it is pass or fail.",
    fail_criteria=(
        "A chunk is incorrectly returned as relevant, or an invented cost figure appears "
        "in the diagnosis."
    ),
)

# ---------------------------------------------------------------------------
# Master list — 10 cases in declared order
# ---------------------------------------------------------------------------

EVAL_CASES: list[EvalCase] = [
    _Q01,  # direct_lookup
    _Q02,  # direct_lookup
    _Q03,  # direct_lookup
    _Q04,  # direct_lookup
    _Q05,  # multi_source
    _Q06,  # multi_source
    _Q07,  # multi_source
    _Q08,  # version_trap
    _Q09,  # version_trap
    _Q10,  # out_of_scope
]
