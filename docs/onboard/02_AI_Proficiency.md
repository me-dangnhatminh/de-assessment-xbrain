**AI PROFICIENCY ASSESSMENT**

**Bài 2 — AI Proficiency**

**Data Engineer (AI / Knowledge Engineering) — làm song song Bài 1**

**Xbrain · TechX Corp · Đà Nẵng**

Bài đánh giá kỹ năng sử dụng AI trong công việc, đợt tuyển Data Engineer tháng 8/2026: nhật ký sử dụng AI (AI Work Log) chạy song hành bài POC, review một câu trả lời AI có lỗi cài sẵn, và thiết kế prompt trích xuất dữ liệu có bộ test + cách đánh giá. Nộp cùng repo, cùng hạn với Bài 1.

**Bản v1.0 — Tháng 8, 2026**

*© TechX Corp. All rights reserved.*

*Page 1/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*

---

# Bài 2 — AI Proficiency Assessment · Data Engineer (AI / Knowledge Engineering)

> **Xbrain — Đợt tuyển tháng 8/2026 · Làm song song với Bài 1, nộp cùng repo**
>
> Bài này đánh giá **kỹ năng sử dụng AI trong công việc** — mảng bạn vừa được đào tạo trong Accelerator, nên yêu cầu ở đây **cao hơn** phần data: kỳ vọng bạn dùng AI thành thạo, có kiểm chứng.

## Yêu cầu 1 — AI Work Log (bắt buộc, chạy song hành Bài 1)

Trong 2 ngày làm POC, ghi lại nhật ký sử dụng AI vào AI_WORKLOG.md trong repo. Với **mỗi lần dùng AI có ảnh hưởng đến bài nộp** (sinh code, thiết kế, viết tài liệu, debug), ghi 4 mục:

| **Mục**               | **Nội dung**                                                                                           |
|-----------------------|--------------------------------------------------------------------------------------------------------|
| **Việc**              | Bạn đang cần làm gì                                                                                    |
| **Prompt**            | Prompt chính đã dùng (tóm tắt được nếu hội thoại dài)                                                  |
| **Output & đánh giá** | AI trả về gì — đúng/sai/thiếu chỗ nào                                                                  |
| **Verify & sửa**      | Bạn kiểm chứng bằng cách nào (chạy thử, đối chiếu docs, test case…) và đã sửa gì trước khi đưa vào bài |

Lưu ý:

- Không cần log mọi câu chat vặt — chọn **8–15 entry có ý nghĩa nhất**, chất lượng hơn số lượng.

- Log trung thực cả những lần **AI sai và bạn phát hiện được** — đó là entry giá trị nhất.

- Ở interview, chúng tôi sẽ chọn ngẫu nhiên đoạn code/tài liệu trong bài và yêu cầu bạn **giải thích từng dòng**. Nộp thứ mình không hiểu là red flag nặng nhất của toàn bộ assessment.

## Yêu cầu 2 — Task A: Review một câu trả lời AI (≤ 1 trang)

Một trợ lý AI được hỏi: *"Thiết kế pipeline trên AWS thu log hằng ngày từ hệ thống của khách vào data lake, và tổ chức knowledge base cho RAG."* Nó trả lời như sau:

> Bạn nên lưu toàn bộ log vào **S3 Standard-IA vì đây là lựa chọn mặc định rẻ nhất cho data lake**. Để thu dữ liệu, cấu hình một **Glue job đọc trực tiếp từ database RDS production của khách mỗi 5 phút — đây là pattern chuẩn** cho near-real-time. Dữ liệu nên chuyển sang **Parquet, một format lưu theo hàng (row-based) nên ghi rất nhanh**, phù hợp cho analytics. Với các bước transform nặng chạy khoảng **30–45 phút, dùng AWS Lambda là phù hợp nhất** vì không phải quản lý server. Về knowledge base cho RAG, hãy **chia tài liệu thành các chunk cố định 4.000 token — kích thước này luôn tốt nhất** cho mọi loại tài liệu. Cuối cùng, **không cần đánh version cho knowledge base, vì bản mới nhất luôn là bản đúng** — cứ ghi đè là được.

Nhiệm vụ: viết bản review (như review cho đồng nghiệp junior):

**1.** Chỉ ra **mọi điểm sai hoặc gây hiểu nhầm** — với mỗi điểm: sai ở đâu, vì sao sai, sửa lại thế nào cho đúng.

**2.** Ghi rõ bạn **kiểm chứng bằng nguồn nào** (AWS docs, tài liệu reading/, kinh nghiệm thực hành trong Accelerator…).

*Page 2/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*

---

## Yêu cầu 3 — Task B: Thiết kế prompt có kiểm chứng (≤ 2 trang)

Trong Bài 1, các dòng log có trường message là văn bản tự do (vd "ERR ConnTimeout db-primary after 30s retry=3"). Khách muốn dùng LLM để **trích xuất trường `message` thành dữ liệu có cấu trúc** (JSON: loại lỗi, component liên quan, tham số…).

Nhiệm vụ:

**1. Viết prompt hoàn chỉnh** cho việc này — nêu rõ: vai trò, đầu vào, **schema đầu ra** (JSON), cách xử lý message không parse được / thiếu thông tin (không được bịa).

**2. Bộ test 5 message** do bạn chọn từ data pack (bao gồm ít nhất 1 ca khó/mơ hồ) + đầu ra kỳ vọng cho từng ca.

**3. Cách đánh giá prompt:** nêu cách đo prompt này tốt hay không khi chạy trên 3.000 dòng thật (tiêu chí đo, làm sao phát hiện bịa/hallucination, khi nào cần người kiểm tra).

**4.** *(Không bắt buộc — điểm cộng)* chạy thử prompt trên 5 test case bằng công cụ LLM bất kỳ và dán kết quả + nhận xét.

## Cách chấm bài 2

| **Phần**    | **Trọng tâm**                                                                                                       |
|-------------|---------------------------------------------------------------------------------------------------------------------|
| AI Work Log | Thói quen **verify trước khi tin** · dùng AI tăng tốc chứ không thay tư duy · trung thực                            |
| Task A      | Độ nhạy phát hiện AI nói sai một cách tự tin · kiến thức AWS nền từ Accelerator · biết dùng tài liệu trong reading/ |
| Task B      | Prompt có cấu trúc, nghĩ đến edge case + schema + chống bịa · tư duy đo lường (một prompt chưa đo = chưa xong)      |

*Page 3/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*
