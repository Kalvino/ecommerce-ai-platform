from typing import Annotated, TypedDict, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentWorkflowState(TypedDict):
    """
    The centralized memory tracking space for our E-commerce Multi-Agent graph.
    Defines exactly what data points can be accessed or modified by our routing nodes.
    """
    
    # 1. Message History Core
    # add_messages is a LangGraph reducer. Instead of overwriting the list, 
    # it automatically appends new incoming assistant/user messages to the history array.
    messages: Annotated[List[BaseMessage], add_messages]
    
    # 2. Context Metadata Trackers
    user_email: str
    current_order_id: Optional[int]
    
    # 3. Graph Routing Control States
    # Helps the router coordinate state transfers between specialized nodes
    next_action: str             # e.g., "call_rag", "fetch_orders", "escalate", "reply"
    verification_passed: bool    # Set by the Inspector Agent to check for hallucinations
    
    # 4. Human-in-the-Loop Flags
    # Tells our Next.js API layer if the graph execution has been interrupted
    requires_human_approval: bool
    human_approval_granted: Optional[bool]
    escalation_reason: Optional[str]
