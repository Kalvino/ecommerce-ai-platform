import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load workspace environment variables from backend/.env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ Critical Error: DATABASE_URL variable missing in backend/.env file.")
    sys.exit(1)

# Establish a connection engine with a fallback timeout pool
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,  # Automatically tests connection health before executing commands
    pool_recycle=3600    # Recycles connections every hour to maintain memory hygiene
)

def init_db():
    """Validates connectivity, creates relational/vector schematics, and activates pgvector."""
    print("🔄 Connecting to PostgreSQL database engine...")
    try:
        with engine.connect() as conn:
            # 1. Activate vector geometry layer natively in Postgres instance
            print("🚀 Initializing native vector spatial extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            
            # 2. Build foundational Relational Core Tables
            print("📦 Structuring core relational data schemas...")
            
            # Users Schema
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    loyalty_tier VARCHAR(20) DEFAULT 'Standard',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Orders Schema
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    user_id INT REFERENCES users(id) ON DELETE CASCADE,
                    status VARCHAR(50) DEFAULT 'Processing',
                    total_amount NUMERIC(10, 2) NOT NULL,
                    shipping_address TEXT NOT NULL,
                    tracking_number VARCHAR(100) DEFAULT 'UNASSIGNED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # 3. Create Vector Storage Table for RAG Documents
            # 1536 matches standard embeddings dimensions (OpenAI text-embedding-3-small, etc.)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding VECTOR(1536),
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            conn.commit()
            print("✅ Database tables structural blueprint mapped out successfully.")
            
    except OperationalError as e:
        print(f"❌ Database connection initialization failed.")
        print(f"👉 Ensure your Docker container 'ecommerce_ai_db' is up and running via: docker compose up -d")
        print(f"Error Context: {e}")
        sys.exit(1)

def seed_mock_data():
    """Seeds foundational users and transaction logs to test LangChain tools against."""
    print("🌱 Injecting initial state database records...")
    try:
        with engine.connect() as conn:
            # Ensure table isn't pre-seeded to prevent unique constraint conflicts
            user_count = conn.execute(text("SELECT COUNT(*) FROM users;")).scalar()
            if user_count == 0:
                # Seed Base Customers
                conn.execute(text("""
                    INSERT INTO users (name, email, loyalty_tier) VALUES 
                    ('Alex Mercer', 'alex@example.com', 'Gold'),
                    ('Jane Doe', 'jane@example.com', 'Standard'),
                    ('Marcus Vance', 'marcus@example.com', 'VIP');
                """))
                
                # Seed Associated Retail Transaction Orders
                conn.execute(text("""
                    INSERT INTO orders (user_id, status, total_amount, shipping_address, tracking_number) VALUES 
                    (1, 'Shipped', 12500.00, 'Nairobi, Westlands District, Block 4B', 'TRK-987654-XYZ'),
                    (1, 'Processing', 3450.00, 'Nairobi, Kilimani Area, Apt 12', 'UNASSIGNED'),
                    (2, 'Delivered', 7200.50, 'Mombasa, Nyali Estate, House 14', 'TRK-112233-ABC'),
                    (3, 'Processing', 89900.00, 'Nairobi, Karen Greens, Plot 7', 'UNASSIGNED');
                """))
                conn.commit()
                print("🏁 Data seeding operations finished smoothly.")
            else:
                print("⚠️ Skipping seeding stage: Relational records already exist in current instance.")
    except Exception as e:
        print(f"❌ Error occurred during data seeding: {e}")

if __name__ == "__main__":
    init_db()
    seed_mock_data()
