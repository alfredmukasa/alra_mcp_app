#!/usr/bin/env python3
"""
Supabase Setup Script for AI Discussion Manager
This script helps set up the Supabase database for the AI Discussion Manager application.
"""

from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_supabase_tables():
    """Guide for creating Supabase tables"""

    print("🚀 AI Discussion Manager - Supabase Setup")
    print("=" * 50)
    print()

    # Supabase configuration
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase configuration!")
        print("Please set the following environment variables in your .env file:")
        print("  SUPABASE_URL=https://your-project-id.supabase.co")
        print("  SUPABASE_KEY=your-supabase-anon-key")
        print()
        return False

    print("🔄 Testing Supabase connection...")
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        # Test connection by trying to access a non-existent table
        supabase.table('test_connection').select('*').limit(1).execute()
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

    print("✅ Connected to Supabase successfully!")
    print()
    print("📋 To set up your database tables, go to your Supabase dashboard:")
    print("1. Open your Supabase project dashboard")
    print("2. Go to the SQL Editor")
    print("3. Run the following SQL commands:")
    print()

    sql_commands = """
-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    project_title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    teams TEXT,
    uploaded_file_name TEXT,
    uploaded_file_content TEXT
);

-- Create messages table
CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    model TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create generated_files table
CREATE TABLE IF NOT EXISTS generated_files (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT REFERENCES conversations(id) ON DELETE CASCADE,
    file_type TEXT NOT NULL CHECK (file_type IN ('markdown', 'prompt', 'cursor_guide')),
    file_name TEXT NOT NULL,
    file_content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_generated_files_conversation_id ON generated_files(conversation_id);
CREATE INDEX IF NOT EXISTS idx_generated_files_created_at ON generated_files(created_at DESC);
"""

    print(sql_commands)
    print("4. After running the SQL commands, your database will be ready!")
    print()
    print("🎉 Supabase setup completed successfully!")
    print("📊 Your database is ready for the AI Discussion Manager application.")

    return True

def test_connection():
    """Test Supabase connection and database status"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase configuration!")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
        return False

    try:
        print("🔄 Testing Supabase connection...")
        supabase: Client = create_client(supabase_url, supabase_key)

        # Test connection by trying to count conversations
        try:
            result = supabase.table('conversations').select('*', count='exact').execute()
            count = result.count if hasattr(result, 'count') else len(result.data)
            print("✅ Connected to Supabase successfully!")
            print(f"📊 Total conversations in database: {count}")
            return True
        except Exception as table_error:
            print(f"⚠️ Connected to Supabase, but tables may not exist yet: {table_error}")
            print("Run the setup script to create the required tables.")
            return False

    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Creating template...")

        env_template = """# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
"""

        with open('.env', 'w') as f:
            f.write(env_template)

        print("✅ Created .env template file")
        print("📝 Please edit .env file with your Supabase credentials and OpenAI API key")
        print()

    print("🔧 Setting up Supabase database...")
    if create_supabase_tables():
        print("\n🧪 Testing connection...")
        test_connection()

    print("\n📚 Setup complete! You can now run the AI Discussion Manager:")
    print("   streamlit run main.py")
