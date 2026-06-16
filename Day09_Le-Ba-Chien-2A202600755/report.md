# Project Implementation Report

## Task 1: Environment Setup & Foundation (Completed)
- **Status**: Completed
- **Details**:
  - Created `.env` file with configuration customized for Alibaba API (`LLM_PROVIDER=custom`). The base URL and placeholders were set up successfully.
  - Initialized this `report.md` file to log progress after each task.
  - Initialized `task.md` for task tracking.

## Task 2: Data Access & Worker 2 Tools (Completed)
- **Status**: Completed
- **Details**:
  - Implemented JSON parsing in `ShoppingDataStore` to load `data/order_customer_mock_data.json`.
  - Built O(1) in-memory dictionaries for `customer_by_id`, `order_by_id`, `orders_by_customer_id`, and `vouchers_by_customer_id`.
  - Implemented 4 robust data lookup tools (`get_customer_by_id`, `get_orders_by_customer_id`, `get_order_detail_by_order_id`, and `get_vouchers_by_customer_id`) that return standardized status dicts (`"ok"` or `"not_found"`).
  - Wrapped the 4 methods using Langchain's `@tool` decorator in `build_data_tools` with appropriate docstrings.

## Task 3: Policy RAG & Worker 1 (Completed)
- **Status**: Completed
- **Details**:
  - Implemented `parse_policy_markdown` in `src/rag/parser.py` to correctly extract hierarchical structures (`H2` and `H3`) and construct full context chunks along with `citation` tracking.
  - Implemented `ChromaPolicyStore` in `src/rag/vector_store.py` using `chromadb`.
  - Successfully connected the parser with the embedding model to build and persist the Chroma collection.
  - Implemented the `search` function to query the top-K relevant chunks based on semantic distance.

## Task 4: Agent Prompts (Completed)
- **Status**: Completed
- **Details**:
  - Rewrote the pseudo-code prompts in `src/app/prompts.py` into robust Vietnamese System Prompts for all 4 LLM agents.
  - `SUPERVISOR_PROMPT`: Instructed to strictly return JSON with routing flags (`needs_policy`, `needs_data`) and forced it to check for missing IDs to return `clarification_needed`.
  - `POLICY_WORKER_PROMPT`: Demanded the agent to use the search tool and structure answers with `summary`, `facts`, and `citations`.
  - `DATA_WORKER_PROMPT`: Instructed to use the 4 specific lookup tools and enforce standardized JSON responses indicating success or missing fields.
  - `RESPONSE_WORKER_PROMPT`: Mandated output in one of three strict text formats (`Success`, `Clarification`, `Not found`) depending on the context provided by upstream workers.

## Task 5: LangGraph Workflow Orchestration (Completed)
- **Status**: Completed
- **Details**:
  - Integrated the LangGraph setup entirely inside the `ShoppingAssistant` class in `src/app/graph.py`.
  - Designed the `StateGraph` with 4 main nodes: `supervisor`, `worker_1_policy`, `worker_2_data`, and `worker_3_response`.
  - Implemented conditional routing functions (`route_after_supervisor` and `route_after_policy`) to intelligently direct the execution flow based on the JSON decisions of the LLMs.
  - Successfully bound the respective `@tool` definitions (`policy_tool` and `data_tools`) to the LLM within each worker's node via `bind_tools`.
  - Handled automated execution of `tool_calls` recursively so models can access actual data/policy, append results, and self-summarize.
  - Implemented the `ask()` entry point to rebuild the ChromaDB when requested and trace node histories.
  - Implemented the `run_batch()` function to loop through predefined test JSON datasets and record full traces for testing.

## Task 6: Batch Testing & Refinement (Completed)
- **Status**: Completed
- **Details**:
  - Implemented the CLI tool in `src/app/cli.py` to parse arguments and hook into the `ShoppingAssistant`.
  - Executed the `--batch` suite over `data/test.json`.
  - Validated that results properly generated `outputs/summary.json` alongside detailed per-question traces.

## Task 7: User Interface (UI) - Streamlit App (Completed)
- **Status**: Completed
- **Details**:
  - Developed an interactive web interface using `Streamlit` in `app/main.py` acting as the frontend for the multi-agent system.
  - Implemented a conversational chat interface keeping session history (`st.session_state.messages`).
  - Integrated the backend `ShoppingAssistant` smoothly to handle user queries and display results in real-time.
  - Built a dynamic sidebar that automatically loads predefined questions from `data/test.json` to allow quick testing without manual typing.
  - Added an expandable section ("Trace") for each assistant response to expose the LangGraph internal reasoning and trace logs for debugging and transparency.
  - Included functionalities to clear chat history and manage session state seamlessly.
