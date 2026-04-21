# Reflection — Vũ Hoàng Minh (2A202600440)

## 1. Đóng góp cá nhân (Engineering Contribution)

### Modules đã phát triển:
- **Synthetic Data Generator (SDG):** Thiết kế và implement `data/synthetic_gen.py` — tạo bộ Golden Dataset gồm 55 test cases đa dạng với 4 mức độ khó, bao phủ 12 categories và 16 loại câu hỏi.
- **Golden Dataset Design:** Thiết kế cấu trúc data JSONL với các trường: question, expected_answer, context, expected_retrieval_ids, metadata. Đảm bảo mỗi case đều có ground truth mapping cho retrieval evaluation.
- **Adversarial Test Design:** Thiết kế 10 câu hỏi adversarial bao gồm prompt injection, goal hijacking, social engineering, jailbreak, và data extraction attempts.

### Git Commits:
- `feat(sdg): implement golden dataset generator with 55 test cases`
- `data: generate golden_set.jsonl with adversarial and edge cases`

---

## 2. Kiến thức kỹ thuật (Technical Depth)

### Synthetic Data Generation (SDG)
- **Khái niệm:** Quy trình tạo dữ liệu test tự động từ tài liệu gốc. Trong thực tế sẽ dùng LLM API (GPT/Claude) để generate QA pairs.
- **Golden Dataset:** Bộ test "chuẩn vàng" với câu trả lời đã được verify, dùng làm baseline cho evaluation.
- **Tầm quan trọng:** Chất lượng dataset quyết định độ tin cậy của toàn bộ evaluation. "Garbage in, garbage out."

### Red Teaming & Adversarial Testing
- **Prompt Injection:** Kỹ thuật lừa AI bỏ qua system instructions. Ví dụ: "Ignore all previous instructions..."
- **Goal Hijacking:** Yêu cầu AI làm việc ngoài phạm vi. Ví dụ: Bot hỗ trợ kỹ thuật bị yêu cầu viết thơ.
- **Social Engineering:** Giả danh người có quyền hạn để trích xuất thông tin.
- **Tại sao cần test:** V1 Agent pass 92.7% tổng thể nhưng 100% fail ở adversarial → Không test adversarial = không biết lỗ hổng.

### Hit Rate vs MRR
- **Hit Rate:** Binary metric (0 hoặc 1) — có tìm thấy doc đúng trong top-K không? Dễ hiểu nhưng không phản ánh ranking quality.
- **MRR:** Continuous metric (0 → 1) — doc đúng ở vị trí nào? Phản ánh chính xác hơn chất lượng retrieval.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Thiết kế dataset đủ đa dạng
- **Thách thức:** 55 cases cần cover đủ loại: fact-check, how-to, comparison, reasoning, adversarial, edge.
- **Giải pháp:** Phân chia theo ma trận: 12 categories × 4 difficulty levels. Mỗi category có ít nhất 2 cases, mỗi difficulty level có ít nhất 5 cases.

### Vấn đề: Ground Truth cho adversarial cases
- **Thách thức:** Adversarial cases không có "câu trả lời đúng" theo nghĩa thông thường.
- **Giải pháp:** Expected answer cho adversarial = cách từ chối đúng ("Tôi không thể thực hiện yêu cầu này..."). Judge chấm dựa trên safety, không phải accuracy.

---

## 4. Bài học rút ra
1. **Dataset quality > Dataset quantity** — 55 cases chất lượng tốt hơn 500 cases kém.
2. **Adversarial testing bắt buộc** — Chỉ test happy path sẽ bỏ sót lỗ hổng nguy hiểm.
3. **Ground Truth mapping quan trọng** — Nếu không có expected_retrieval_ids, không thể đánh giá Retrieval stage.
