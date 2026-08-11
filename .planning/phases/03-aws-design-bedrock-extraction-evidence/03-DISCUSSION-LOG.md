# Phase 3: Discussion Log

**Date:** 2026-08-12
**Phase:** 03 — AWS Design & Bedrock Extraction Evidence
**Duration:** ~10 min
**Areas discussed:** 4/4

## Discussion Summary

### Area 1: AWS Diagram Tooling & Depth

**Options presented:**
- Diagram tool: Draw.io (recommended) / Mermaid / Both
- Diagram scope: Full flow with failure + IAM (recommended) / Happy path only

**User selected:** Draw.io + Full flow with failure + IAM

**Notes:** The brief explicitly requires services, data flow, and "điểm bạn chưa chắc." Draw.io gives better visual control for AWS service architecture without adding Node dependencies. Full flow + IAM directly addresses AWS-03 (IAM boundaries, failure handling, uncertainties).

---

### Area 2: Extraction Prompt Schema Design

**Options presented:**
- Scope: All levels (recommended) / ERROR only
- Schema shape: Flat with confidence (recommended) / Nested by category

**User selected:** All levels + Flat with confidence

**Notes:** The brief says "trường message" generically (not just ERROR) and requires "ca khó/mơ hồ" which likely involves non-ERROR interpretation. Flat schema matches the brief's stated output dimensions exactly: "loại lỗi, component liên quan, tham số."

---

### Area 3: Bedrock Preflight & Credential Safety

**Options presented:**
- Config shape: .env + os.environ (recommended) / Config file + env override
- Preflight: CLI command (recommended) / Integrated into trial
- Model choice: Fully configurable (recommended) / Default + override

**User selected:** .env + os.environ, CLI preflight command, Fully configurable

**Notes:** Matches RPRO-05 (no credentials committed) and AIEXT-06 (preflight before trial). Separate preflight allows reviewers to verify access without incurring inference costs.

---

### Area 4: Evaluation Method for 3,000 Lines

**Options presented:**
- Ground truth: Phase 1 output as baseline (recommended) / Independent manual annotation
- Eval structure: 3-tier schema+field+hallucination (recommended) / 2-tier automated+human

**User selected:** Phase 1 output as baseline + 3-tier evaluation

**Notes:** Leveraging Phase 1's verified regex normalization as ground truth is efficient and credible. Three-tier evaluation directly addresses all three elements the brief asks for: "tiêu chí đo" (schema + field metrics), "làm sao phát hiện bịa" (hallucination tier), "khi nào cần người kiểm tra" (human-review triggers).

---

## Deferred Ideas

None — all discussion stayed within Phase 3 scope.

## Agent's Discretion Items

- Exact 5 test-case message selections (planner picks for coverage)
- Internal module layout of `design/` Python code
- File layout within `design/output/` for trial artifacts
- Wording of AI response review (flexible per claim structure)
