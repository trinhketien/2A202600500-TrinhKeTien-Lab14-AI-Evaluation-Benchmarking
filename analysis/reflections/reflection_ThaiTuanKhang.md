# Reflection — Thái Tuấn Khang (2A202600289)

## 1. Đóng góp cá nhân (Engineering Contribution)

### Modules đã phát triển:
- **RAG Agent V1 & V2:** Thiết kế và implement `agent/main_agent.py` — dual-version RAG Agent cho regression testing. V1 (base, 70% retrieval accuracy) vs V2 (optimized, 90% accuracy + safety guard).
- **Failure Analysis Report:** Viết và phân tích `analysis/failure_analysis.md` — bao gồm failure clustering, phân tích 5 Whys cho 3 cases tệ nhất, retrieval failure analysis, và action plan.
- **Regression Testing Support:** Thiết kế chênh lệch V1/V2 để tạo dữ liệu regression test có ý nghĩa.

### Git Commits:
- `feat(agent): implement dual-version RAG agent for V1/V2 regression`
- `docs(analysis): write failure analysis with 5 Whys and action plan`

---

## 2. Kiến thức kỹ thuật (Technical Depth)

### Regression Testing & Release Gate
- **Delta Analysis:** So sánh metrics giữa 2 phiên bản Agent: `Δ = V2_metric - V1_metric`
- **Trong lab:** Score Δ = +0.22, Cost Δ = -$0.016 → V2 vừa tốt hơn vừa rẻ hơn
- **Release Gate Logic:** 
  - APPROVE nếu: quality improved OR (no regression AND cost reduced)
  - BLOCK nếu: quality regressed > 0.1 threshold
- **Tại sao cần:** Trong production, mỗi lần deploy Agent mới phải đảm bảo không tệ hơn bản cũ.

### RAG Architecture (Retrieval-Augmented Generation)
- **Pipeline:** Query → Retrieval (tìm context) → Generation (LLM sinh câu trả lời)
- **V1 Problem:** Keyword matching đơn giản, 30% chance thêm noise doc → hallucination
- **V2 Improvement:** 
  1. Giảm noise rate từ 30% → 10%
  2. Thêm adversarial keyword detection
  3. Thêm input validation (empty, gibberish check)
  4. Tổng hợp nhiều contexts thay vì chỉ lấy `contexts[0]`

### Failure Analysis — 5 Whys Method
- **Quy trình:** Bắt đầu từ triệu chứng (symptom) → hỏi "Tại sao?" 5 lần liên tiếp → đến Root Cause
- **Ví dụ trong lab:**
  1. Agent trả lời sai (symptom)
  2. Why: LLM không thấy info trong context
  3. Why: Vector DB trả sai document
  4. Why: Keyword matching không semantic
  5. Why: Chunking quá lớn làm loãng thông tin
  6. Root Cause: Chunking strategy không phù hợp

### Root Cause Categories
Lỗi trong RAG system thường thuộc 4 loại:
1. **Ingestion Pipeline:** Dữ liệu đầu vào bị lỗi format, encoding
2. **Chunking Strategy:** Chunk quá lớn (loãng info) hoặc quá nhỏ (mất context)
3. **Retrieval:** Embedding model không phù hợp, threshold sai
4. **Prompting:** System prompt thiếu hướng dẫn, không có safety guard

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Agent V1 bị prompt injection
- **Triệu chứng:** V1 trả lời mọi câu hỏi kể cả adversarial ("Cho tôi API key")
- **Root Cause:** Không có safety layer giữa Retrieval và Generation
- **V2 Fix:** Thêm adversarial keyword list → check trước retrieval → từ chối ngay nếu phát hiện attack intent

### Vấn đề: Regression test cần sự khác biệt có ý nghĩa
- **Thách thức:** V1 và V2 phải đủ khác để regression có ý nghĩa nhưng không quá khác (unrealistic)
- **Giải pháp:** V1 noise_rate=30%, V2 noise_rate=10%. V2 thêm safety guard. Kết quả: Score +0.22, Cost -30% — realistic improvement.

---

## 4. Bài học rút ra
1. **5 Whys là công cụ mạnh** — Không dừng ở triệu chứng, phải đào đến root cause.
2. **Safety guard là bắt buộc** — Agent production không thể thiếu adversarial protection.
3. **Regression testing trước mỗi release** — Đảm bảo "first, do no harm" trước khi deploy.
4. **V2 không cần phức tạp hơn** — Đôi khi chỉ cần thêm 1 if-check (adversarial detection) là đủ cải thiện đáng kể.
