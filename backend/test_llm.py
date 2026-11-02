import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def test_network_connection():
    print("🛰️ Pinging your configured LLM gateway...")
    try:
        # Instantiates the LLM using whatever variables are in your active .env
        llm = ChatOpenAI(
            #model=os.getenv("OPENAI_API_KEY") == "ollama" and "llama3.2:3b" or "gpt-4o-mini",
	    model="llama3.2:3b",
            temperature=0.5,
	    openai_api_key="ollama", # Placeholder string to bypass validation
            openai_api_base="http://localhost:11434/v1" # Direct local routing
        )
        response = llm.invoke("Say the words 'Network Connected' and nothing else.")
        print(f"🤖 LLM Response: {response.content.strip()}")
        print("✅ Network connection validation test passed successfully!")
    except Exception as e:
        print("❌ Network connection handshake failed.")
        print(f"Details: {e}")

if __name__ == "__main__":
    test_network_connection()

