from langchain_core.tools import tool
from sqlalchemy import text
from app.database import engine
from typing import Dict, Any, List
from langchain_community.embeddings import OllamaEmbeddings

# Initialize local embedding layer
embeddings_engine = OllamaEmbeddings(
    model="all-minilm:l6-v2",
    base_url="http://localhost:11434"
)

@tool
def lookup_customer_profile(email: str) -> Dict[str, Any]:
    """
    Queries the database to retrieve a customer's basic account profile 
    and loyalty tier using their verified email address.
    """
    query = text("""
        SELECT id, name, email, loyalty_tier 
        FROM users 
        WHERE email = :email;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email.strip()}).mappings().first()
        
    if not result:
        return {"error": f"No customer profile found matching the email address: {email}"}
        
    return dict(result)


@tool
def track_customer_orders(user_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves a complete list of past and present retail transactions, 
    order statuses, totals, and tracking codes for a specific user ID.
    """
    query = text("""
        SELECT id, status, total_amount, shipping_address, tracking_number, created_at
        FROM orders 
        WHERE user_id = :user_id
        ORDER BY created_at DESC;
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query, {"user_id": user_id}).mappings().all()
        
    if not rows:
        return []
        
    # Serialize decimals and timestamps for clean JSON transport
    serialized_orders = []
    for row in rows:
        order_dict = dict(row)
        order_dict["total_amount"] = float(order_dict["total_amount"])
        order_dict["created_at"] = order_dict["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        serialized_orders.append(order_dict)
        
    return serialized_orders


@tool
def search_shipping_and_return_policies(query_text: str) -> str:
    """
    Performs a real-time semantic vector similarity search against the database knowledge base
    to retrieve shipping speeds, refund timelines, and warehouse operational policies.
    """
    # 1. Compute embedding vector for the incoming raw search text string
    raw_vector = embeddings_engine.embed_query(query_text)
    
    # 2. Query using native pgvector cosine distance operator (<=>)
    query = text("""
        SELECT content, metadata
        FROM knowledge_base
        ORDER BY embedding <=> :embedded_query
        LIMIT 1;
    """)
    
    with engine.connect() as conn:
        row = conn.execute(query, {"embedded_query": str(raw_vector)}).mappings().first()
        
    if not row:
        return "No explicit matching company logistics rules uncovered in corporate knowledge base maps."
        
    return f"Extracted Corporate Policy Context:\n{row['content']}"
