from langchain_core.tools import tool
from sqlalchemy import text
from app.database import engine
from typing import Dict, Any, List

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
    Simulates a vector-store semantic search against the knowledge base 
    to retrieve shipping speeds, refund windows, and general policies.
    """
    # This is a temporary structural fallback placeholder until we populate embeddings in Step 5.
    # It allows your agents to get immediate, predictable policy answers during integration testing.
    lowercased = query_text.lower()
    if "return" in lowercased or "refund" in lowercased:
        return "Policy: Standard items can be returned within 30 days of delivery. Refunds take 5-7 business days."
    if "shipping" in lowercased or "delivery" in lowercased:
        return "Policy: Standard shipping takes 3-5 business days. Express shipping takes 1-2 days. Orders over KSh 5,000 ship free."
    
    return "Policy: For complex delivery issues or manual modifications, escalate to a human supervisor."
