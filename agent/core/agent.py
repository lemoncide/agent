from agent.core.planner import Planner
from agent.core.reactor import ReActEngine
from agent.core.state import AgentState
from agent.memory.manager import MemoryManager
from agent.tools.manager import ToolManager
from agent.llm.client import LLMClient
from agent.utils.logger import logger

class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.tools = ToolManager()
        self.memory = MemoryManager()
        self.planner = Planner(self.llm)
        self.reactor = ReActEngine(self.llm, self.tools)
        logger.info("Agent initialized successfully")

    def run(self, objective: str):
        logger.info(f"Agent started with objective: {objective}")
        
        # 1. Initialize State
        state = AgentState(input_query=objective)
        
        # 2. Plan
        plan = self.planner.plan(objective)
        state.plan = plan
        
        # 3. Save to Memory
        self.memory.add_memory(f"Objective: {objective}", {"type": "goal"})
        self.memory.add_memory(f"Plan: {plan}", {"type": "plan"})

        # 4. Execute Loop
        results = []
        while state.get_current_step():
            step_result = self.reactor.execute_step(state)
            results.append(step_result)
            state.next_step()
            
        final_result = "\n".join(results)
        self.memory.add_memory(f"Result: {final_result}", {"type": "result"})
        
        return final_result
