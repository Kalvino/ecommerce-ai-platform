import sys
from langchain_core.messages import HumanMessage
from app.agents.graph import compiled_graph

def run_terminal_agent_simulation():
    print("🕸️  Initializing Multi-Agent Graph Simulation Loop...")
    print("🤖 Target Model Engine: llama3.2:3b via Ollama Local")
    print("-" * 60)
    
    # Define an active test state context tracking target info
    # We will query for 'alex@example.com' which we seeded into Postgres earlier
    initial_state = {
        "messages": [
            HumanMessage(content="Hi there! Can you tell me the current status of my orders?")
        ],
        "user_email": "alex@example.com",
        "current_order_id": None,
        "next_action": "analyze",
        "verification_passed": True,
        "requires_human_approval": False,
        "human_approval_granted": None,
        "escalation_reason": None
    }

    print(f"👤 User Query: {initial_state['messages'][0].content}")
    print(f"📧 Bound User Context: {initial_state['user_email']}")
    print("-" * 60)
    print("🚀 Triggering LangGraph Workflow Compilation Stream:\n")

    try:
        # Use .stream() to step through the execution node by node
        # This mirrors how the events will stream back to Next.js later
        for event in compiled_graph.stream(initial_state, stream_mode="updates"):
            for node_name, node_output in event.items():
                print(f"▶️ [NODE EXECUTED]: {node_name}")
                
                # Check if the node altered the next action step routing tracking
                if "next_action" in node_output:
                    print(f"   ↳ 🎯 Next Planned Action Routing Flag: '{node_output['next_action']}'")
                
                # Check if verification states were modified
                if "verification_passed" in node_output:
                    print(f"   ↳ 🛡️ Guardrail Status: Passed={node_output['verification_passed']}")
                    
                # If an agent appended a response message to history, print out the text
                if "messages" in node_output and node_output["messages"]:
                    last_message = node_output["messages"][-1]
                    print(f"   ↳ 💬 Agent Draft Output:\n\"\"\"\n{last_message.content}\n\"\"\"")
                
                print("-" * 40)
                
        print("\n🏁 Workflow execution successfully reached END node.")
        
    except Exception as e:
        print(f"\n❌ Execution Interrupted via Error: {e}")
        print("👉 Tip: Double check that 'uv run uvicorn' isn't locking your database connection if it's active.")
        sys.exit(1)

if __name__ == "__main__":
    run_terminal_agent_simulation()
