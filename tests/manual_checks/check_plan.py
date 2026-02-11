import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.getcwd())

from agent.core.nodes import AgentNodes
from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager

def check_plan():
    print("Initializing Agent Components...")
    llm = LLMClient()
    memory = MemoryManager()
    tools = ToolManager(memory_manager=memory)
    nodes = AgentNodes(llm, tools, memory)
    
    print("\n--- Planner Verification ---")
    if len(sys.argv) > 1:
        objective = sys.argv[1]
    else:
        objective = input("Enter a task for the agent (e.g., 'Calculate 5+5 and save to file'): ")
    
    if not objective:
        objective = "Calculate 10 + 20 and tell me the result."
        print(f"Using default objective: {objective}")
        
    state = {
        "input": objective,
        "plan": [],
        "current_step_index": 0,
        "past_steps": [],
        "response": None
    }
    
    print(f"\nPlanning for: {objective}...")
    result = nodes.plan_node(state)
    
    print("\n--- Generated Plan ---")
    for i, step in enumerate(result["plan"]):
        print(f"{i+1}. {step}")
        
if __name__ == "__main__":
    check_plan()
