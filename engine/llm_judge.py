import asyncio
import re
import sys
from typing import Dict, Any
from pathlib import Path

# Add Day09 src path to sys.path
day09_dir = Path(__file__).resolve().parents[1] / "Day09_Le-Ba-Chien-2A202600755"
src_dir = day09_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from langchain_core.messages import HumanMessage
from app.config import Settings
from provider import get_chat_model
from provider.gemini import build_gemini_model

class LLMJudge:
    def __init__(self):
        self.settings = Settings.load()
        
        # Primary judge (from .env LLM_PROVIDER)
        try:
            self.judge_primary = get_chat_model(self.settings)
        except Exception as e:
            print(f"Warning: Primary judge init failed: {e}")
            self.judge_primary = None
            
        # Secondary judge (Gemini)
        try:
            from dataclasses import replace
            gemini_settings = replace(self.settings, model="gemini-3.1-flash-lite")
            self.judge_secondary = build_gemini_model(gemini_settings)
        except Exception as e:
            print(f"Warning: Secondary judge init failed (maybe missing GOOGLE_API_KEY?): {e}")
            # If Gemini fails, fallback to primary or None
            self.judge_secondary = self.judge_primary
            
        self.prompt_template = """
Bạn là một giám khảo AI có nhiệm vụ đánh giá câu trả lời của một chatbot hỗ trợ khách hàng.
Hãy so sánh [Câu trả lời của Chatbot] với [Câu trả lời đúng (Ground Truth)].
Đánh giá điểm số từ 1 đến 5 (1 = Tệ nhất, 5 = Tốt nhất) dựa trên 2 tiêu chí:
1. Accuracy: Sự chính xác của thông tin so với Ground Truth.
2. Tone: Giọng điệu chuyên nghiệp và lịch sự.

[Câu hỏi]: {question}
[Câu trả lời đúng]: {ground_truth}
[Câu trả lời của Chatbot]: {answer}

Bạn chỉ trả về MỘT điểm số nguyên từ 1 đến 5 cuối cùng để đại diện cho chất lượng câu trả lời.
Không giải thích gì thêm, hãy trả về theo định dạng JSON như sau:
{{"score": 4, "reasoning": "Lý do ngắn gọn..."}}
"""

    async def _evaluate_single_model(self, model, question: str, answer: str, ground_truth: str) -> int:
        if not model:
            return 3 # Default middle score if model is not available
            
        prompt = self.prompt_template.format(
            question=question,
            ground_truth=ground_truth,
            answer=answer
        )
        try:
            res = await model.ainvoke([HumanMessage(content=prompt)])
            content = res.content
            if isinstance(content, list):
                content = " ".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
            elif not isinstance(content, str):
                content = str(content)
            # Extract JSON
            import json
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return int(data.get("score", 3))
            
            # Fallback regex
            score_match = re.search(r'"score"\s*:\s*(\d)', content)
            if score_match:
                return int(score_match.group(1))
            return 3
        except Exception as e:
            print(f"Lỗi khi judge đánh giá: {e}")
            return 3

    async def evaluate_multi_judge(self, question: str, answer: str, ground_truth: str) -> Dict[str, Any]:
        """
        Gọi 2 model (Primary và Secondary).
        Tính toán sự sai lệch và Agreement Rate.
        """
        # Call both judges concurrently
        score_a_task = self._evaluate_single_model(self.judge_primary, question, answer, ground_truth)
        score_b_task = self._evaluate_single_model(self.judge_secondary, question, answer, ground_truth)
        
        score_a, score_b = await asyncio.gather(score_a_task, score_b_task)
        
        avg_score = (score_a + score_b) / 2.0
        
        # Agreement: 1.0 if diff is 0, 0.5 if diff is 1, 0.0 if diff >= 2
        diff = abs(score_a - score_b)
        if diff == 0:
            agreement = 1.0
        elif diff == 1:
            agreement = 0.5
        else:
            agreement = 0.0
            
        return {
            "final_score": avg_score,
            "agreement_rate": agreement,
            "individual_scores": {
                "judge_primary": score_a,
                "judge_secondary": score_b
            }
        }
