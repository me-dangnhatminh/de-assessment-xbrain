**ROLE-BASED ASSESSMENT**

**Bài 1 — Domain Knowledge**

**POC Data Engineer (AI / Knowledge Engineering)**

**Xbrain · TechX Corp · Đà Nẵng**

Đề bài thực hành vị trí Data Engineer, đợt tuyển tháng 8/2026: một yêu cầu POC mô phỏng từ khách hàng (giả lập) gồm 2 phần — pipeline xử lý log 7 ngày thành dữ liệu sạch + báo cáo, và mini knowledge base cho trợ lý AI kèm bộ câu hỏi kiểm chứng chất lượng. Ứng viên làm trong 2 ngày và nộp toàn bộ artifact trong một Git repo. Tài liệu cần thiết cho phần kiến thức mới có kèm sẵn trong đề.

**Bản v1.0 — Tháng 8, 2026**

*© TechX Corp. All rights reserved.*

*Page 1/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*

---

# Bài 1 — Role-based Assessment · Data Engineer (AI / Knowledge Engineering)

> Đi kèm: **data pack** (data/ + reading/) + Bài 2 (AI Proficiency — làm song song, nộp cùng repo)
>
> ⚠ Bài này KHÔNG đòi hỏi bạn đã biết trước về data engineering chuyên sâu hay RAG — tài liệu cần thiết có trong reading/. Anh chị chấm **cách bạn suy nghĩ, quy trình làm việc và tốc độ học**, không chấm việc bạn thuộc lòng công cụ.

## Bối cảnh — yêu cầu POC từ khách hàng (giả lập)

Đây là một yêu cầu như TechX/Xbrain vẫn nhận từ khách hàng thật. Toàn bộ tên công ty, hệ thống và dữ liệu trong đề đều là **giả lập** phục vụ bài đánh giá.

> **Từ:** Phòng CNTT — Công ty Tài chính **Sao Đỏ** (khách hàng giả lập)
>
> **Tới:** Đội Data Engineering, Xbrain
>
> **V/v:** POC trợ lý AI vận hành hệ thống

\>

> Chúng tôi vận hành 5 hệ thống nội bộ và gặp 2 vấn đề:

\>

> 1\. Log lỗi nằm rải rác, đội vận hành mất nhiều thời gian tổng hợp thủ công để biết **hệ thống nào đang lỗi nhiều, lỗi gì, xu hướng ra sao**.
>
> 2\. Tài liệu vận hành (SOP, chính sách backup, hướng dẫn xử lý sự cố) nằm ở nhiều file, **nhân viên mới không biết tin bản nào**; chúng tôi muốn một trợ lý AI trả lời được các câu hỏi vận hành **dựa đúng trên tài liệu nội bộ**.

\>

> Đề nghị Xbrain làm một POC trong 2 ngày chứng minh: (A) dựng được pipeline xử lý log của chúng tôi thành dữ liệu sạch + báo cáo, và (B) dựng được một knowledge base từ tài liệu của chúng tôi mà trợ lý AI có thể dùng, kèm cách kiểm chứng chất lượng.

\>

> Chúng tôi gửi kèm: 7 ngày log (data/app_logs_7days.jsonl) và 8 tài liệu vận hành (data/docs/).

Bạn là DE của Xbrain được giao POC này. Hãy làm như một dự án thật: có kế hoạch, có quy trình, có tài liệu bàn giao.

## Phần A — Data pipeline (log → dữ liệu sạch → báo cáo)

Viết pipeline bằng **Python** (chạy local — không bắt buộc chạy trên AWS thật):

**1. Ingest + validate:** đọc data/app_logs_7days.jsonl. Dữ liệu thật thì không sạch — hãy tự phát hiện và xử lý có chủ đích các vấn đề trong file (nói rõ trong README bạn tìm thấy gì và quyết định xử lý thế nào).

**2. Transform + lưu trữ:** làm sạch, chuẩn hoá và lưu thành dataset có cấu trúc (chọn format và giải thích **vì sao**).

**3. Báo cáo:** trả lời 4 câu hỏi của khách bằng SQL hoặc pandas (kèm code + kết quả):

> ◦ Service nào có nhiều lỗi (level=ERROR) nhất trong 7 ngày?

*Page 2/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*

---

> ◦ Số lượng lỗi theo ngày của toàn hệ thống — ngày nào bất thường?
>
> ◦ Top 3 loại lỗi (message/error code) phổ biến nhất, thuộc service nào?
>
> ◦ Có bao nhiêu bản ghi bị loại/sửa trong bước làm sạch, thuộc những loại vấn đề gì?

**4. Thiết kế AWS (trên giấy):** vẽ 1 sơ đồ + ≤1 trang giải thích: nếu triển khai pipeline này lên AWS cho khách chạy hằng ngày, bạn dùng những service nào (gợi ý phạm vi: những gì bạn đã học — S3, Glue, Lambda, Athena, IAM…) và dữ liệu chảy thế nào. Ghi rõ điểm bạn **chưa chắc** — trung thực được đánh giá cao hơn vẽ đẹp.

## Phần B — Mini knowledge base cho trợ lý AI

Trước khi làm, đọc 2 tài liệu trong reading/ (chunking + đánh giá KB). Sau đó:

**1. Thiết kế KB** từ 8 tài liệu trong data/docs/: cách chia nhỏ (chunking) — chia thế nào, vì sao; metadata cho mỗi chunk (nguồn, phiên bản, ngày…); cách tổ chức index để tìm lại được (dùng công cụ gì tuỳ bạn — từ SQLite full-text đến embeddings đều chấp nhận, **lý do chọn quan trọng hơn công cụ**).

**2. Xử lý mâu thuẫn:** trong bộ tài liệu có ít nhất một cặp tài liệu **mâu thuẫn nhau**. Tìm ra, và đề xuất cơ chế để KB luôn trả lời theo bản đúng (gợi ý: nghĩ về version + freshness).

**3. Bộ eval:** soạn **10 câu hỏi kiểm chứng** kèm đáp án mong đợi (trích từ tài liệu nào) + tiêu chí chấm một câu trả lời của trợ lý AI là đạt/không đạt. Chạy thử tối thiểu 3 câu trên KB của bạn và ghi kết quả.

**4. SOP cập nhật:** viết 1 SOP ngắn (≤1 trang): khi khách gửi tài liệu mới/sửa tài liệu cũ, quy trình cập nhật KB gồm những bước nào, bao lâu một lần, ai kiểm tra gì.

## Nộp bài — toàn bộ artifact trong 1 Git repo

```text
repo/
├── README.md            # EN — tổng quan, cách chạy từng phần, các quyết định + lý do
├── pipeline/            # code Phần A + kết quả 4 câu hỏi
├── kb/                  # code/cấu trúc KB + bộ eval + kết quả chạy thử
├── design/              # sơ đồ AWS + giải thích
├── sop/                 # SOP cập nhật KB
└── AI_WORKLOG.md        # theo yêu cầu Bài 2
```

- Nộp **link repo (GitHub, public hoặc mời account được chỉ định) + file zip backup** qua kênh ghi trong email phát đề.

- **Commit theo tiến trình thật** (chúng tôi xem lịch sử commit 2 ngày) — đừng dồn 1 commit cuối.

- README viết **tiếng Anh**; các tài liệu khác EN hay VN đều được.

## Cách chúng tôi chấm

- Tư duy + quy trình + tốc độ học \> kết quả hoàn hảo. Một pipeline đơn giản chạy đúng, giải thích rõ, thắng một kiến trúc phức tạp không chạy.

- **Được dùng AI thoải mái** — nhưng theo đúng luật ở Bài 2 (AI Work Log + bạn phải giải thích được mọi dòng mình nộp; interview sẽ probe trực tiếp).

- Ghi rõ điều chưa làm kịp/chưa chắc trong README — trung thực là tiêu chí văn hoá.

- Có câu hỏi về đề: gửi vào kênh Q&A trong email phát đề (câu trả lời được gửi chung cho mọi ứng viên để công bằng).

*Page 3/3 | © TechX Corp. All rights reserved. | Confidential — Xbrain and TechX only*
