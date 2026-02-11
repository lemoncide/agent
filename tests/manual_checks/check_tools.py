import sys
import os
import json

sys.path.append(os.getcwd())

from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager

def check_tools():
    print("Initializing Tool Manager...")
    # Initialize without memory first to just check loading
    # Or with memory to check indexing
    memory = MemoryManager()
    tools = ToolManager(memory_manager=memory)
    
    print("\n--- Tool Discovery ---")
    all_tools = tools.list_tools(limit=100)
    print(f"Total Tools Loaded: {len(all_tools)}")
    
    for t in all_tools:
        print(f"- {t['name']}: {t['description']}")
        
    print("\n--- Tool Execution Test ---")
    
    if len(sys.argv) > 1:
        tool_name = sys.argv[1]
    else:
        tool_name = input("Enter a tool name to test (or press Enter to skip): ")
        
    if tool_name:
        tool = tools.get_tool(tool_name)
        if tool:
            if len(sys.argv) > 2:
                args_str = sys.argv[2]
            else:
                args_str = input(f"Enter arguments for {tool_name} (JSON format, e.g. {{'expression': '1+1'}}): ")
            
            try:
                args = json.loads(args_str)
                print(f"Executing {tool_name} with {args}...")
                result = tools.execute_tool(tool_name, **args)
                print(f"Result: {result}")
            except json.JSONDecodeError:
                print("Invalid JSON arguments.")
        else:
            print(f"Tool {tool_name} not found.")
            
if __name__ == "__main__":
    check_tools()
