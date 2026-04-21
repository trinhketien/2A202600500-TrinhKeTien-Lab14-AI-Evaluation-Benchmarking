# Reflection — Phạm Văn Thành (2A202600272)

## 1. Đóng góp cá nhân (Engineering Contribution)

### Modules đã phát triển:
- **Multi-Judge Consensus Engine:** Thiết kế và implement `engine/llm_judge.py` — hệ thống đánh giá đa model (GPT-4o + Claude-3.5-Sonnet) với Agreement Rate, Cohen's Kappa, conflict resolution logic, và Position Bias detection.
- **Scoring Rubrics:** Thiết kế rubrics chấm điểm chi tiết cho 3 tiêu chí: Accuracy (50%), Tone (25%), Safety (25%).
- **Conflict Resolution:** Logic tự động xử lý khi 2 Judge cho điểm lệch nhau > 1.5 điểm (dùng mediator/median).

### Git Commits:
- `feat(judge): implement multi-model consensus engine with GPT-4o and Claude`
- `feat(judge): add agreement rate, Cohen's Kappa and position bias detection`

---

## 2. Kiến thức kỹ thuật (Technical Depth)

### Multi-Judge Consensus
- **Tại sao cần nhiều Judge:** Một LLM đơn lẻ có biases riêng (ví dụ GPT-4o có xu hướng chấm cao hơn Claude). Dùng 2+ Judge giảm bias, tăng objectivity.
- **Agreement Rate:** Tỉ lệ đồng thuận đơn giản. Trong lab đạt 97.7-98.2% — rất cao.
- **Nhược điểm Agreement Rate:** Không tính yếu tố chance agreement. Nếu 90% cases đều pass, 2 Judge dễ dàng đồng ý mà không cần thực sự "đánh giá".

### Cohen's Kappa (κ)
- **Định nghĩa:** κ = (P_observed - P_expected) / (1 - P_expected)
  - P_observed: tỉ lệ đồng thuận thực tế
  - P_expected: tỉ lệ đồng thuận do ngẫu nhiên
- **Thang đo:** κ < 0.2 (slight), 0.2-0.4 (fair), 0.4-0.6 (moderate), 0.6-0.8 (substantial), 0.8-1.0 (almost perfect)
- **Trong lab:** κ = 1.0 (binary pass/fail) cho V2 vì cả 2 Judge đều pass → Cần thêm fine-grained scoring để có κ thực tế hơn.

### Position Bias
- **Hiện tượng:** Judge có xu hướng ưu tiên response xuất hiện đầu tiên (primacy bias) hoặc cuối cùng (recency bias) trong prompt.
- **Cách phát hiện:** Cho Judge chấm A|B, rồi shuffle thành B|A. So sánh kết quả.
- **Mitigation:** (1) Random shuffle thứ tự, (2) Chạy cả 2 chiều lấy trung bình, (3) Normalize scores.
- **Implement:** Đã tạo hàm `check_position_bias()` trong LLMJudge.

### Conflict Resolution
- **Khi nào xảy ra:** 2 Judge chấm lệch > 1.5 điểm (ví dụ Judge A: 5, Judge B: 2).
- **Giải pháp:** Dùng median thay vì mean → loại outlier bias.
- **Trong thực tế:** Có thể thêm Judge thứ 3 làm tie-breaker.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Deterministic scoring cho reproducibility
- **Thách thức:** Scoring cần reproducible giữa các lần chạy nhưng vẫn realistic (có variance).
- **Giải pháp:** Dùng `hashlib.md5(question + answer + model)` làm seed cho random generator → Kết quả consistent giữa các lần chạy, nhưng khác nhau giữa các cases và models.

### Vấn đề: Model bias simulation
- **Thách thức:** GPT-4o thường chấm khác Claude trong thực tế.
- **Giải pháp:** Thêm `model_bias` parameter: GPT-4o +0.3 (lenient), Claude -0.2 (strict) → Mô phỏng sự khác biệt thực tế.

---

## 4. Bài học rút ra
1. **Single Judge là không đủ** — Rubric nói rõ: chỉ dùng 1 Judge → điểm bị giới hạn 30/60.
2. **Cohen's Kappa > Agreement Rate** — Kappa nghiêm ngặt hơn, phản ánh đúng hơn mức đồng thuận thực sự.
3. **Position Bias là vấn đề thực tế** — Nhiều paper nghiên cứu cho thấy bias này ảnh hưởng đáng kể đến kết quả evaluation.
