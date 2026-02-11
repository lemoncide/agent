from langgraph.graph import StateGraph, END
from agent.core.state import AgentState
from agent.core.nodes import AgentNodes
from agent.llm.client import LLMClient
from agent.tools.manager import ToolManager
from agent.memory.manager import MemoryManager

def build_graph():
    # Initialize dependencies
    llm_client = LLMClient()
    # Note: ToolManager might need updates to handle LangChain tools internally, 
    # but for now we pass it as is.
    tool_manager = ToolManager() 
    memory_manager = MemoryManager()
    
    nodes = AgentNodes(llm_client, tool_manager, memory_manager)
    
    # Initialize Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("plan", nodes.plan_node)
    workflow.add_node("execute", nodes.execute_node)
    workflow.add_node("reflect", nodes.reflect_node)
    
    # Set Entry Point
    workflow.set_entry_point("plan")
    
    # Add Edges
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "reflect")
    
    # Conditional Edge from Reflect
    def should_continue(state: AgentState):
        if state.get("response"):
            return "end"
        
        # Check if replan happened (current_step_index reset to 0 and we are not at start)
        # Or simply check if we need to loop back to plan or execute
        # Based on Reflect Node logic:
        # - Retry: index same -> Execute
        # - Replan: index 0 -> Execute (Plan updated in state)
        # - Next: index + 1 -> Execute
        
        # Wait, if we Replan, we might want to go to Execute directly with new plan?
        # Or go to Plan node to regenerate?
        # Our Reflect node logic updates 'plan' directly if action is 'replan'.
        # So we can just go to Execute.
        
        return "continue"
    
    workflow.add_conditional_edges(
        "reflect",
        should_continue,
        {
            "continue": "execute",
            "end": END
        }
    )
    
    # Compile
    app = workflow.compile()
    return app
