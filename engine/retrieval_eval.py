"""
Retrieval Evaluator — Lab 14
==============================
Tính toán Hit Rate và MRR cho Retrieval pipeline.
Hỗ trợ evaluate cả batch và phân tích chi tiết.
"""

from typing import List, Dict
import asyncio


class RetrievalEvaluator:
    """Đánh giá chất lượng Retrieval stage."""

    def __init__(self, top_k: int = 3):
        self.top_k = top_k

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = None) -> float:
        """
        Tính Hit Rate: có ít nhất 1 doc đúng trong top-K hay không.
        Hit = 1 nếu ∃ expected_id ∈ retrieved_ids[:top_k], 0 nếu không.
        """
        k = top_k or self.top_k
        if not expected_ids:
            return 1.0  # Không yêu cầu retrieval → luôn pass
        top_retrieved = retrieved_ids[:k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank.
        MRR = 1 / position (1-indexed) của doc đúng đầu tiên được tìm thấy.
        Nếu không tìm thấy → 0.
        """
        if not expected_ids:
            return 1.0  # Không yêu cầu retrieval → luôn pass
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    def calculate_precision_at_k(self, expected_ids: List[str], retrieved_ids: List[str], k: int = None) -> float:
        """
        Precision@K: tỉ lệ doc đúng trong top-K.
        """
        k = k or self.top_k
        if not expected_ids:
            return 1.0
        top_k_ids = retrieved_ids[:k]
        relevant = sum(1 for doc_id in top_k_ids if doc_id in expected_ids)
        return relevant / k if k > 0 else 0.0

    async def evaluate_single(self, expected_ids: List[str], retrieved_ids: List[str]) -> Dict:
        """Đánh giá retrieval cho 1 case."""
        return {
            "hit_rate": self.calculate_hit_rate(expected_ids, retrieved_ids),
            "mrr": self.calculate_mrr(expected_ids, retrieved_ids),
            "precision_at_k": self.calculate_precision_at_k(expected_ids, retrieved_ids),
            "expected_ids": expected_ids,
            "retrieved_ids": retrieved_ids[:self.top_k]
        }

    async def evaluate_batch(self, results: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ batch kết quả.
        Mỗi result cần có trường 'expected_retrieval_ids' và 'retrieved_ids'.
        """
        if not results:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0, "avg_precision_at_k": 0.0, "total": 0}

        hit_rates = []
        mrrs = []
        precisions = []

        for r in results:
            expected = r.get("expected_retrieval_ids", [])
            retrieved = r.get("retrieved_ids", [])
            
            single = await self.evaluate_single(expected, retrieved)
            hit_rates.append(single["hit_rate"])
            mrrs.append(single["mrr"])
            precisions.append(single["precision_at_k"])

        total = len(results)
        return {
            "avg_hit_rate": round(sum(hit_rates) / total, 4),
            "avg_mrr": round(sum(mrrs) / total, 4),
            "avg_precision_at_k": round(sum(precisions) / total, 4),
            "total": total,
            "hit_count": sum(1 for h in hit_rates if h > 0),
            "miss_count": sum(1 for h in hit_rates if h == 0),
            "detail": {
                "hit_rates": hit_rates,
                "mrrs": mrrs
            }
        }
