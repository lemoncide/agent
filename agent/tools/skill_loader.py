import os
import importlib.util
from typing import List, Any
from langchain_core.tools import BaseTool, StructuredTool

class SkillLoader:
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir

    def load_skills(self) -> List[BaseTool]:
        tools = []
        if not os.path.exists(self.skills_dir):
            return tools

        for filename in os.listdir(self.skills_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                file_path = os.path.join(self.skills_dir, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Expect the module to have a 'get_tools' function that returns list of LangChain Tools
                    # OR a list of functions we can wrap
                    if hasattr(module, "get_tools"):
                        module_tools = module.get_tools()
                        # If the skill returns our old BaseTool, we might need to adapt, 
                        # but let's assume we update skills to return LangChain tools or compatible objects.
                        # For now, let's wrap anything that looks like a function or object with .run
                        
                        for t in module_tools:
                            if isinstance(t, BaseTool):
                                tools.append(t)
                            elif hasattr(t, 'run') and hasattr(t, 'name') and hasattr(t, 'description'):
                                # Adapt old custom tool to LangChain Tool
                                tools.append(StructuredTool.from_function(
                                    func=t.run,
                                    name=t.name,
                                    description=t.description
                                ))
                except Exception as e:
                    print(f"Failed to load skill {module_name}: {e}")
        
        return tools
