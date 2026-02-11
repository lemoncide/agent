import sys
import os

sys.path.append(os.getcwd())

from agent.core.nodes import AgentNodes
from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager

def check_execute():
    print("Initializing Agent Components...")
    llm = LLMClient()
    memory = MemoryManager()
    tools = ToolManager(memory_manager=memory)
    nodes = AgentNodes(llm, tools, memory)
    
    print("\n--- Executor Verification ---")
    print("We will simulate a single step execution.")
    
    if len(sys.argv) > 1:
        step_desc = sys.argv[1]
    else:
        step_desc = input("Enter a step description (e.g., 'Use calculator to add 5 and 5'): ")
        
    if not step_desc:
        step_desc = "Use calculator to add 5 and 5"
        print(f"Using default step: {step_desc}")
        
    # Mock State
    state = {
        "input": "User wants to do some math",
        "plan": [step_desc],
        "current_step_index": 0,
        "past_steps": [],
        "response": None,
        "summary": "Previous steps: None"
    }
    
    print(f"\nExecuting Step: {step_desc}...")
    result = nodes.execute_node(state)
    
    print("\n--- Execution Result ---")
    step_result = result["past_steps"][0]
    print(f"Result: {step_result['result']}")
        
if __name__ == "__main__":
    check_execute()
