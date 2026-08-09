# Data Pack — Role-based Assessment · Data Engineer @ Xbrain

Gói dữ liệu đi kèm đề Bài 1 (Domain Knowledge — POC). Toàn bộ dữ liệu và tài liệu là **giả lập** của khách hàng "Công ty Tài chính Sao Đỏ", phục vụ bài đánh giá.

## Nội dung

```
data/
├── app_logs_7days.jsonl    # log 7 ngày (27/07–02/08) của 5 hệ thống — dùng cho Phần A
└── docs/                   # 8 tài liệu vận hành — dùng cho Phần B (knowledge base)
reading/
├── 01_chunking_basics.md   # tài liệu đọc: chia nhỏ tài liệu (chunking)
└── 02_rag_eval_basics.md   # tài liệu đọc: đánh giá chất lượng knowledge base
```

## Lưu ý

- Dữ liệu log **không sạch** — đó là chủ đích của đề. Đừng sửa file gốc; xử lý trong pipeline của bạn.
- Đọc 2 file trong `reading/` **trước khi** làm Phần B.
- Mọi câu hỏi về đề: gửi vào kênh Q&A ghi trong email phát đề.
