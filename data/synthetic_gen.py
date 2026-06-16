import json
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict

# Add Day09 src path to sys.path
day09_dir = Path(__file__).resolve().parents[1] / "Day09_Le-Ba-Chien-2A202600755"
src_dir = day09_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from rag.parser import parse_policy_markdown
from app.config import Settings
from provider import get_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

async def generate_qa_from_text(settings: Settings, chunks: List[dict], num_pairs_per_chunk: int = 2) -> List[Dict]:
    """
    Sử dụng LLM API để tạo các cặp (Question, Expected Answer, Context, Citation)
    từ các chunk tài liệu cho trước.
    """
    llm = get_chat_model(settings)
    qa_pairs = []
    
    prompt_template = """
Bạn là một chuyên gia tạo dữ liệu đánh giá hệ thống RAG. 
Hãy đọc đoạn tài liệu sau và tạo ra {num} câu hỏi và câu trả lời tương ứng.
Yêu cầu:
- Câu hỏi phải đa dạng (có thể là câu hỏi dễ, khó, hoặc câu hỏi lừa/adversarial đòi hỏi suy luận).
- Trả lời dưới định dạng JSON array:
[
  {{"question": "câu hỏi...", "expected_answer": "câu trả lời...", "difficulty": "easy/medium/hard"}}
]

Đoạn tài liệu:
{text}
"""

    print(f"Bắt đầu tạo câu hỏi từ {len(chunks)} chunks...")
    
    # Để tránh bị rate limit hoặc mất quá nhiều thời gian, giới hạn số chunk nếu cần.
    # Nhưng yêu cầu là 50+ cases, nếu có 25 chunks * 2 = 50 cases.
    for i, chunk in enumerate(chunks):
        if len(qa_pairs) >= 55:
            break
            
        print(f"Đang xử lý chunk {i+1}/{len(chunks)}...")
        text = chunk["rendered_text"]
        citation = chunk["citation"]
        
        prompt = prompt_template.format(num=num_pairs_per_chunk, text=text)
        messages = [
            SystemMessage(content="Bạn là trợ lý ảo tạo dữ liệu JSON hợp lệ. Chỉ trả về JSON array."),
            HumanMessage(content=prompt)
        ]
        
        try:
            # We use a blocking invoke in a separate thread for async
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: llm.invoke(messages))
            
            content = response.content
            # Extract JSON array
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                pairs = json.loads(json_match.group())
            else:
                pairs = json.loads(content)
                
            for p in pairs:
                p["expected_retrieval_ids"] = [citation]
                p["context"] = text
                # Normalize metadata
                diff = p.get("difficulty", "medium")
                p["metadata"] = {"difficulty": diff, "type": "policy"}
                qa_pairs.append(p)
                
        except Exception as e:
            print(f"Lỗi khi xử lý chunk {i+1}: {e}")
            
    return qa_pairs

async def main():
    settings = Settings.load()
    policy_path = settings.policy_path
    
    if not policy_path.exists():
        print(f"Không tìm thấy file: {policy_path}")
        return
        
    with open(policy_path, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
        
    chunks = parse_policy_markdown(markdown_text)
    
    # We want ~50 pairs. Assuming we have around 20 chunks, 3 pairs per chunk.
    qa_pairs = await generate_qa_from_text(settings, chunks, num_pairs_per_chunk=3)
    
    print(f"\nĐã tạo thành công {len(qa_pairs)} test cases.")
    
    with open("data/golden_set.jsonl", "w", encoding="utf-8") as f:
        for pair in qa_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    print("Done! Saved to data/golden_set.jsonl")

if __name__ == "__main__":
    asyncio.run(main())
