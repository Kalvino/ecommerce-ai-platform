import os
import asyncio
import json
from fastapi import FastAPI, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from langchain_core.messages import HumanMessage
# Use the Async version of the checkpointer driver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Import security layer, custom state structure, and compiled workflow graph
from app.security import validate_api_key
from app.agents.state import AgentWorkflowState
from app.agents.graph import compiled_graph
from app.agents.graph import workflow

app = FastAPI(
    title="E-Commerce Multi-Agent Platform Core",
    description="Production-grade AI agent orchestration matrix powered by FastAPI & LangGraph",
    version="1.0.0"
)

# Configure CORS: Allow internal local traffic networks safely during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js development server address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for input payload sanitation
class UserQueryRequest(BaseModel):
    message: str
    user_email: EmailStr
    thread_id: str  # Add this line to accept session IDs from Next.js

@app.get("/health", status_code=status.HTTP_200_OK)
async def system_health_check():
    """Simple baseline status route to confirm server runtime stability."""
    return {"status": "healthy", "service": "ecommerce-ai-backend"}

@app.post("/api/v1/agent/stream", dependencies=[Depends(validate_api_key)])
async def stream_agent_workflow(payload: UserQueryRequest):
    """
    Secure workflow hub. Accepts user requests, compiles runtime memory states,
    and streams live LangGraph node transformations directly across the network layer
    using Server-Sent Events (SSE).
    """
    
    # 1. Initialize the base state schema matching our graph input expectations
    initial_graph_state: AgentWorkflowState = {
        "messages": [HumanMessage(content=payload.message)],
        "user_email": str(payload.user_email),
        "current_order_id": None,
        "next_action": "analyze",
        "verification_passed": True,
        "requires_human_approval": False,
        "human_approval_granted": None,
        "escalation_reason": None
    }

    # Define the execution thread context metadata
    graph_config = {"configurable": {"thread_id": payload.thread_id}}
    DB_URI = os.getenv("DATABASE_URL")
    
    async def event_generator():
        try:
            # Open a live connection pool instance for this specific streaming thread lifecycle
            async with AsyncPostgresSaver.from_conn_string(DB_URI) as memory_pool:
                # Compile the graph bound dynamically to this connection frame
                runtime_graph = workflow.compile(checkpointer=memory_pool)
                
                # 2. Iterate asynchronously over graph execution increments using .astream()
                # We utilize stream_mode="updates" to capture single-node delta changes instantly
                async for chunk in runtime_graph.astream(initial_graph_state, config=graph_config, stream_mode="updates"):
                    for node_name, node_output in chunk.items():
                    
                        # Package metadata about which agent node is running
                        meta_event = {
                            "event": "node_update",
                            "node": node_name,
                            "next_action": node_output.get("next_action", "none")
                        }
                        yield f"data: {json.dumps(meta_event)}\n\n"
                        
                        # If the node produced a fresh textual response, extract and stream it immediately
                        if "messages" in node_output and node_output["messages"]:
                            last_message = node_output["messages"][-1]
                            token_event = {
                                "event": "text_chunk",
                                "content": last_message.content
                            }
                            yield f"data: {json.dumps(token_event)}\n\n"
                    
                    # Tiny yielding pause to keep network frames clean and manageable
                    await asyncio.sleep(0.05)

            # Signal final stream termination boundary
            yield f"data: {json.dumps({'event': 'workflow_complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'detail': str(e)})}\n\n"
            
        except asyncio.CancelledError:
            print("⚠️ Next.js server disconnected from active streaming channel pipeline prematurely.")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

