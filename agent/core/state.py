from typing import List, Dict, Any, Optional, TypedDict, Annotated
import operator

class AgentState(TypedDict):
    input: str
    plan: List[str]
    current_step_index: int
    past_steps: Annotated[List[Dict[str, str]], operator.add]
    response: Optional[str]
    scratchpad: Dict[str, Any]
    summary: Optional[str] # For memory compression
