from typing import List, Dict, Optional
from agent.tools.base import BaseTool
from agent.tools.mcp_adapter import MCPAdapter
from agent.tools.skill_loader import SkillLoader
from agent.utils.config import config
from agent.utils.logger import logger
import os

from agent.memory.manager import MemoryManager

class ToolManager:
    def __init__(self, memory_manager: MemoryManager = None):
        self.tools: Dict[str, BaseTool] = {}
        self.mcp_adapter = MCPAdapter()
        self.skill_loader = SkillLoader(os.path.join(os.getcwd(), 'skills'))
        self.memory_manager = memory_manager
        self._initialize_tools()

    def _initialize_tools(self):
        # 1. Load MCP Tools
        mcp_servers = config.get("mcp.servers", {})
        for name, url in mcp_servers.items():
            self.mcp_adapter.connect_server(name, url)
        
        for tool in self.mcp_adapter.list_tools():
            self.register_tool(tool)

        # 2. Load Skills
        for tool in self.skill_loader.load_skills():
            self.register_tool(tool)
            
        logger.info(f"Total tools loaded: {len(self.tools)}")

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
        if self.memory_manager:
            self.memory_manager.index_tool(tool.name, tool.description)
        logger.debug(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self.tools.get(name)

    def list_tools(self, query: str = None, limit: int = 5) -> List[Dict[str, str]]:
        # Modified to support retrieval
        if query and self.memory_manager:
            relevant_names = self.memory_manager.retrieve_tools(query, limit)
            tools_to_return = [self.tools[name] for name in relevant_names if name in self.tools]
            # Fallback if no relevant tools found or memory not ready
            if not tools_to_return:
                 tools_to_return = list(self.tools.values())[:limit]
        else:
            tools_to_return = list(self.tools.values())

        # Support LangChain Tools
        result = []
        for t in tools_to_return:
            if hasattr(t, "to_dict"):
                result.append(t.to_dict())
            else:
                result.append({
                    "name": t.name,
                    "description": t.description
                })
        return result

    def execute_tool(self, name: str, **kwargs):
        tool = self.get_tool(name)
        if tool:
            try:
                # LangChain tool support
                if hasattr(tool, "run"):
                    # For StructuredTool or BaseTool, .run expects tool_input or **kwargs
                    # If it's a StructuredTool from function, it might expect specific args
                    # Let's try passing kwargs directly
                    return tool.run(tool_input=kwargs)
                elif hasattr(tool, "run"): # Fallback for old style if any
                     return tool.run(**kwargs)
            except Exception as e:
                # Try passing as dictionary if kwargs failed or try positional
                try:
                    return tool.run(kwargs)
                except:
                    logger.error(f"Error executing tool {name}: {e}")
                    return f"Error: {str(e)}"
        return f"Tool {name} not found."
