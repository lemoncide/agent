import sys
import os

sys.path.append(os.getcwd())

from agent.core.nodes import AgentNodes
from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager

def check_memory():
    print("Initializing Components...")
    llm = LLMClient()
    memory = MemoryManager()
    tools = ToolManager(memory_manager=memory)
    nodes = AgentNodes(llm, tools, memory)
    
    print("\n--- Memory Summarization Verification ---")
    print("Generating fake long history...")
    
    past_steps = []
    for i in range(12): # > 5 threshold
        past_steps.append({
            "step": f"Step {i+1}: Do something important",
            "result": f"Result {i+1}: Success data {i+1}"
        })
        
    state = {
        "input": "Long running task",
        "plan": ["..."],
        "current_step_index": 12,
        "past_steps": past_steps,
        "response": None
    }
    
    print(f"Current History Length: {len(past_steps)}")
    print("Triggering compression check...")
    
    # Directly call the internal method for testing
    result = nodes._summarize_memory(state)
    
    if result:
        print("\n--- Compression Triggered ---")
        print(f"Summary: {result['summary']}")
        print(f"Cleared History? {result['past_steps'] == []}")
    else:
        print("Compression NOT triggered (Threshold might not be met).")

if __name__ == "__main__":
    check_memory()
