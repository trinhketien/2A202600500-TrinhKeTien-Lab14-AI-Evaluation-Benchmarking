"""
Benchmark Runner — Lab 14
===========================
Async runner chạy pipeline đánh giá song song.
Hỗ trợ batching để tránh rate limit + tracking cost/latency.
"""

import asyncio
import time
from typing import List, Dict


class BenchmarkRunner:
    """
    Async Benchmark Runner.
    Chạy Agent → Evaluator → Judge song song cho toàn bộ dataset.
    """

    def __init__(self, agent, evaluator, judge, retrieval_evaluator=None):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge
        self.retrieval_evaluator = retrieval_evaluator
        self.total_tokens = 0
        self.total_cost = 0.0

    async def run_single_test(self, test_case: Dict) -> Dict:
        """Chạy 1 test case qua pipeline: Agent → RAGAS → Judge."""
        start_time = time.perf_counter()

        # 1. Gọi Agent
        response = await self.agent.query(test_case["question"])
        agent_latency = time.perf_counter() - start_time

        # 2. Chạy RAGAS metrics + Retrieval eval
        ragas_scores = await self.evaluator.score(test_case, response)

        # 3. Retrieval evaluation (Hit Rate, MRR)
        expected_ids = test_case.get("expected_retrieval_ids", [])
        retrieved_ids = response.get("retrieved_ids", [])
        
        if self.retrieval_evaluator and expected_ids:
            ret_eval = await self.retrieval_evaluator.evaluate_single(expected_ids, retrieved_ids)
            ragas_scores["retrieval"] = ret_eval
        else:
            ragas_scores["retrieval"] = {
                "hit_rate": 1.0 if not expected_ids else 0.0,
                "mrr": 1.0 if not expected_ids else 0.0,
                "precision_at_k": 1.0 if not expected_ids else 0.0,
            }

        # 4. Chạy Multi-Judge
        judge_result = await self.judge.evaluate_multi_judge(
            test_case["question"],
            response["answer"],
            test_case["expected_answer"]
        )

        # Track cost
        tokens = response.get("metadata", {}).get("tokens_used", 0)
        cost = response.get("metadata", {}).get("cost_usd", 0)
        self.total_tokens += tokens
        self.total_cost += cost

        total_latency = time.perf_counter() - start_time

        return {
            "id": test_case.get("id", "N/A"),
            "test_case": test_case["question"],
            "expected_answer": test_case["expected_answer"],
            "agent_response": response["answer"],
            "retrieved_ids": retrieved_ids,
            "expected_retrieval_ids": expected_ids,
            "latency": round(total_latency, 4),
            "agent_latency": round(agent_latency, 4),
            "ragas": ragas_scores,
            "judge": judge_result,
            "tokens_used": tokens,
            "cost_usd": cost,
            "metadata": test_case.get("metadata", {}),
            "status": "fail" if judge_result["final_score"] < 3 else "pass"
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 5) -> List[Dict]:
        """
        Chạy song song bằng asyncio.gather với giới hạn batch_size để không bị Rate Limit.
        In progress bar cho mỗi batch.
        """
        results = []
        total = len(dataset)

        for i in range(0, total, batch_size):
            batch = dataset[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            print(f"   📦 Batch {batch_num}/{total_batches} ({len(batch)} cases)...", end=" ")

            tasks = [self.run_single_test(case) for case in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            passed = sum(1 for r in batch_results if r["status"] == "pass")
            print(f"✅ {passed}/{len(batch)} passed")

        return results

    def get_cost_report(self) -> Dict:
        """Tạo báo cáo chi phí."""
        return {
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "avg_cost_per_eval": round(self.total_cost / max(1, self.total_tokens // 150), 6),
            "cost_optimization_suggestions": [
                "Sử dụng caching cho các câu hỏi trùng lặp",
                "Giảm max_tokens cho câu hỏi đơn giản",
                "Sử dụng model nhỏ hơn (gpt-4o-mini) cho pre-screening",
                "Batch processing để giảm overhead"
            ]
        }
