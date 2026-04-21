import encoding_fix

"""
Main Pipeline — Lab 14: AI Evaluation & Benchmarking
======================================================
Pipeline hoàn chỉnh:
1. Load Golden Dataset
2. Chạy Benchmark V1 (Base Agent)
3. Chạy Benchmark V2 (Optimized Agent)
4. So sánh Regression (Delta Analysis)
5. Release Gate Decision
6. Tạo reports
"""

import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from engine.llm_judge import LLMJudge
from engine.retrieval_eval import RetrievalEvaluator
from agent.main_agent import MainAgent


class ExpertEvaluator:
    """RAGAS-style evaluator tính Faithfulness và Relevancy."""

    async def score(self, case, resp):
        """
        Mô phỏng tính toán RAGAS metrics.
        Trong thực tế sẽ sử dụng thư viện ragas để đánh giá.
        """
        import hashlib
        import random

        seed = int(hashlib.md5(case["question"].encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        answer = resp.get("answer", "")
        expected = case.get("expected_answer", "")
        contexts = resp.get("contexts", [])

        # Faithfulness: Câu trả lời có trung thực với context không?
        if contexts and any(c in answer for c in [ctx[:30] for ctx in contexts]):
            faithfulness = round(rng.uniform(0.7, 1.0), 3)
        elif "[Câu trả lời mẫu]" in answer:
            faithfulness = round(rng.uniform(0.1, 0.3), 3)
        else:
            faithfulness = round(rng.uniform(0.4, 0.8), 3)

        # Relevancy: Câu trả lời có liên quan đến câu hỏi không?
        if len(answer) > 20 and len(case["question"]) > 5:
            relevancy = round(rng.uniform(0.6, 1.0), 3)
        else:
            relevancy = round(rng.uniform(0.2, 0.5), 3)

        return {
            "faithfulness": faithfulness,
            "relevancy": relevancy,
        }


async def run_benchmark_with_results(agent_version: str, dataset: list):
    """Chạy benchmark cho 1 phiên bản Agent."""
    print(f"\n🚀 Khởi động Benchmark cho {agent_version}...")
    start_time = time.perf_counter()

    # Khởi tạo components
    agent = MainAgent(version="v1" if "V1" in agent_version else "v2")
    evaluator = ExpertEvaluator()
    judge = LLMJudge(models=["gpt-4o", "claude-3-5-sonnet"])
    retrieval_eval = RetrievalEvaluator(top_k=3)

    runner = BenchmarkRunner(agent, evaluator, judge, retrieval_eval)
    results = await runner.run_all(dataset, batch_size=10)

    total_time = time.perf_counter() - start_time
    total = len(results)

    # Tính metrics tổng hợp
    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail_count = total - pass_count

    avg_faithfulness = sum(r["ragas"]["faithfulness"] for r in results) / total
    avg_relevancy = sum(r["ragas"]["relevancy"] for r in results) / total
    avg_hit_rate = sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total
    avg_mrr = sum(r["ragas"]["retrieval"]["mrr"] for r in results) / total
    avg_judge_score = sum(r["judge"]["final_score"] for r in results) / total
    avg_agreement = sum(r["judge"]["agreement_rate"] for r in results) / total
    avg_latency = sum(r["latency"] for r in results) / total
    total_tokens = sum(r["tokens_used"] for r in results)
    total_cost = sum(r["cost_usd"] for r in results)

    # Summary
    summary = {
        "metadata": {
            "version": agent_version,
            "total": total,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pass_rate": round(pass_count / total * 100, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_runtime_seconds": round(total_time, 2),
        },
        "metrics": {
            "avg_score": round(avg_judge_score, 3),
            "avg_faithfulness": round(avg_faithfulness, 3),
            "avg_relevancy": round(avg_relevancy, 3),
            "hit_rate": round(avg_hit_rate, 3),
            "mrr": round(avg_mrr, 3),
            "agreement_rate": round(avg_agreement, 3),
            "avg_latency_seconds": round(avg_latency, 4),
        },
        "cost": {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_cost_per_eval_usd": round(total_cost / total, 6),
        },
        "difficulty_breakdown": {},
    }

    # Phân tích theo độ khó
    for diff in ["easy", "medium", "hard", "adversarial", "edge"]:
        diff_results = [r for r in results if r.get("metadata", {}).get("difficulty") == diff]
        if diff_results:
            summary["difficulty_breakdown"][diff] = {
                "total": len(diff_results),
                "pass_rate": round(
                    sum(1 for r in diff_results if r["status"] == "pass") / len(diff_results) * 100, 1
                ),
                "avg_score": round(
                    sum(r["judge"]["final_score"] for r in diff_results) / len(diff_results), 2
                ),
            }

    print(f"   ⏱️ Hoàn thành trong {total_time:.2f}s")
    print(f"   📊 Pass Rate: {pass_count}/{total} ({pass_count/total*100:.1f}%)")
    print(f"   🎯 Avg Score: {avg_judge_score:.2f}/5.0")
    print(f"   🔍 Hit Rate: {avg_hit_rate*100:.1f}%")
    print(f"   💰 Total Cost: ${total_cost:.4f}")

    return results, summary


async def main():
    print("=" * 60)
    print("🏭 AI EVALUATION FACTORY — Lab Day 14")
    print("=" * 60)

    # 1. Load Golden Dataset
    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng.")
        return

    print(f"📂 Đã load {len(dataset)} test cases từ Golden Dataset")

    # 2. Chạy Benchmark V1 (Base)
    v1_results, v1_summary = await run_benchmark_with_results("Agent_V1_Base", dataset)

    # 3. Chạy Benchmark V2 (Optimized)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized", dataset)

    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    # 4. Regression / Delta Analysis
    print("\n" + "=" * 60)
    print("📊 REGRESSION ANALYSIS (V1 vs V2)")
    print("=" * 60)

    regression = {}
    for metric in ["avg_score", "hit_rate", "mrr", "agreement_rate", "avg_faithfulness", "avg_relevancy"]:
        v1_val = v1_summary["metrics"].get(metric, 0)
        v2_val = v2_summary["metrics"].get(metric, 0)
        delta = v2_val - v1_val
        regression[metric] = {
            "v1": v1_val,
            "v2": v2_val,
            "delta": round(delta, 4),
            "improved": delta > 0
        }
        sign = "+" if delta >= 0 else ""
        status = "📈" if delta > 0 else ("📉" if delta < 0 else "➡️")
        print(f"   {status} {metric}: V1={v1_val:.3f} → V2={v2_val:.3f} (Δ {sign}{delta:.4f})")

    # 5. Release Gate Decision
    print("\n" + "=" * 60)
    score_delta = regression["avg_score"]["delta"]
    hit_delta = regression["hit_rate"]["delta"]
    cost_v1 = v1_summary["cost"]["total_cost_usd"]
    cost_v2 = v2_summary["cost"]["total_cost_usd"]
    cost_delta = cost_v2 - cost_v1

    # Gate logic: chấp nhận nếu score tăng HOẶC (giữ nguyên + giảm chi phí)
    quality_improved = score_delta > 0
    cost_reduced = cost_delta < 0
    no_regression = score_delta >= -0.1  # Cho phép giảm nhẹ 0.1

    gate_decision = "APPROVE" if (quality_improved or (no_regression and cost_reduced)) else "BLOCK"

    if gate_decision == "APPROVE":
        print("✅ RELEASE GATE: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
        reasons = []
        if quality_improved:
            reasons.append(f"Quality improved by {score_delta:+.3f}")
        if cost_reduced:
            reasons.append(f"Cost reduced by ${abs(cost_delta):.4f}")
        print(f"   Lý do: {', '.join(reasons)}")
    else:
        print("❌ RELEASE GATE: TỪ CHỐI (BLOCK RELEASE)")
        print(f"   Lý do: Score giảm {score_delta:.3f}, không đạt ngưỡng chất lượng")

    # Thêm regression info vào V2 summary
    v2_summary["regression"] = regression
    v2_summary["release_gate"] = {
        "decision": gate_decision,
        "score_delta": score_delta,
        "cost_delta": round(cost_delta, 4),
        "quality_improved": quality_improved,
        "cost_reduced": cost_reduced,
    }
    v2_summary["v1_summary"] = v1_summary

    # 6. Tạo Reports
    os.makedirs("reports", exist_ok=True)

    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Đã lưu: reports/summary.json")

    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "v1_results": v1_results,
            "v2_results": v2_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Đã lưu: reports/benchmark_results.json")

    # 7. Failure Analysis Summary
    failed_cases = [r for r in v2_results if r["status"] == "fail"]
    if failed_cases:
        print(f"\n⚠️ {len(failed_cases)} cases FAILED. Xem chi tiết trong analysis/failure_analysis.md")
        print("   Top 3 cases tệ nhất:")
        worst = sorted(failed_cases, key=lambda x: x["judge"]["final_score"])[:3]
        for i, w in enumerate(worst, 1):
            print(f"   {i}. [{w['id']}] Score: {w['judge']['final_score']:.1f} — {w['test_case'][:60]}...")

    print("\n" + "=" * 60)
    print("🏁 BENCHMARK HOÀN TẤT!")
    print(f"   Tổng thời gian: {v1_summary['metadata']['total_runtime_seconds'] + v2_summary['metadata']['total_runtime_seconds']:.1f}s")
    print(f"   Tổng chi phí: ${cost_v1 + cost_v2:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
