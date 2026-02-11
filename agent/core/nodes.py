from typing import List, Dict, Any
from agent.core.state import AgentState
from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager
from langchain_core.messages import HumanMessage, SystemMessage
import json
import re

class AgentNodes:
    def __init__(self, llm_client: LLMClient, tool_manager: ToolManager, memory_manager: MemoryManager):
        self.llm = llm_client
        self.tools = tool_manager
        self.memory = memory_manager

    def plan_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate a plan based on input"""
        print("--- Plan Node ---")
        objective = state["input"]
        
        # Load prompt template
        from agent.utils.prompt_loader import prompt_loader
        template = prompt_loader.get("plan_template")
        
        # Simple tool names list for planning context
        tool_names = [t['name'] for t in self.tools.list_tools(limit=10)] # Retrieve some tools context
        
        prompt = template.format(objective=objective, tool_names=tool_names)
        
        response = self.llm.generate(prompt, system_prompt="You are a helpful AI assistant that plans tasks.")
        
        # Parse the response into a list of strings
        plan = []
        for line in response.split('\n'):
            line = line.strip()
            # Support *, -, 1. etc
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering and bullets
                cleaned_line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
                if cleaned_line:
                    plan.append(cleaned_line)
        
        if not plan:
            # Fallback if parsing fails or LLM returns non-list
            plan = [response]
            
        print(f"Generated Plan: {plan}")
            
        return {
            "plan": plan, 
            "current_step_index": 0, 
            "past_steps": [],
            "response": None
        }

    def _summarize_memory(self, state: AgentState) -> Dict[str, Any]:
        """Compress memory if history is too long"""
        history = state.get("past_steps", [])
        if len(history) > 5: # Threshold for demo, usually 10+
            from agent.utils.prompt_loader import prompt_loader
            
            history_text = "\n".join([f"Step: {s['step']}\nResult: {s['result']}" for s in history])
            template = prompt_loader.get("summary_template")
            prompt = template.format(history=history_text)
            
            summary = self.llm.generate(prompt)
            print(f"--- Memory Compressed: {summary[:50]}... ---")
            
            # Return new state updates
            return {
                "summary": summary,
                "past_steps": [] # Clear history after summarization
            }
        return {}

    def execute_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the current step using ReAct"""
        # Check if memory needs compression first
        memory_update = self._summarize_memory(state)
        if memory_update:
             # If we compressed memory, we should conceptually update the state before proceeding.
             # In LangGraph, we return dicts to update state. 
             # But here we are inside a node. We can just use the updated values locally or return them.
             # Ideally, summarization should be a separate node or a pre-hook. 
             # For simplicity, we just use the summary in our prompt context.
             state["summary"] = memory_update["summary"]
             state["past_steps"] = [] # Local clear for this run

        print("--- Execute Node ---")
        plan = state["plan"]
        index = state["current_step_index"]
        
        if index >= len(plan):
            return {"response": "All steps completed."}
            
        current_step = plan[index]
        print(f"Executing Step {index + 1}: {current_step}")
        
        # Tool execution logic using LLM
        # Use retrieval to get relevant tools
        available_tools = self.tools.list_tools(query=current_step, limit=5)
        
        from agent.utils.prompt_loader import prompt_loader
        template = prompt_loader.get("execute_template")
        
        prompt = template.format(
            current_step=current_step,
            input=state['input'],
            summary=state.get('summary', 'None'),
            history=state.get('past_steps', []),
            tools=json.dumps(available_tools, indent=2)
        )
        
        # Define Schema for Structured Output
        execution_schema = {
            "tool": "tool_name_or_null",
            "args": {"arg_name": "arg_value"},
            "response": "final_response_if_no_tool"
        }
        
        result = f"Failed to execute step: {current_step}"
        
        try:
            decision = self.llm.generate_structured(
                prompt, 
                example_schema=execution_schema,
                system_prompt="You are a precise agent that executes tasks using tools."
            )
            
            tool_name = decision.get("tool")
            
            if tool_name and tool_name.lower() != "null" and tool_name.lower() != "none":
                print(f"LLM decided to use tool: {tool_name}")
                args = decision.get("args", {})
                # Securely execute tool (no eval in nodes.py, relies on tool implementation)
                tool_output = self.tools.execute_tool(tool_name, **args)
                result = f"Tool '{tool_name}' Output: {tool_output}"
            else:
                result = decision.get("response", "Step processed without tools.")
                
        except Exception as e:
            print(f"Error executing step: {e}")
            result = f"Error: {str(e)}"

        return {
            "past_steps": [{"step": current_step, "result": result}],
            # We don't increment index here, we let the reflect node decide
        }

    def reflect_node(self, state: AgentState) -> Dict[str, Any]:
        """Reflect on the past step and decide next move"""
        print("--- Reflect Node ---")
        plan = state["plan"]
        index = state["current_step_index"]
        
        # Check result of the last step
        past_steps = state.get("past_steps", [])
        last_step_result = past_steps[-1]["result"] if past_steps else "No result"
        
        # Check retry count
        current_step_desc = plan[index]
        retry_count = 0
        for step in reversed(past_steps):
            if step.get("step") == current_step_desc:
                retry_count += 1
            else:
                break
        
        print(f"Current Step: {current_step_desc} (Executions: {retry_count})")

        # If last result contains Error, trigger LLM to decide
        # Also trigger if retry count is high to see if we should replan
        is_error = "Error" in last_step_result or "Failed" in last_step_result
        
        if is_error or retry_count > 1:
             from agent.utils.prompt_loader import prompt_loader
             template = prompt_loader.get("reflect_template")
             prompt = template.format(plan=plan, index=index, result=last_step_result)
             
             # Force replan if too many retries
             if retry_count >= 3:
                 prompt += "\n\nCRITICAL: You have retried this step 3 times. You MUST choose 'replan' and provide a simplified or alternative plan."
             
             reflect_schema = {
                 "action": "retry | replan | next",
                 "reason": "explanation",
                 "new_plan": ["step1", "step2"] 
             }
             
             try:
                 decision = self.llm.generate_structured(
                     prompt, 
                     example_schema=reflect_schema,
                     system_prompt="You are a supervisor managing a task plan."
                 )
                 
                 action = decision.get("action")
                 print(f"Reflect Decision: {action} - {decision.get('reason')}")
                 
                 if action == "retry":
                     if retry_count >= 3:
                         print("Reflect decided retry but limit reached. Forcing Replan request.")
                         # Fallback if LLM stubbornly says retry
                         # Actually if it fails to replan, we might get stuck. 
                         # Let's trust the prompt constraint above.
                         pass
                     return {"current_step_index": index} # No change, retry
                 elif action == "replan":
                     new_plan = decision.get("new_plan", [])
                     if new_plan:
                         return {"plan": new_plan, "current_step_index": 0} # Reset to new plan
                     else:
                         print("Warning: Replan requested but no plan provided. Continuing.")
             except Exception as e:
                 print(f"Reflect Logic Failed: {e}. Defaulting to next step.")

        # Default behavior: Move to next step
        new_index = index + 1
        is_finished = new_index >= len(plan)
        
        response = None
        if is_finished:
            # Aggregate results
            results = "\n".join([f"Step: {s.get('step', 'Unknown')}\nResult: {s.get('result', 'Unknown')}" for s in past_steps])
            response = f"Task Completed.\nSummary:\n{results}"
        
        return {
            "current_step_index": new_index,
            "response": response
        }
