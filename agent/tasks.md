# Multi-Agent Migration Tasks

## Phase 1: Infrastructure & Dependencies
- [x] **Update Dependencies**: Add `langgraph` and `duckduckgo-search` to `requirements.txt`.
- [x] **Environment Setup**: Ensure API keys (OpenAI/DeepSeek, FRED, etc.) are correctly configured for the new architecture.

## Phase 2: Core Implementation (LangGraph)
- [x] **Define Graph State**: Create `agent/core/state.py` to define `AgentState` (TypedDict).
- [x] **Implement Node Wrappers**: Create helper functions in `agent/core/nodes.py` to wrap Skills into LangGraph Nodes.
- [x] **Implement Business Manager**:
    - [x] Design System Prompt for the Manager.
    - [x] Implement the Routing logic (LLM call -> JSON/Function -> Next Node).
- [x] **Implement Web Search Skill**:
    - [x] Create `skills/web_search_tool/`.
    - [x] Implement `WebSearchSkill` using `DuckDuckGoSearchRun`.
- [x] **Construct the Graph**:
    - [x] Create `agent/core/graph.py`.
    - [x] Add all Nodes (Manager, Macro, Market, Sentiment, Search).
    - [x] Define Conditional Edges based on Manager's output.
    - [x] Compile the workflow.

## Phase 3: Integration
- [x] **Update Agent Entrypoint**: Modify `agent/core/agent.py` to replace `AgentExecutor` with the compiled Graph Runnable.
- [x] **API Adaptation**: Ensure `agent/main.py` and `backend/api_server.py` can handle the Graph's output format (streaming vs static).

## Phase 4: Verification & Testing
- [x] **Unit Tests**: Test individual Nodes (mocking LLM/Tools).
- [x] **Integration Tests**: Run complex queries covering multiple agents.
    - [x] *Case 1*: "Analyze Apple's stock" (Market + Sentiment)
    - [x] *Case 2*: "Impact of Fed rates on Gold" (Macro + Market)
    - [x] *Case 3*: "Why is stock X halted?" (Web Search)
- [x] **Performance Tuning**: Adjust Prompts and Recursion Limit based on test results.
