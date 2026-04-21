# Reflection — Nguyễn Thành Luân (2A202600204)

## 1. Đóng góp cá nhân (Engineering Contribution)

### Modules đã phát triển:
- **Retrieval Evaluator:** Implement `engine/retrieval_eval.py` — tính toán Hit Rate, MRR (Mean Reciprocal Rank), Precision@K cho Retrieval pipeline.
- **Benchmark Runner:** Implement `engine/runner.py` — async pipeline chạy song song với batching để tránh rate limit, tracking cost/token usage, progress bar.
- **Performance Optimization:** Thiết kế batch_size parameter để cân bằng giữa tốc độ (async) và ổn định (rate limit).

### Git Commits:
- `feat(retrieval): implement Hit Rate, MRR, Precision@K evaluation`
- `feat(runner): async benchmark runner with batching and cost tracking`

---

## 2. Kiến thức kỹ thuật (Technical Depth)

### Retrieval Evaluation Metrics

#### Hit Rate (Hit@K)
- **Công thức:** Hit = 1 nếu ∃ doc ∈ expected_ids nằm trong top-K retrieved_ids, ngược lại = 0
- **Ý nghĩa:** Đo xem hệ thống có "tìm thấy" tài liệu đúng không (binary: có/không)
- **Trong lab:** Hit Rate = 87.3% → 87.3% cases tìm thấy ít nhất 1 doc đúng trong top-3
- **Hạn chế:** Không phân biệt doc đúng ở vị trí 1 vs vị trí 3

#### MRR (Mean Reciprocal Rank)
- **Công thức:** MRR = 1/position (1-indexed) của doc đúng đầu tiên
  - Vị trí 1 → MRR = 1.0, Vị trí 2 → MRR = 0.5, Vị trí 3 → MRR = 0.33
- **Ý nghĩa:** Đo chất lượng ranking — doc đúng càng ở trên cao thì MRR càng cao
- **Trong lab:** V1 MRR = 0.745, V2 MRR = 0.788 → V2 ranking tốt hơn

#### Precision@K
- **Công thức:** Precision@K = (số doc đúng trong top-K) / K
- **Ý nghĩa:** Tỉ lệ doc đúng trong kết quả trả về. Precision@3 = 0.33 nghĩa là 1/3 doc trong top-3 là đúng.
- **So sánh:** Precision@K khắt khe hơn Hit Rate (đo tỉ lệ, không chỉ có/không)

### Async Pipeline Design
- **asyncio.gather():** Chạy nhiều coroutines đồng thời. 10 cases chạy cùng lúc thay vì tuần tự → tăng tốc 5-10x.
- **Batching:** Chia dataset thành batches (10 cases/batch) để tránh rate limit API.
- **Trade-off:** batch_size lớn = nhanh hơn nhưng rủi ro rate limit. batch_size nhỏ = ổn định nhưng chậm.

### Cost Tracking
- **Token usage:** Mỗi lần eval tiêu tốn tokens (input + output). V1: avg 200 tokens/case, V2: avg 140 tokens/case.
- **Cost per eval:** V1 $0.00097/case, V2 $0.00068/case → V2 tiết kiệm 30%.
- **Optimization:** Early rejection cho adversarial = 0 tokens. Caching = giảm 50%+ cho repeated queries.

---

## 3. Giải quyết vấn đề (Problem Solving)

### Vấn đề: Pipeline chạy quá chậm khi tuần tự
- **Triệu chứng:** 55 cases × 0.5s latency/case = 27.5s tuần tự
- **Giải pháp:** Async pipeline với batch_size=10 → 55 cases trong 2.38s (V2), giảm 91.3% thời gian
- **Kỹ thuật:** `asyncio.gather(*tasks)` + semaphore batching

### Vấn đề: Retrieval evaluation cho adversarial cases
- **Thách thức:** Adversarial cases có `expected_retrieval_ids = []` → không có ground truth retrieval
- **Giải pháp:** Nếu expected_ids rỗng → trả Hit Rate = 1.0 (không yêu cầu retrieval). Tránh false negative.

---

## 4. Bài học rút ra
1. **Retrieval quality quyết định answer quality** — Nếu retrieval sai context, LLM sẽ hallucinate dù prompt tốt.
2. **MRR > Hit Rate cho ranking evaluation** — Hit Rate chỉ biết có/không, MRR biết "ở đâu".
3. **Async là bắt buộc cho production** — 91% reduction trong latency, zero trade-off quality.
4. **Cost tracking phải built-in** — Không đo chi phí = không tối ưu được.
