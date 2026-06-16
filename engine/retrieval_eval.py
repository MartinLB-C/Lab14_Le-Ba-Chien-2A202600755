from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 4) -> float:
        """
        Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        """
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank.
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        """
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(self, dataset: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu (trên các kết quả đã được agent thực thi).
        Dataset cần có trường 'expected_retrieval_ids' và 'retrieved_ids'.
        """
        total = len(dataset)
        if total == 0:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0}
            
        hit_rate_sum = 0.0
        mrr_sum = 0.0
        
        for case in dataset:
            expected = case.get("expected_retrieval_ids", [])
            retrieved = case.get("retrieved_ids", [])
            hit_rate_sum += self.calculate_hit_rate(expected, retrieved)
            mrr_sum += self.calculate_mrr(expected, retrieved)
            
        return {
            "avg_hit_rate": hit_rate_sum / total,
            "avg_mrr": mrr_sum / total
        }
