import asyncio
from typing import List, Dict
import sys
import json
from pathlib import Path

# Add Day09 src path to sys.path
day09_dir = Path(__file__).resolve().parents[1] / "Day09_Le-Ba-Chien-2A202600755"
src_dir = day09_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.append(str(src_dir))

from app.graph import ShoppingAssistant

class MainAgent:
    """
    Day 09 ShoppingAssistant RAG Agent wrapper for Lab 14 Evaluation.
    """
    def __init__(self):
        self.name = "ShoppingAssistant-v2-Optimized"
        # We assume settings are properly configured in Day09's .env
        # and paths have been patched to use settings.
        self.assistant = ShoppingAssistant()
        
        # Ensure Chroma index is built once
        self.assistant.policy_store.ensure_index(self.assistant.settings.policy_path)

    async def query(self, question: str) -> Dict:
        """
        Executes the ShoppingAssistant RAG pipeline.
        Returns format compatible with Lab 14 evaluators.
        """
        # ShoppingAssistant is synchronous, so we run it in an executor to avoid blocking asyncio loop
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(None, lambda: self.assistant.ask(question, rebuild_index=False))
        
        # Extract the final answer
        answer = final_state.get("final_answer", "")
        
        # We need to extract retrieved_ids to compute Hit Rate and MRR.
        # Since policy chunks are retrieved by the policy_tool, we can either extract from trace
        # or do a parallel search. Given that our evaluation relies on what was *actually* retrieved,
        # we can just query the policy_store directly using the question to simulate the retriever's top-k hits.
        # Alternatively, since the policy tool queries the policy_store internally, we just query it.
        # Since the worker might refine the query, let's just query the policy store with the original question.
        # This is a standard approximation for RAG metrics on the retriever part.
        hits = self.assistant.policy_store.search(question, top_k=self.assistant.settings.top_k)
        
        contexts = [hit["content"] for hit in hits]
        retrieved_ids = [hit["citation"] for hit in hits]

        return {
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": self.assistant.settings.model,
                "provider": self.assistant.settings.provider,
                "route": final_state.get("route", {}),
                "trace": final_state.get("trace", [])
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        resp = await agent.query("Đơn hàng 1971 có được hoàn trả không?")
        print(json.dumps(resp, ensure_ascii=False, indent=2))
    asyncio.run(test())
