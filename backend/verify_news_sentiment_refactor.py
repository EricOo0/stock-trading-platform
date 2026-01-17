import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import json
import logging
from backend.app.agents.news_sentiment.agent import create_news_sentiment_agent

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    event_queue = asyncio.Queue()
    agent = create_news_sentiment_agent(event_queue)
    
    query = "分析 NVIDIA (NVDA) 在 RTX 5090 发布前后的市场情绪"
    
    print(f"Starting Agent with query: {query}")
    
    # Run in background
    task = asyncio.create_task(agent.run(query))
    
    # Consume events
    start_time = asyncio.get_event_loop().time()
    while True:
        try:
            # Timeout to prevent hanging forever
            item = await asyncio.wait_for(event_queue.get(), timeout=120.0)
            # print(f"Received Event: {item.strip()}")
            
            data = json.loads(item)
            
            # Re-serialize with ensure_ascii=False for readable logs
            readable_item = json.dumps(data, ensure_ascii=False)
            
            task_id = data.get('payload', {}).get('task_id', 'UNKNOWN')
            event_type = data.get('payload', {}).get('type', 'UNKNOWN')
            
            # Highlight tool calls
            if event_type == 'tool_call':
                 tool_name = data.get('payload', {}).get('tool_name', 'unknown')
                 print(f"[{task_id}] TOOL CALL: {tool_name}")
            
            # print(f"Received Event: {readable_item}", flush=True)
            
            if data['type'] == 'conclusion':
                print("\n=== CONCLUSION REACHED ===")
                print(json.dumps(data['payload'], indent=2, ensure_ascii=False))
                break
            
            if data['type'] == 'error':
                print(f"Error: {data['content']}")
                break
                
        except asyncio.TimeoutError:
            print("Timeout waiting for event.")
            break
        except Exception as e:
            print(f"Error processing event: {e}")
            break

    # Clean up
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())
