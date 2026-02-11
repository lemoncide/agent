from agent.tools.base import BaseTool
from simpleeval import simple_eval

class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__("calculator", "A simple calculator that evaluates math expressions.")

    def run(self, expression: str, **kwargs):
        try:
            # Using simpleeval for safe evaluation
            return str(simple_eval(expression))
        except Exception as e:
            return f"Error: {e}"

def get_tools():
    return [CalculatorTool()]
