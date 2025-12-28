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
        pass

    async def on_agent_action(self, action: Any, **kwargs: Any) -> Any:
        # Log agent thinking process (Action)
        log = f"Agent Action: {action.tool} with {action.tool_input}"
        self.job_manager.append_event(self.job_id, "log", {"message": log})
        await stream_manager.push_event(
            self.job_id, "log", json.dumps({"level": "info", "message": log})
        )

    async def on_agent_finish(self, finish: Any, **kwargs: Any) -> Any:
        # print(f"Agent finish running with result: {finish.return_values}")
        # Save to DB
        self.job_manager.append_event(
            self.job_id,
            "status",
            {"status": "completed", "output": finish.return_values},
        )

        # Sync to Memory STM
        output_content = finish.return_values.get("output", "")
        if output_content:
            self.memory_client.add_memory(
                str(output_content), role="agent", metadata={"job_id": self.job_id}
            )
            
        # 触发记忆异步结算 (STM -> MTM/LTM)
        task_id = self.memory_client.finalize()
        if task_id:
            logger.info(f"Memory Finalize Task started for job {self.job_id}. Task ID: {task_id}")
        else:
            logger.warning(f"Memory Finalize Task failed to start for job {self.job_id}")

        # Stream the full completion status including the final answer
        try:
            output_content = finish.return_values.get("output", "")
            # Ensure output_content is a string
            if not isinstance(output_content, str):
                output_content = str(output_content)

            await stream_manager.push_event(
                self.job_id,
                "status",
                json.dumps(
                    {"status": "completed", "output": output_content}, default=str
                ),
            )  # Use default=str to handle non-serializable objects
        except Exception as e:
            print(f"Error streaming finish status: {e}")
            await stream_manager.push_event(
                self.job_id,
                "status",
                json.dumps(
                    {
                        "status": "completed",
                        "output": "Task completed (output serialization failed)",
                    }
                ),
            )

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
