import json
from app.agents.tools import lookup_customer_profile, track_customer_orders, search_shipping_and_return_policies

def run_local_tool_diagnostics():
    print("🧪 Starting manual LangChain Tool validation tests...\n")

    # ---- TEST 1: Lookup Customer Profile ----
    print("🔍 [TEST 1] Running profile lookup for 'alex@example.com'...")
    # LangChain tools expect keyword arguments or can be run via .invoke()
    profile_result = lookup_customer_profile.invoke({"email": "alex@example.com"})
    print(f"Response: {json.dumps(profile_result, indent=2)}\n")

    # ---- TEST 2: Track Customer Orders ----
    if "id" in profile_result:
        user_id = profile_result["id"]
        print(f"📦 [TEST 2] Fetching transaction logs for User ID: {user_id}...")
        orders_result = track_customer_orders.invoke({"user_id": user_id})
        print(f"Response: {json.dumps(orders_result, indent=2)}\n")
    else:
        print("❌ Skipping Test 2: Profile lookup failed to return an ID.\n")

    # ---- TEST 3: Search Policies ----
    print("📜 [TEST 3] Testing rule lookup for refund windows...")
    policy_result = search_shipping_and_return_policies.invoke({"query_text": "What is your return policy?"})
    print(f"Response: {policy_result}\n")

    print("🏁 Validation tests complete.")

if __name__ == "__main__":
    run_local_tool_diagnostics()
