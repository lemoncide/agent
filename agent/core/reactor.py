from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.core.state import AgentState
from agent.utils.logger import logger

class ReActEngine:
    def __init__(self, llm_client: LLMClient, tool_manager: ToolManager):
        self.llm = llm_client
        self.tools = tool_manager

    def execute_step(self, state: AgentState) -> str:
        current_step = state.get_current_step()
        if not current_step:
            return "No more steps."

        logger.info(f"Executing Step {state.current_step_index + 1}: {current_step}")
        
        # In a full ReAct loop, we would:
        # 1. Ask LLM what to do for this step (Thought)
        # 2. LLM decides an Action (Tool call)
        # 3. Execute Tool (Observation)
        # 4. Repeat until LLM says step is done
        
        # Simplified implementation:
        # Check if any tool matches the step description (naive)
        
        available_tools = self.tools.list_tools()
        tool_names = [t['name'] for t in available_tools]
        
        prompt = f"""
        You are an agent executing a plan.
        Current Step: {current_step}
        Available Tools: {tool_names}
        
        Decide which tool to use. Return JSON format: {{"tool": "tool_name", "args": {{...}}}}
        If no tool is needed, return {{"tool": null, "response": "text response"}}
        """
        
        # Mocking the decision process for the demo
        response = "Executed step logic."
        
        # Check if 'example_skill' is relevant
        if ("calculate" in current_step.lower() or "calculator" in current_step.lower()) and "calculator" in tool_names:
             # extract expression from input_query for demo purposes
             import re
             expression = "0"
             match = re.search(r'[\d\+\-\*\/\(\)\s]+', state.input_query)
             if match:
                 expression = match.group(0).strip()
             
             result = self.tools.execute_tool("calculator", expression=expression)
             response = f"Calculated: {result}"
        elif "search" in current_step.lower() and "example_search" in tool_names:
             result = self.tools.execute_tool("example_search", query=current_step)
             response = f"Search Result: {result}"
        else:
             response = f"Processed step: {current_step} (Internal Logic)"

        state.update_history(current_step, response)
        return response
