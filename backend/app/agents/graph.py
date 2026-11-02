import os
from typing import Literal, Dict, Any
from dotenv import load_dotenv

# LangChain & LangGraph Imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

# Local Architecture Imports
from app.agents.state import AgentWorkflowState
from app.agents.tools import lookup_customer_profile, track_customer_orders, search_shipping_and_return_policies

load_dotenv()

# Initialize the LLM Core. 
# Switch to base_url="http://localhost:11434/v1" if utilizing Ollama locally!
LLM = ChatOpenAI(
    #model="gpt-4o-mini", uncomment if using cloud-first configuration(OpenAI). Swap with any preferred OpenAI model
    model="llama3.2:3b", #using Local-First Configuration (Ollama)
    temperature=0.2,
    openai_api_key="ollama",
    openai_api_base="http://localhost:11434/v1"
)

# Bind the operational tools directly to our core model matrix
TOOLS_BY_NAME = {
    "lookup_customer_profile": lookup_customer_profile,
    "track_customer_orders": track_customer_orders,
    "search_shipping_and_return_policies": search_shipping_and_return_policies
}
LLM_WITH_TOOLS = LLM.bind_tools(list(TOOLS_BY_NAME.values()))

# ==========================================
# 🧠 NODE DEFINITIONS (The Agents)
# ==========================================

def router_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    """
    Analyzes user text intent and decides whether to route the conversation 
    to RAG search, Account Database queries, or escalate immediately.
    """
    messages = state["messages"]
    
    system_prompt = SystemMessage(content=(
        "You are the Lead Router for an elite E-commerce Logistics platform.\n"
        "Analyze the conversation history. Decide the next best action from these three:\n"
        "1. 'fetch_orders' - If the user is asking about order tracking, status, delivery dates, or history.\n"
        "2. 'call_rag' - If they are asking general policy questions (returns, refunds, shipping rules).\n"
        "3. 'reply' - If they are saying hello, thanking you, or if you already have enough data to reply.\n"
        "Respond strictly with just the single action word: 'fetch_orders', 'call_rag', or 'reply'."
    ))
    
    # Simple semantic fallback or LLM call to get routing action
    response = LLM.invoke([system_prompt] + messages)
    action = response.content.strip().lower()
    
    # Clean up responses to ensure strict routing values
    if "order" in action or "fetch_orders" in action:
        next_action = "fetch_orders"
    elif "rag" in action or "call_rag" in action:
        next_action = "call_rag"
    else:
        next_action = "reply"
        
    return {"next_action": next_action}


def rag_specialist_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    """Retrieves standard logistics policies and frames a draft answer."""
    messages = state["messages"]
    last_user_msg = messages[-1].content
    
    # Invoke our Policy lookup tool directly
    policy_context = search_shipping_and_return_policies.invoke({"query_text": last_user_msg})
    
    system_prompt = SystemMessage(content=(
        f"You are a policy assistant. Answer the user using ONLY this extracted context:\n{policy_context}"
    ))
    
    response = LLM.invoke([system_prompt] + messages)
    return {"messages": [response], "next_action": "inspect"}


def account_ops_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    """Fetches user information and transactional tracking metrics directly from Postgres."""
    email = state.get("user_email", "")
    
    # 1. Pull basic demographic profile metrics
    profile = lookup_customer_profile.invoke({"email": email})
    
    if "error" in profile:
        msg = AIMessage(content=f"I couldn't find an account matching the email: {email}. Could you double check it?")
        return {"messages": [msg], "next_action": "reply"}
        
    # 2. Pull relational transaction ledger logs
    orders = track_customer_orders.invoke({"user_id": profile["id"]})
    
    system_prompt = SystemMessage(content=(
        f"You are an Account Operations Bot. Synthesize this profile: {profile} and order log: {orders} "
        "into a helpful tracking breakdown for the customer. Be concise."
    ))
    
    response = LLM.invoke([system_prompt] + state["messages"])
    return {"messages": [response], "next_action": "inspect"}


def inspector_agent(state: AgentWorkflowState) -> Dict[str, Any]:
    """Safety guardrail node checking drafted answers against corporate criteria."""
    messages = state["messages"]
    last_ai_msg = messages[-1].content
    
    # Simple structural check for presentation consistency
    if len(last_ai_msg) > 10:
        return {"verification_passed": True, "next_action": "complete"}
    
    # Fail guardrail and route back for self-correction if answer is too brief or empty
    return {"verification_passed": False, "next_action": "retry"}

# ==========================================
# 🗺️ ROUTING LOGIC & GRAPH COMPILATION
# ==========================================

def route_after_analysis(state: AgentWorkflowState) -> Literal["account_ops", "rag_specialist", "generate_reply"]:
    """Conditional router determining structural pathways based on next_action state values."""
    action = state["next_action"]
    if action == "fetch_orders":
        return "account_ops"
    elif action == "call_rag":
        return "rag_specialist"
    return "generate_reply"


def route_after_inspection(state: AgentWorkflowState) -> Literal["finalize", "router"]:
    """Loops back if guardrail check fails, preventing output hallucinations."""
    if state.get("verification_passed", True):
        return "finalize"
    return "router"

# Initialize StateGraph with our structured state tracker Dict
workflow = StateGraph(AgentWorkflowState)

# Append functional agent nodes into execution layout
workflow.add_node("router", router_agent)
workflow.add_node("account_ops", account_ops_agent)
workflow.add_node("rag_specialist", rag_specialist_agent)
workflow.add_node("inspector", inspector_agent)

# Configure Entrypoint edge lines
workflow.add_edge(START, "router")

# Add conditional execution forks
workflow.add_conditional_edges(
    "router",
    route_after_analysis
)

# Route agent output vectors into verification matrix
workflow.add_edge("account_ops", "inspector")
workflow.add_edge("rag_specialist", "inspector")

# Configure inspection exit/retry loops
workflow.add_conditional_edges(
    "inspector",
    route_after_inspection,
    {
        "finalize": END,
        "router": "router"
    }
)

# Create standalone conversational fallback endpoint node for greeting vectors
def generic_reply_node(state: AgentWorkflowState) -> Dict[str, Any]:
    response = LLM.invoke(state["messages"])
    return {"messages": [response]}

workflow.add_node("generate_reply", generic_reply_node)
workflow.add_edge("generate_reply", END)

# ==========================================================
# 💾 REUSABLE POSTGRES COLD STORAGE MEMORY MATRIX
# ==========================================================

# Pull connection string from env
DB_URI = os.getenv("DATABASE_URL")

# 1. Open the checkpointer using a context manager to handle connection lifecycles safely
with PostgresSaver.from_conn_string(DB_URI) as memory_pool:
    # 2. Run migrations automatically to build the `checkpoints`, `writes`, etc. tables
    memory_pool.setup()
    
    # 3. Compile framework diagram layout WITH checkpointer memory active
    compiled_graph = workflow.compile(checkpointer=memory_pool)

print("🕸️  LangGraph Multi-Agent execution matrix compiled with active PostgresSaver memory checkpoint loops.")
