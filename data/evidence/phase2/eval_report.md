# KB Evaluation Report

**Generated:** 2026-08-12 12:58 UTC  
**Index:** `data/evidence/phase2/index.sqlite`  
**Top-k:** 5  
**Total cases:** 10

## Summary

| Retrieval Hit | Count |
|---|---|
| ✅ Pass | 9 |
| ⚠️ Partial | 1 |
| ❌ Fail | 0 |

| Question Type | Pass | Partial | Fail |
|---|---|---|---|
| direct_lookup | 4 | 0 | 0 |
| multi_source | 2 | 1 | 0 |
| version_trap | 2 | 0 | 0 |
| out_of_scope | 1 | 0 | 0 |

---

## Case Results

### Q01 — direct_lookup

**Question:** Thời gian sao lưu dữ liệu theo chính sách hiện hành là mấy giờ?

**Query submitted:** `sao lưu`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `POL-01` § Quy định

**Retrieved chunks (top 2):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `POL-01_2.0_chunk0` | ✅ | `-2.2292` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · T… |
| 2 | `POL-01_2.0_chunk1` | ✅ | `-2.1280` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · T… |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 1 keyword(s) present in retrieved content.

---

### Q02 — direct_lookup

**Question:** Ngưỡng CRITICAL của tỉ lệ ERROR trong 15 phút là bao nhiêu?

**Query submitted:** `ngưỡng`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `GUIDE-01` § Ngưỡng cảnh báo hiện hành

**Retrieved chunks (top 1):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `GUIDE-01_v0_chunk1` | ✅ | `-4.3639` | # GUIDE-01 — Hướng dẫn giám sát hệ thống  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 06/2026  ## Ngưỡng cảnh … |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 1 keyword(s) present in retrieved content.

---

### Q03 — direct_lookup

**Question:** Khi nào phải escalation lên cấp 3?

**Query submitted:** `escalation`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `SOP-02` § Luồng escalation

**Retrieved chunks (top 3):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `SOP-02_v0_chunk1` | ✅ | `-2.1809` | # SOP-02 — Quy trình escalation sự cố  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 04/2026  ## Luồng escalatio… |
| 2 | `SOP-01_v0_chunk2` | ✅ | `-1.9650` | # SOP-01 — Quy trình khởi động lại dịch vụ  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 03/2026 · Người duyệt:… |
| 3 | `SOP-02_v0_chunk0` | ✅ | `-1.4909` | # SOP-02 — Quy trình escalation sự cố  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 04/2026  ## Phân mức sự cố … |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 3 keyword(s) present in retrieved content.

---

### Q04 — direct_lookup

**Question:** Job batch-report chạy lúc mấy giờ hàng ngày?

**Query submitted:** `lịch chạy`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `RUN-01` § Lịch chạy

**Retrieved chunks (top 1):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `RUN-01_v0_chunk0` | ✅ | `-2.7945` | # RUN-01 — Runbook job báo cáo cuối ngày (batch-report)  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 05/2026  … |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 1 keyword(s) present in retrieved content.

---

### Q05 — multi_source

**Question:** Khi payment-api gặp lỗi HTTP 502, quy trình xử lý gồm những bước nào?

**Query submitted:** `502`  
**Search mode:** `current`

**Retrieval hit:** ⚠️ `partial`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `FAQ-01` § 3. `ERR HTTP 502 upstream=payment-api`
- `SOP-01` § Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước)

**Retrieved chunks (top 1):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `FAQ-01_v0_chunk2` | ✅ | `-2.8899` | # FAQ-01 — Các lỗi thường gặp và cách xử lý  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 07/2026  ## 3. `ERR H… |

**Diagnosis:**

> Retrieval hit PARTIAL: 1/2 expected source(s) found. Missing: ["('SOP-01', 'Quy trình chuẩn (theo thứ tự, KHÔNG bỏ bước)')"]. Groundedness PASS: all 2 keyword(s) present in retrieved content.

---

### Q06 — multi_source

**Question:** Yêu cầu bảo mật khi truy cập cơ sở dữ liệu production là gì?

**Query submitted:** `log`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `POL-02` § Quy định chung
- `GUIDE-01` § Quy ước log

**Retrieved chunks (top 4):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `GUIDE-01_v0_chunk2` | ✅ | `-2.0165` | # GUIDE-01 — Hướng dẫn giám sát hệ thống  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 06/2026  ## Quy ước log … |
| 2 | `GUIDE-01_v0_chunk1` | ✅ | `-1.5344` | # GUIDE-01 — Hướng dẫn giám sát hệ thống  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 06/2026  ## Ngưỡng cảnh … |
| 3 | `POL-02_1.1_chunk0` | ✅ | `-1.1736` | # POL-02 — Chính sách truy cập hệ thống  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 1.1 · Ban hành: 02/2026  … |
| 4 | `SOP-01_v0_chunk1` | ✅ | `-0.9885` | # SOP-01 — Quy trình khởi động lại dịch vụ  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Ban hành: 03/2026 · Người duyệt:… |

**Diagnosis:**

> Retrieval hit PASS: all 2 expected source(s) found in top-k. Groundedness PASS: all 2 keyword(s) present in retrieved content.

---

### Q07 — multi_source

**Question:** Quy trình xử lý khi job báo cáo cuối ngày lỗi NullPointer?

**Query submitted:** `NullPointer`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `RUN-01` § Khi job lỗi (`ERR NullPointer in ReportBuilder`)
- `FAQ-01` § 4. `ERR NullPointer in ReportBuilder`

**Retrieved chunks (top 2):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `FAQ-01_v0_chunk3` | ✅ | `-2.4217` | # FAQ-01 — Các lỗi thường gặp và cách xử lý  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 07/2026  ## 4. `ERR N… |
| 2 | `RUN-01_v0_chunk1` | ✅ | `-1.7243` | # RUN-01 — Runbook job báo cáo cuối ngày (batch-report)  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Cập nhật: 05/2026  … |

**Diagnosis:**

> Retrieval hit PASS: all 2 expected source(s) found in top-k. Groundedness PASS: all 1 keyword(s) present in retrieved content.

---

### Q08 — version_trap

**Question:** Thời gian lưu giữ bản sao lưu theo chính sách hiện hành là bao lâu?

**Query submitted:** `lưu trữ`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `POL-01` § Quy định

**Retrieved chunks (top 1):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `POL-01_2.0_chunk0` | ✅ | `-2.2697` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · T… |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 1 keyword(s) present in retrieved content. Version trap: POL-01 v2 (current) returned; superseded v1 correctly excluded.

---

### Q09 — version_trap

**Question:** So sánh chính sách sao lưu phiên bản cũ và phiên bản mới khác nhau thế nào?

**Query submitted:** `sao lưu`  
**Search mode:** `all`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Expected sources:**
- `POL-01` § Quy định

**Retrieved chunks (top 4):**

| Rank | chunk_id | is_current | bm25 | snippet |
|---|---|---|---|---|
| 1 | `POL-01_1.0_chunk0` | ⬛ superseded | `-2.3354` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 1.0 · Ban hành: 06/2025  ##… |
| 2 | `POL-01_2.0_chunk0` | ✅ | `-2.2292` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · T… |
| 3 | `POL-01_1.0_chunk1` | ⬛ superseded | `-2.2064` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 1.0 · Ban hành: 06/2025  ##… |
| 4 | `POL-01_2.0_chunk1` | ✅ | `-2.1280` | # POL-01 — Chính sách sao lưu dữ liệu  **Công ty Tài chính Sao Đỏ — Phòng CNTT** · Phiên bản 2.0 · Ban hành: 05/2026 · T… |

**Diagnosis:**

> Retrieval hit PASS: all 1 expected source(s) found in top-k. Groundedness PASS: all 4 keyword(s) present in retrieved content. Version trap (comparison): both POL-01 v1 (superseded) and v2 (current) retrieved — full version history available for comparison.

---

### Q10 — out_of_scope

**Question:** Chi phí hàng tháng cho dịch vụ cloud backup là bao nhiêu?

**Query submitted:** `chi phí cloud backup`  
**Search mode:** `current`

**Retrieval hit:** ✅ `pass`  
**Groundedness:** ✅ `pass`

**Retrieved chunks:** *(none — query returned no results)*

**Diagnosis:**

> Not found in the supplied documents. No relevant chunks retrieved — correct outcome for out-of-scope question.

---
