"""简单的 backend/skills Agent CLI Demo

用途：
- 在 `backend/tests` 目录下提供一个与业务代码解耦的测试脚本
- 使用 LangChain 对话 Agent，通过 CLI 与用户交互
- **只使用 `backend/skills/` 目录下的 skill**（如 market-data、macro-economy、web-search 等）
- 这些 skill 通过各自目录下的脚本执行（例如 `backend/skills/market-data/scripts/market_data.py`）
- LLM 等配置从项目根目录的 `.config.yaml` / `~/.config.yaml` 等路径读取（由 `ConfigLoader` 负责）

运行方式示例（在项目根目录）：
- `python backend/tests/skills_agent_cli.py`

注意：
- 这是一个测试 / demo，与主项目服务无直接耦合，仅用于快速验证 backend/skills 的行为。
"""

import logging
import subprocess
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Optional, Type

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# 为了能够导入 backend 模块，这里把项目根目录加入 sys.path
CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent
PROJECT_ROOT = CURRENT_FILE.parents[2]  # backend/tests/skills_agent_cli.py -> backend/tests -> backend -> root

if str(PROJECT_ROOT) not in sys.path:
    # sys.path.insert(0, str(PROJECT_ROOT))
    pass


import os
import yaml
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

def _load_config_dict() -> Dict:
    """手动读取配置，不依赖 backend 模块"""
    # 优先尝试 .config.yaml，其次是 config.yaml，最后是 ~/.config.yaml
    config_paths = [
        PROJECT_ROOT / ".config.yaml",
        PROJECT_ROOT / "config.yaml",
        Path.home() / ".config.yaml",
    ]
    for path in config_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    if data:
                        print(f"[CLI] 已加载配置: {path}")
                        return data
            except Exception as e:
                logging.warning(f"读取配置失败 {path}: {e}")
    print("[CLI] 未找到有效配置文件，将仅依赖环境变量或默认值")
    return {}

def _build_llm():
    """构建 LLM 实例，独立于 backend 业务逻辑"""
    # 尝试加载 .env 文件
    load_dotenv(PROJECT_ROOT / ".env")
    
    config = _load_config_dict()
    
    # 优先使用 siliconflow (DeepSeek)
    api_key = config.get("api_keys", {}).get("siliconflow") or os.environ.get("SILICONFLOW_API_KEY")
    base_url = "https://api.siliconflow.cn/v1"
    model = "deepseek-ai/DeepSeek-V3"  # 默认使用 DeepSeek V3

    # 回退到 OpenAI
    if not api_key:
        api_key = config.get("api_keys", {}).get("openai") or os.environ.get("OPENAI_API_KEY")
        base_url = config.get("api_url") or os.environ.get("OPENAI_API_BASE")
        model = config.get("model", "gpt-4o")

    if not api_key:
        print("\n[警告] 未找到 OpenAI API Key，请确保 .config.yaml 或环境变量 OPENAI_API_KEY 已设置。")
        print("尝试使用空 Key 继续（可能会报错）...")
        api_key = "sk-placeholder"
    
    return ChatOpenAI(
        model=model,
        temperature=0.3,
        api_key=api_key,
        base_url=base_url,
    )


class SkillQueryInput(BaseModel):
    query: str = Field(description="传入技能的查询或指令字符串")

class ShellCommandInput(BaseModel):
    command: str = Field(description="要执行的Shell命令字符串")


class _LazySkillTool(BaseTool):
    args_schema: Type[BaseModel] = SkillQueryInput
    name: str
    description: str
    _skill_path: Path
    _skill_module: Optional[object] = None
    _main_handle: Optional[object] = None

    def __init__(self, skill_path: Path, name: str, description: str):
        super().__init__(name=name, description=description)
        self._skill_path = skill_path

    def _ensure_adapter(self):
        if self._main_handle is None:
            parent = self._skill_path.parent.absolute()
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            module_name = self._skill_path.name
            pkg = importlib.import_module(module_name)
            mod = importlib.import_module(f"{module_name}.skill")
            if not hasattr(mod, "main_handle"):
                raise RuntimeError(f"{module_name}.skill 未找到 main_handle")
            self._skill_module = mod
            self._main_handle = mod.main_handle

    def _run(self, query: str) -> str:  # type: ignore[override]
        self._ensure_adapter()
        try:
            result = self._main_handle(query)
        except Exception as exc:  # noqa: BLE001
            return f"Skill 执行失败: {exc}"
        try:
            import json
            return json.dumps(result, ensure_ascii=False, indent=2, default=str)
        except Exception:
            return str(result)

    async def _arun(self, query: str) -> str:  # type: ignore[override]
        return self._run(query)

class _ShellCLITool(BaseTool):
    args_schema: Type[BaseModel] = ShellCommandInput
    name: str = "shell_exec"
    description: str = "执行Shell命令，用于运行各技能的CLI脚本或读取文档（如 cat SKILL.md）。"

    def _run(self, command: str) -> str:  # type: ignore[override]
        if not command:
            return "命令为空"
        try:
            completed = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as exc:  # noqa: BLE001
            return f"执行失败: {exc}"
        if completed.returncode != 0:
            return f"退出码 {completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        return completed.stdout or "(无输出)"

    async def _arun(self, command: str) -> str:  # type: ignore[override]
        return self._run(command)


def _discover_skill_packages() -> List[Path]:
    skills_dir = PROJECT_ROOT / "skills"
    if not skills_dir.exists():
        return []
    return [p for p in skills_dir.iterdir() if (p / "skill.py").exists()]

def _discover_skill_docs() -> List[Path]:
    docs_dir = PROJECT_ROOT / "backend" / "skills"
    if not docs_dir.exists():
        return []
    return [p for p in docs_dir.iterdir() if (p / "SKILL.md").exists()]

def _parse_skill_md(md_path: Path) -> Dict[str, str]:
    try:
        content = md_path.read_text(encoding="utf-8")
    except Exception:
        return {"name": md_path.parent.name, "description": ""}
    name: Optional[str] = None
    description: Optional[str] = None
    import re
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if m:
        yaml_block = m.group(1)
        nm = re.search(r"\n?name:\s*(.+)", yaml_block)
        dm = re.search(r"\n?description:\s*(.+)", yaml_block)
        if nm:
            name = nm.group(1).strip()
        if dm:
            description = dm.group(1).strip()
    if not name:
        h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if h1:
            name = h1.group(1).strip()
    if not description:
        paras = [line.strip() for line in content.splitlines()]
        # 找到第一个非标题的非空段落
        for line in paras:
            if not line or line.startswith("#") or line.startswith("---"):
                continue
            description = line
            break
    return {"name": name or md_path.parent.name, "description": description or ""}

def _build_skills_prompt() -> str:
    lines = []
    lines.append(f"当前工作目录: {PROJECT_ROOT}")
    lines.append("你是一个仅有一个工具（shell_exec）的助手。")
    lines.append("技能采用渐进式披露：启动时仅提供以下 YAML 描述；需要使用技能时，请先用 shell_exec 读取对应 SKILL.md 了解命令用法，再用 shell_exec 执行脚本。")
    lines.append("可读取文档示例：cat backend/skills/<skill>/SKILL.md")
    lines.append("执行脚本示例（请确保路径正确）：python backend/skills/market-data/scripts/market_data.py quote 600036")
    lines.append("注意：")
    lines.append("1. 执行命令前，请先确认文件路径是否存在。")
    lines.append("2. 你的工作目录是项目根目录，所有路径请使用相对于根目录的相对路径（如 backend/skills/...）。")
    lines.append("3. 如果执行失败，请检查输出中的错误信息并尝试修正命令。")
    lines.append("4. **必须** 打印出你打算执行的命令以便调试。")
    lines.append("技能说明：")
    for doc_dir in _discover_skill_docs():
        info = _parse_skill_md(doc_dir / "SKILL.md")
        lines.append("---")
        lines.append(f"name: {info['name']}")
        lines.append(f"description: {info['description']}")
        lines.append("---")
    
    prompt = "\n".join(lines)
    print(f"\n[DEBUG] System Prompt:\n{prompt}\n")  # 打印 System Prompt 方便调试
    return prompt


def _make_skill_tools() -> List[BaseTool]:
    tools: List[BaseTool] = []
    for pkg in _discover_skill_packages():
        tool_name = pkg.name
        description = "标准 Skill，按需加载"
        tools.append(
            _LazySkillTool(
                skill_path=pkg,
                name=tool_name,
                description=description,
            )
        )
    return tools



def _build_tools() -> List[BaseTool]:
    """构建可用的工具列表。

    注意：
    - 仅暴露一个 Shell 执行工具；技能通过文档披露与脚本调用完成
    """

    return [_ShellCLITool()]


def _print_skills_help(tools: List[object]) -> None:
    print("\n当前技能（文档披露层）：")
    for doc_dir in _discover_skill_docs():
        info = _parse_skill_md(doc_dir / "SKILL.md")
        print(f"- {info['name']}: {info['description']}")

    print("""
用法示例：
- 直接输入需求，如“查询AAPL的最新行情”、“分析000001的情绪”
- 详细指令参考各技能包的 SKILL.md
""")


def _print_trajectory(intermediate_steps) -> None:
    """打印 Agent 调用工具的轨迹信息（Thought / Action / Observation 的简化版）。"""

    if not intermediate_steps:
        return

    print("\n=== 工具调用轨迹（仅供调试观察使用） ===")
    for idx, step in enumerate(intermediate_steps, start=1):
        # LangChain 默认返回形如 (AgentAction, observation) 的二元组
        if isinstance(step, (list, tuple)) and len(step) >= 2:
            action, observation = step[0], step[1]
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", "")
            print(f"[Step {idx}] 工具: {tool_name}")
            print(f"  输入: {tool_input}")
            # 只打印 observation 的前若干字符，避免刷屏
            obs_text = str(observation)
            if len(obs_text) > 300:
                obs_text = obs_text[:300] + "... (截断)"
            print(f"  输出: {obs_text}\n")
        else:
            # 兜底打印原始 step 内容
            print(f"[Step {idx}] 原始 step: {step}\n")


def _run_shell_command(command: str) -> None:
    """在 CLI 中直接执行一个 shell 命令。

    例如：`!python backend/skills/market-data/scripts/market_data.py quote 600036`
    用于直接运行 backend/skills 下的原始脚本，方便做低层级调试。
    """

    import subprocess

    if not command:
        return

    print(f"[CLI] 执行命令: {command}")
    try:
        completed = subprocess.run(
            command,
            shell=True,
            check=False,
        )
        if completed.returncode != 0:
            print(f"[CLI] 命令退出码: {completed.returncode}")
    except Exception as exc:  # noqa: BLE001
        print(f"[CLI] 执行命令失败: {exc}")


def main() -> None:
    """启动 Skills Agent CLI，对话入口。"""

    logging.basicConfig(level=logging.INFO)

    # 构建工具与 LLM Agent
    tools = _build_tools()

    llm = _build_llm()

    checkpointer = InMemorySaver()
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=_build_skills_prompt(),
        checkpointer=checkpointer,
    )

    print("""\n=== Skills Agent CLI Demo ===
说明：
- 这是一个与业务无关的测试 Agent，用于在命令行里尝试调用 backend/skills 下的各类 skill。
- 输入自然语言即可与 Agent 对话。
- 输入 `skills` 或 `help` 可以查看当前可用的技能列表。
- 以 `!` 开头的输入会被当作 Shell 命令直接执行，例如：
    !python backend/skills/market-data/scripts/market_data.py quote 600036
- 输入 `exit` / `quit` / `q` 退出。
""")

    _print_skills_help(tools)

    while True:
        try:
            user_input = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见 👋")
            break

        if not user_input:
            continue

        lower = user_input.lower()
        if lower in {"exit", "quit", "q"}:
            print("退出 Skills Agent CLI。")
            break

        # 查看技能列表 / 渐进式披露基础信息
        if lower in {"help", "skills", "技能", "?"}:
            _print_skills_help(tools)
            continue

        # 以 `!` 开头的命令，直接走 Shell （用于执行原始 skill 脚本等）
        if user_input.startswith("!"):
            _run_shell_command(user_input[1:].strip())
            continue

        # 走 LangChain Agent 对话 + Tool 调用
        try:
            # create_agent 返回的 graph 需要 thread_id 配置
            config = {"configurable": {"thread_id": "cli-session"}}
            # 输入需要是 messages 列表
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            # invoke 返回的是最终状态 state
            final_state = agent.invoke(inputs, config=config)
            
            # 从 messages 中提取最后一条 AI 回复
            messages = final_state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                output = last_msg.content
            else:
                output = "(无回复)"
            
            # intermediate_steps 在 LangGraph 中对应消息历史里的 ToolMessage
            # 这里简单处理，暂不打印完整轨迹，或从 history 提取
            intermediate_steps = [] 

        except Exception as exc:  # noqa: BLE001
            print(f"Agent 执行出错: {exc}")
            continue

        # 主回复
        print(f"助手> {output}")


if __name__ == "__main__":
    main()
