from typing import List
from agent.llm.client import LLMClient
from agent.utils.logger import logger

class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def plan(self, objective: str) -> List[str]:
        logger.info(f"Generating plan for: {objective}")
        
        prompt = f"""
        You are an expert planner. Given the objective, create a step-by-step plan to achieve it.
        Return ONLY the plan steps as a numbered list.
        
        Objective: {objective}
        """
        
        response = self.llm.generate(prompt)
        
        # Parse the response into a list of strings
        steps = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering
                cleaned_line = line.lstrip('0123456789.- ').strip()
                if cleaned_line:
                    steps.append(cleaned_line)
        
        # Fallback if parsing fails (mock)
        if not steps:
            steps = ["Analyze the request", "Execute necessary tools", "Summarize results"]
            
        logger.info(f"Generated plan with {len(steps)} steps")
        return steps
