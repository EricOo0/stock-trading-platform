from typing import Any, Dict, List, Optional
from uuid import UUID
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult
from backend.app.services.research.job_manager import JobManager
from backend.app.services.research.stream_manager import stream_manager
from backend.infrastructure.adk.core.memory_client import MemoryClient
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ResearchAgentCallback(AsyncCallbackHandler):
    def __init__(self, job_id: str, user_id: str = "default_user"):
        self.job_id = job_id
        self.user_id = user_id
        self.job_manager = JobManager()
        self.memory_client = MemoryClient(user_id=user_id, agent_id="research_agent")
        # run_id -> {name, input}
        self.tool_runs: Dict[UUID, Dict[str, str]] = {}
        self.current_thought_buffer: str = ""

    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        print(f"LLM start running with prompts: {prompts}")
        self.current_thought_buffer = ""  # Reset buffer
        pass

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM ends running."""
        # Check if we have buffered thought content
        if self.current_thought_buffer:
            self.job_manager.append_event(
                self.job_id, "thought", {"delta": self.current_thought_buffer}
            )
            self.current_thought_buffer = ""  # Reset
        pass

    async def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Run when LLM errors."""
        if self.current_thought_buffer:
            self.job_manager.append_event(
                self.job_id, "thought", {"delta": self.current_thought_buffer}
            )
            self.current_thought_buffer = ""

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        self.current_thought_buffer += token
        await stream_manager.push_event(
            self.job_id, "thought", json.dumps({"delta": token})
        )

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, *, run_id: UUID, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""
        tool_name = serialized.get("name")
        print(f"Tool start running with input: {input_str}, tool_name: {tool_name}")

        # Track tool run for artifact generation in on_tool_end
        self.tool_runs[run_id] = {"name": tool_name, "input": input_str}

        self.job_manager.append_event(
            self.job_id, "tool_start", {"tool": tool_name, "input": input_str}
        )
        await stream_manager.push_event(
            self.job_id,
            "tool_start",
            json.dumps({"tool": tool_name, "args": input_str}),
        )

    async def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Run when tool ends running."""
        # Output can be a string or a ToolMessage object (or other types)
        # Ensure it's serializable
        if hasattr(output, "content"):
            output_str = str(output.content)
        else:
            output_str = str(output)

        self.job_manager.append_event(self.job_id, "tool_end", {"output": output_str})
        await stream_manager.push_event(
            self.job_id,
            "log",
            json.dumps(
                {"level": "success", "message": f"Tool finished: {output_str[:100]}..."}
            ),
        )

        # Check for Artifact Generation
        tool_info = self.tool_runs.get(run_id)
        if tool_info:
            tool_name = tool_info.get("name")
            await self._try_create_artifact(tool_name, output_str)
            # Cleanup
            del self.tool_runs[run_id]

    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        # 识别是否为根 Chain 的结束
        # 1. 如果 parent_run_id 为 None，通常是根
        # 2. 如果 outputs 包含最终回答的特征
        
        parent_run_id = kwargs.get("parent_run_id")
        if parent_run_id is not None:
            # 忽略子链（如工具调用、内部节点等）
            return

        logger.info(f"on_chain_end triggered for job {self.job_id}. Processing memory sync.")
        
        output_content = ""
        # 尝试从 LangGraph 输出中提取最终回答
        # 常见格式: {"messages": [...]} 或 {"output": "..."}
        if isinstance(outputs, dict):
            if "messages" in outputs and isinstance(outputs["messages"], list) and outputs["messages"]:
                last_msg = outputs["messages"][-1]
                if hasattr(last_msg, "content"):
                    output_content = str(last_msg.content)
            elif "output" in outputs:
                output_content = str(outputs["output"])
        
        if not output_content:
            logger.warning(f"on_chain_end: Could not extract output content for job {self.job_id}")
            return

        # 执行记忆同步 (STM)
        try:
            self.memory_client.add_memory(
                str(output_content), role="agent", metadata={"job_id": self.job_id}
            )
            logger.info(f"Saved agent output to STM for job {self.job_id} (via on_chain_end)")
        except Exception as e:
            logger.error(f"Failed to save STM in on_chain_end: {e}")

        # 更新 Job 状态
        try:
            self.job_manager.update_job_status(self.job_id, "completed", output=output_content)
            logger.info(f"Updated job status to completed for job {self.job_id}")
        except Exception as e:
            logger.error(f"Failed to update job status in on_chain_end: {e}")

        # 推流给前端
        try:
            await stream_manager.push_event(
                self.job_id,
                "status",
                json.dumps(
                    {"status": "completed", "output": output_content}, default=str
                ),
            )
            logger.info(f"Streamed completed status for job {self.job_id}")
        except Exception as e:
            logger.error(f"Failed to stream completion status in on_chain_end: {e}")

        # 触发记忆结算 (STM -> MTM/LTM)
        try:
            task_id = self.memory_client.finalize()
            if task_id:
                logger.info(f"Memory Finalize Task started for job {self.job_id}. Task ID: {task_id}")
            else:
                logger.warning(f"Memory Finalize Task failed to start for job {self.job_id}")
        except Exception as e:
            logger.error(f"Failed to finalize memory in on_chain_end: {e}")


    async def on_agent_action(self, action: Any, **kwargs: Any) -> Any:
        # Log agent thinking process (Action)
        log = f"Agent Action: {action.tool} with {action.tool_input}"
        self.job_manager.append_event(self.job_id, "log", {"message": log})
        await stream_manager.push_event(
            self.job_id, "log", json.dumps({"level": "info", "message": log})
        )

    async def on_agent_finish(self, finish: Any, **kwargs: Any) -> Any:
        """
        Run on agent end.
        Note: With LangGraph, this callback is typically NOT triggered.
        The logic has been migrated to `on_chain_end` (for memory and status streaming).
        """
        pass

    async def _try_create_artifact(self, tool_name: str, output_str: str):
        """
        Try to parse the tool output and create a visualization artifact if applicable.
        """
        try:
            # Only process specific data tools
            artifact_type = None
            title = "Data Artifact"

            if tool_name == "get_market_data":
                artifact_type = "kline"
                title = "Stock Market Data"
            elif tool_name == "get_financial_metrics":
                artifact_type = "financial_table"
                title = "Financial Metrics"
            elif tool_name == "get_macro_economic_data":
                artifact_type = "macro_chart"
                title = "Macro Economic Data"
            elif tool_name == "get_company_report":
                artifact_type = "pdf_preview"
                title = "Financial Report"
            elif tool_name == "get_discussion_wordcloud":
                artifact_type = "wordcloud"
                title = "Social Media Sentiment"
            elif tool_name == "get_technical_indicators":
                artifact_type = "technical_indicators"
                title = "Technical Indicators"
            elif tool_name == "search_google":
                artifact_type = "search_results"
                title = "Search References"

            if not artifact_type:
                return

            # Try parsing JSON
            # Note: Tools return JSON strings, but sometimes might wrap error messages or text
            if not output_str.strip().startswith(("{", "[")):
                return

            data = json.loads(output_str)

            # Simple validation: Must be non-empty dict or list
            if not data:
                return
            if isinstance(data, dict) and "error" in data:
                return
            if isinstance(data, str):  # Double encoded?
                return

            # Construct Artifact Payload
            payload = {"type": artifact_type, "title": title, "data": data}

            # 1. Save to DB
            self.job_manager.create_artifact(
                self.job_id, artifact_type, data, title=title
            )

            # 2. Push to Frontend
            await stream_manager.push_event(
                self.job_id, "artifact", json.dumps(payload, default=str)
            )

            logger.info(f"Generated artifact {artifact_type} from tool {tool_name}")

        except json.JSONDecodeError:
            pass  # Not JSON, ignore
        except Exception as e:
            logger.error(f"Error creating artifact for {tool_name}: {e}")
