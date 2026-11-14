import os
import json
from sqlalchemy import text
from langchain_community.embeddings import OllamaEmbeddings
from app.database import engine

# Initialize the exact local embedding engine model
embeddings_engine = OllamaEmbeddings(
    model="all-minilm:l6-v2",
    base_url="http://localhost:11434"
)

MOCK_POLICIES = [
    {
        "content": "Standard items can be returned within 30 days of delivery. Refunds take 5-7 business days to process back to the original payment method once inspected at our warehouse registry.",
        "metadata": {"category": "refunds", "sla_days": 7}
    },
    {
        "content": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 days. Orders over KSh 5,000 ship free across all districts. Lost packages must be escalated to human operators.",
        "metadata": {"category": "shipping", "minimum_spend": 5000}
    }
]

def migrate_and_seed_vectors():
    print("🔄 Ensuring vector dimension configuration aligns with model layout...")
    with engine.connect() as conn:
        # Alter table column dynamically to match the 384 dimensions of all-minilm
        conn.execute(text("ALTER TABLE knowledge_base ALTER COLUMN embedding TYPE vector(384);"))
        conn.commit()

        print("🧠 Generating embeddings via Ollama and injecting records...")
        for policy in MOCK_POLICIES:
            # Generate the raw vector array from text string
            vector = embeddings_engine.embed_query(policy["content"])
            
            query = text("""
                INSERT INTO knowledge_base (content, embedding, metadata)
                VALUES (:content, :embedding, :metadata);
            """)
            
            conn.execute(query, {
                "content": policy["content"],
                "embedding": str(vector), # SQLAlchemy parses vector string casting formats natively
                "metadata": json.dumps(policy["metadata"])
            })
        conn.commit()
    print("✅ pgvector knowledge base populated successfully.")

if __name__ == "__main__":
    migrate_and_seed_vectors()
