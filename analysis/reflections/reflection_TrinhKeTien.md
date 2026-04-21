# Reflection — Trịnh Kế Tiến (2A202600500)

## 1. Đóng góp cá nhân (Engineering Contribution)

### Modules đã phát triển:
- **Synthetic Data Generator (SDG):** Thiết kế và implement `data/synthetic_gen.py` — tạo 55 test cases chất lượng với 4 mức độ khó (easy/medium/hard/adversarial + edge cases). Đảm bảo coverage đa dạng: 12 categories, 16 loại câu hỏi khác nhau.
- **Multi-Judge Consensus Engine:** Implement `engine/llm_judge.py` — hệ thống đánh giá đa model với Agreement Rate, Cohen's Kappa (simplified), conflict resolution logic, và Position Bias detection.
- **Main Agent V1/V2:** Thiết kế dual-version agent (`agent/main_agent.py`) với Retrieval accuracy khác nhau (V1: 70%, V2: 90%) để tạo dữ liệu regression test thực tế.
- **Pipeline Integration:** Kết nối tất cả components trong `main.py` — pipeline hoàn chỉnh từ load dataset → benchmark V1/V2 → regression analysis → release gate decision → report generation.

### Git Commits:
- `feat(sdg): implement 55-case golden dataset with adversarial & edge cases`
- `feat(judge): multi-model consensus engine with agreement rate & conflict resolution`
- `feat(agent): dual-version RAG agent for regression testing`
- `feat(pipeline): complete benchmark pipeline with release gate`
- `docs(analysis): failure analysis with 5 Whys root cause`

---

## 2. Kiến thức kỹ thuật (Technical Depth)

### Các khái niệm đã hiểu và áp dụng:

#### MRR (Mean Reciprocal Rank)
- **Định nghĩa:** Trung bình nghịch đảo vị trí (1-indexed) của tài liệu đúng đầu tiên trong danh sách kết quả retrieval.
- **Ý nghĩa:** MRR cao (gần 1.0) nghĩa là hệ thống luôn đặt tài liệu đúng ở đầu kết quả. MRR = 0.5 nghĩa là trung bình tài liệu đúng nằm ở vị trí 2.
- **Áp dụng trong lab:** V1 MRR = 0.745, V2 MRR = 0.788 → V2 cải thiện việc ranking tài liệu đúng lên cao hơn.

#### Cohen's Kappa
- **Định nghĩa:** Hệ số đo mức đồng thuận giữa 2+ annotators (ở đây là Judge models) có tính đến yếu tố ngẫu nhiên (chance agreement).
- **Khác Agreement Rate:** Agreement Rate đơn giản chỉ tính tỉ lệ đồng ý. Cohen's Kappa loại trừ phần đồng ý do ngẫu nhiên, nên khắt khe hơn.
- **Áp dụng:** κ = 1.0 khi cả 2 Judge hoàn toàn đồng ý (binary pass/fail). Trong thực tế cần > 0.6 (substantial agreement) và > 0.8 (almost perfect agreement).

#### Position Bias
- **Định nghĩa:** Xu hướng Judge ưu tiên response xuất hiện đầu tiên (hoặc cuối cùng) trong prompt, bất kể chất lượng thực.
- **Cách phát hiện:** Cho Judge đánh giá Response A|B, rồi đổi thứ tự B|A. Nếu kết quả thay đổi → bias.
- **Mitigaton:** Chạy đánh giá cả 2 chiều và lấy trung bình, hoặc shuffle thứ tự randomly.

#### Trade-off Chi phí vs Chất lượng
- **Thực tế:** V1 dùng gpt-4o-mini (rẻ hơn) → $0.0536 nhưng quality 3.87/5.0. V2 dùng gpt-4o (đắt hơn per-token) nhưng tối ưu token usage → $0.0374 (-30%) với quality 4.09/5.0 (+5.7%).
- **Insight:** Không phải model đắt hơn = tốn hơn. Tối ưu prompt + early rejection cho adversarial cases giúp giảm cost đáng kể.
- **Đề xuất giảm 30% cost:** (1) Cache responses for FAQs, (2) Pre-screen with cheap model, (3) Early reject adversarial without LLM call.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề 1: Unicode Encoding trên Windows
- **Triệu chứng:** Script crash vì cp1258 console không hỗ trợ emoji.
- **Giải pháp:** Tạo `encoding_fix.py` wrapper force stdout/stderr sang UTF-8 + set PYTHONIOENCODING env var.

### Vấn đề 2: Thiết kế Regression Test không bị deterministic
- **Triệu chứng:** Cần V1 và V2 có kết quả khác nhau nhất quán (reproducible) mà vẫn realistic.
- **Giải pháp:** Sử dụng deterministic seed dựa trên hash(question + model) → kết quả consistent giữa các lần chạy nhưng vẫn có variability realistic.

### Vấn đề 3: Rate Limit handling
- **Triệu chứng:** Chạy 55 cases song song có thể bị rate limit.
- **Giải pháp:** Implement batch_size parameter trong BenchmarkRunner — chạy 10 cases cùng lúc, đợi xong mới chạy batch tiếp.

---

## 4. Bài học rút ra

1. **"Nếu không đo được, không cải tiến được"** — Chỉ khi có metrics cụ thể (Hit Rate, MRR, Judge Score) mới thấy rõ V2 tốt hơn V1 ở đâu.
2. **Multi-Judge quan trọng hơn Single-Judge** — 1 model có thể biased. 2+ models với agreement rate giúp đảm bảo khách quan.
3. **Adversarial testing là bắt buộc** — V1 pass 92.7% nhưng 100% fail ở adversarial. Không test adversarial = không biết hệ thống có lỗ hổng.
4. **Cost optimization ≠ Sacrifice quality** — V2 vừa tốt hơn vừa rẻ hơn, nhờ tối ưu logic thay vì chỉ đổi model.
