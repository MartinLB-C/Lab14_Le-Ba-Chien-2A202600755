from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from app.config import Settings
from app.state import ShoppingState
from provider import get_chat_model
from app.data_access import ShoppingDataStore, build_data_tools
from rag.embeddings import SentenceTransformerEmbeddings
from rag.vector_store import ChromaPolicyStore
from app.prompts import (
    SUPERVISOR_PROMPT,
    POLICY_WORKER_PROMPT,
    DATA_WORKER_PROMPT,
    RESPONSE_WORKER_PROMPT,
)


class ShoppingAssistant:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.load()

        # Load models and store
        self.llm = get_chat_model(self.settings)
        self.data_store = ShoppingDataStore(Path("data/order_customer_mock_data.json"))
        self.data_tools = build_data_tools(self.data_store)
        self.embedding_model = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
        self.policy_store = ChromaPolicyStore(Path("data/chroma"), self.embedding_model)

        # Define policy search tool
        @tool
        def search_policy(query: str) -> str:
            """Search the shopping policy."""
            hits = self.policy_store.search(query)
            return json.dumps(hits, ensure_ascii=False)

        self.policy_tool = search_policy
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        builder = StateGraph(ShoppingState)

        builder.add_node("supervisor", self._supervisor_node)
        builder.add_node("worker_1_policy", self._worker_1_policy_node)
        builder.add_node("worker_2_data", self._worker_2_data_node)
        builder.add_node("worker_3_response", self._worker_3_response_node)

        builder.set_entry_point("supervisor")

        def route_after_supervisor(state: ShoppingState):
            route = state.get("route", {})
            if route.get("status") == "clarification_needed":
                return "worker_3_response"
            if route.get("needs_policy"):
                return "worker_1_policy"
            if route.get("needs_data"):
                return "worker_2_data"
            return "worker_3_response"

        def route_after_policy(state: ShoppingState):
            route = state.get("route", {})
            if route.get("needs_data"):
                return "worker_2_data"
            return "worker_3_response"

        builder.add_conditional_edges(
            "supervisor",
            route_after_supervisor,
            ["worker_1_policy", "worker_2_data", "worker_3_response"]
        )
        builder.add_conditional_edges(
            "worker_1_policy",
            route_after_policy,
            ["worker_2_data", "worker_3_response"]
        )
        builder.add_edge("worker_2_data", "worker_3_response")
        builder.add_edge("worker_3_response", END)

        return builder.compile()

    def _supervisor_node(self, state: ShoppingState) -> ShoppingState:
        messages = [
            SystemMessage(content=SUPERVISOR_PROMPT),
            HumanMessage(content=state["question"])
        ]
        response = self.llm.invoke(messages)
        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                route_data = json.loads(json_match.group())
            else:
                route_data = json.loads(response.content)
        except Exception:
            route_data = {"status": "ok", "needs_policy": True, "needs_data": True}

        return {"route": route_data, "trace": [{"node": "supervisor", "output": route_data}]}

    def _worker_1_policy_node(self, state: ShoppingState) -> ShoppingState:
        llm_with_tools = self.llm.bind_tools([self.policy_tool])
        messages = [
            SystemMessage(content=POLICY_WORKER_PROMPT),
            HumanMessage(content=state["question"])
        ]
        response = llm_with_tools.invoke(messages)
        if response.tool_calls:
            messages.append(response)
            for tc in response.tool_calls:
                if tc["name"] == "search_policy":
                    tool_res = self.policy_tool.invoke(tc["args"])
                    messages.append(ToolMessage(content=str(tool_res), tool_call_id=tc["id"]))
            response = self.llm.invoke(messages)

        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                policy_result = json.loads(json_match.group())
            else:
                policy_result = json.loads(response.content)
        except Exception:
            policy_result = {"status": "not_found", "summary": response.content}

        return {"policy_result": policy_result, "trace": [{"node": "worker_1_policy", "output": policy_result}]}

    def _worker_2_data_node(self, state: ShoppingState) -> ShoppingState:
        llm_with_tools = self.llm.bind_tools(self.data_tools)
        messages = [
            SystemMessage(content=DATA_WORKER_PROMPT),
            HumanMessage(content=state["question"])
        ]
        response = llm_with_tools.invoke(messages)
        if response.tool_calls:
            messages.append(response)
            for tc in response.tool_calls:
                tool_fn = next((t for t in self.data_tools if t.name == tc["name"]), None)
                if tool_fn:
                    tool_res = tool_fn.invoke(tc["args"])
                    messages.append(ToolMessage(content=json.dumps(tool_res, ensure_ascii=False), tool_call_id=tc["id"]))
            response = self.llm.invoke(messages)

        try:
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                data_result = json.loads(json_match.group())
            else:
                data_result = json.loads(response.content)
        except Exception:
            data_result = {"status": "not_found", "summary": response.content}

        return {"data_result": data_result, "trace": [{"node": "worker_2_data", "output": data_result}]}

    def _worker_3_response_node(self, state: ShoppingState) -> ShoppingState:
        context = []
        route = state.get("route", {})
        policy_res = state.get("policy_result", {})
        data_res = state.get("data_result", {})

        context.append(f"Supervisor Route: {json.dumps(route, ensure_ascii=False)}")
        if route.get("needs_policy"):
            context.append(f"Policy Worker Result: {json.dumps(policy_res, ensure_ascii=False)}")
        if route.get("needs_data"):
            context.append(f"Data Worker Result: {json.dumps(data_res, ensure_ascii=False)}")

        messages = [
            SystemMessage(content=RESPONSE_WORKER_PROMPT),
            HumanMessage(content=f"Câu hỏi: {state['question']}\n\nContext:\n" + "\n".join(context))
        ]
        response = self.llm.invoke(messages)

        return {"final_answer": response.content, "trace": [{"node": "worker_3_response", "output": response.content}]}

    def ask(
        self,
        question: str,
        trace_file: Path | None = None,
        rebuild_index: bool = False,
    ) -> dict[str, Any]:
        if rebuild_index:
            self.policy_store.rebuild(Path("data/policy_mock_vi.md"))
        else:
            self.policy_store.ensure_index(Path("data/policy_mock_vi.md"))

        inputs = {"question": question, "trace": []}
        final_state = self.graph.invoke(inputs)

        if trace_file:
            trace_file.parent.mkdir(parents=True, exist_ok=True)
            with open(trace_file, 'w', encoding='utf-8') as f:
                json.dump(final_state.get("trace", []), f, ensure_ascii=False, indent=2)

        return final_state

    def run_batch(
        self,
        test_file: Path,
        output_dir: Path,
        rebuild_index: bool = False,
    ) -> dict[str, Any]:
        with open(test_file, 'r', encoding='utf-8') as f:
            tests = json.load(f)

        summary = {"total": len(tests), "passed": 0, "results": []}
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, t in enumerate(tests):
            q = t["question"]
            trace_path = output_dir / f"trace_{i}.json"
            try:
                res = self.ask(q, trace_file=trace_path, rebuild_index=(rebuild_index and i == 0))
                summary["results"].append({
                    "question": q,
                    "final_answer": res.get("final_answer"),
                    "route": res.get("route"),
                    "trace_file": str(trace_path)
                })
                # Basic check
                if res.get("final_answer"):
                    summary["passed"] += 1
            except Exception as e:
                summary["results"].append({
                    "question": q,
                    "error": str(e)
                })

        with open(output_dir / "summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        return summary
