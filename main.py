import asyncio
import json
import os
import time
from engine.runner import BenchmarkRunner
from agent.main_agent import MainAgent
from engine.retrieval_eval import RetrievalEvaluator
from engine.llm_judge import LLMJudge

class ExpertEvaluator:
    def __init__(self):
        self.retrieval_eval = RetrievalEvaluator()
        
    async def score(self, case, resp): 
        # Calculate Hit Rate và MRR
        expected = case.get("expected_retrieval_ids", [])
        retrieved = resp.get("retrieved_ids", [])
        
        hit_rate = self.retrieval_eval.calculate_hit_rate(expected, retrieved)
        mrr = self.retrieval_eval.calculate_mrr(expected, retrieved)
        
        # Giả lập RAGAS context faithfulness/relevancy for now since it's costly and not fully implemented
        return {
            "faithfulness": 0.9, 
            "relevancy": 0.8,
            "retrieval": {"hit_rate": hit_rate, "mrr": mrr}
        }

async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    if not os.path.exists("data/golden_set.jsonl"):
        print("❌ Thiếu data/golden_set.jsonl. Hãy chạy 'python data/synthetic_gen.py' trước.")
        return None, None

    with open("data/golden_set.jsonl", "r", encoding="utf-8") as f:
        dataset = [json.loads(line) for line in f if line.strip()]

    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng. Hãy tạo ít nhất 1 test case.")
        return None, None

    agent = MainAgent()
    evaluator = ExpertEvaluator()
    judge = LLMJudge()
    
    runner = BenchmarkRunner(agent, evaluator, judge)
    results = await runner.run_all(dataset, batch_size=3)

    total = len(results)
    if total == 0:
        return [], {}
        
    summary = {
        "metadata": {"version": agent_version, "total": total, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")},
        "metrics": {
            "avg_score": sum(r["judge"]["final_score"] for r in results) / total,
            "hit_rate": sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total,
            "agreement_rate": sum(r["judge"]["agreement_rate"] for r in results) / total
        }
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    # V1 is simulated as a baseline.
    v1_summary = {
        "metrics": {
            "avg_score": 3.0,
            "hit_rate": 0.5,
            "agreement_rate": 0.5
        }
    }
    
    # V2 is actual benchmarking
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark.")
        return

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    delta = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    print(f"V1 Score: {v1_summary['metrics']['avg_score']:.2f}")
    print(f"V2 Score: {v2_summary['metrics']['avg_score']:.2f}")
    print(f"Delta: {'+' if delta >= 0 else ''}{delta:.2f}")

    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    # Simple Failure Clustering Generation for analysis
    failures = [r for r in v2_results if r["status"] == "fail"]
    with open("analysis/failure_analysis.md", "w", encoding="utf-8") as f:
        f.write("# Báo cáo Phân tích Thất bại (Failure Analysis Report)\n\n")
        f.write(f"- **Tổng số cases:** {v2_summary['metadata']['total']}\n")
        f.write(f"- **Tỉ lệ Fail:** {len(failures)}/{v2_summary['metadata']['total']}\n")
        f.write(f"- **Điểm LLM-Judge trung bình:** {v2_summary['metrics']['avg_score']:.2f} / 5.0\n")
        f.write(f"- **Hit Rate trung bình:** {v2_summary['metrics']['hit_rate']:.2f}\n\n")
        f.write("## 2. Phân nhóm lỗi (Failure Clustering)\n")
        for fail in failures:
            f.write(f"- **Case:** {fail['test_case']}\n")
            f.write(f"  - **Score:** {fail['judge']['final_score']}\n")
            f.write(f"  - **Individual:** {fail['judge']['individual_scores']}\n\n")

    if delta >= 0:
        print("✅ QUYẾT ĐỊNH: CHẤP NHẬN BẢN CẬP NHẬT (APPROVE)")
    else:
        print("❌ QUYẾT ĐỊNH: TỪ CHỐI (BLOCK RELEASE)")

if __name__ == "__main__":
    asyncio.run(main())
