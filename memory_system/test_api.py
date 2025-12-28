import requests
import time
import json

BASE_URL = "http://localhost:10000/api/v1"
USER_ID = "test_user_001"
AGENT_ID = "research_agent"

def test_memory_pipeline():
    print("🚀 开始记忆系统 API 联调测试...")

    # 1. 添加短期记忆 (STM)
    print("\n1. 正在同步对话到 STM...")
    add_payload = {
        "user_id": USER_ID,
        "agent_id": AGENT_ID,
        "content": "我是一个激进型投资者，喜欢投资半导体和AI领域的成长股。我认为NVIDIA (NVDA) 在AI算力领域有绝对统治力。",
        "metadata": {
            "role": "user",
            "importance": 0.8
        }
    }
    response = requests.post(f"{BASE_URL}/memory/add", json=add_payload)
    print(f"   Status: {response.status_code}, Response: {response.json()}")

    # 2. 获取上下文 (验证连贯性)
    print("\n2. 正在获取增强上下文...")
    context_payload = {
        "user_id": USER_ID,
        "agent_id": AGENT_ID,
        "query": "分析一下半导体行业的投资机会"
    }
    response = requests.post(f"{BASE_URL}/memory/context", json=context_payload)
    context = response.json().get("context", {})
    print(f"   response: {response}")
    print(f"   context: {context}")
    print(f"   ✓ 获取成功。Token 总数: {response.json().get('token_usage', {}).get('total')}")
    # print(f"   Persona: {context.get('user_persona')}")

    # 3. 触发异步结算 (Finalize)
    print("\n3. 正在触发异步结算 (Finalize)...")
    finalize_payload = {
        "user_id": USER_ID,
        "agent_id": AGENT_ID
    }
    response = requests.post(f"{BASE_URL}/memory/finalize", json=finalize_payload)
    task_data = response.json()
    task_id = task_data.get("task_id")
    print(f"   ✓ 任务已入队。Task ID: {task_id}")

    # 4. 追踪任务状态
    print("\n4. 正在追踪结算任务状态...")
    for _ in range(10):
        status_res = requests.get(f"{BASE_URL}/memory/task/{task_id}")
        status = status_res.json().get("data", {}).get("status")
        print(f"   Current Status: {status}")
        if status == "completed":
            print("   ✅ 结算完成！")
            break
        elif status == "failed":
            print("   ❌ 结算失败！")
            break
        time.sleep(2)

    # 5. 验证长期画像演进
    print("\n5. 验证画像与知识沉淀...")
    response = requests.post(f"{BASE_URL}/memory/context", json=context_payload)
    new_context = response.json().get("context", {})
    persona = new_context.get("user_persona")
    if persona and persona.get("risk_preference"):
        print(f"   ✓ 画像已提取: {persona.get('risk_preference')} | {persona.get('interested_sectors')}")
    
    # 6. 获取统计信息
    print("\n6. 获取系统统计...")
    stats_params = {"user_id": USER_ID, "agent_id": AGENT_ID}
    response = requests.get(f"{BASE_URL}/memory/stats", params=stats_params)
    print(f"   Stats: {response.json().get('stats')}")

    print("\n🎉 API 联调测试完成！")

if __name__ == "__main__":
    try:
        test_memory_pipeline()
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        print("请确保记忆系统服务已启动 (python -m api.server)")
