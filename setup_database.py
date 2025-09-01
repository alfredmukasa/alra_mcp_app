#!/usr/bin/env python3
"""
Database Setup Script for AI Discussion Manager
This script helps set up the MySQL database for the AI Discussion Manager application.
"""

import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_database():
    """Create the AI Discussion Manager database and tables"""

    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
    }

    database_name = os.getenv('DB_NAME', 'ai_discussion_manager')

    connection = None
    try:
        print("🔄 Connecting to MySQL server...")

        # Connect without database first
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        print("✅ Connected to MySQL server successfully!")

        # Create database if it doesn't exist
        print(f"🔄 Creating database '{database_name}' if it doesn't exist...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"✅ Database '{database_name}' ready!")

        # Use the database
        cursor.execute(f"USE {database_name}")

        # Create conversations table
        print("🔄 Creating conversations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                project_title VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                status ENUM('active', 'completed', 'cancelled') DEFAULT 'active',
                teams TEXT,
                uploaded_file_name VARCHAR(500),
                uploaded_file_content LONGTEXT
            )
        """)
        print("✅ Conversations table created!")

        # Create messages table
        print("🔄 Creating messages table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT,
                role ENUM('user', 'assistant') NOT NULL,
                content LONGTEXT NOT NULL,
                model VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        print("✅ Messages table created!")

        # Create generated_files table
        print("🔄 Creating generated_files table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                conversation_id INT,
                file_type ENUM('markdown', 'prompt', 'cursor_guide') NOT NULL,
                file_name VARCHAR(500) NOT NULL,
                file_content LONGTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        print("✅ Generated_files table created!")

        connection.commit()
        print("\n🎉 Database setup completed successfully!")
        print(f"📊 Database: {database_name}")
        print("📋 Tables created: conversations, messages, generated_files")

        return True

    except Error as e:
        print(f"❌ Database setup failed: {e}")
        return False

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed.")

def test_connection():
    """Test database connection"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'ai_discussion_manager')
    }

    try:
        print("🔄 Testing database connection...")
        connection = mysql.connector.connect(**db_config)

        if connection.is_connected():
            db_info = connection.get_server_info()
            print("✅ Connected to MySQL server version", db_info)
            print(f"📊 Database: {db_config['database']}")

            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            print(f"📈 Total conversations in database: {count}")

            cursor.close()
            connection.close()
            return True

    except Error as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 AI Discussion Manager - Database Setup")
    print("=" * 50)

    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  No .env file found. Creating template...")

        env_template = """# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=ai_discussion_manager

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
"""

        with open('.env', 'w') as f:
            f.write(env_template)

        print("✅ Created .env template file")
        print("📝 Please edit .env file with your database credentials and OpenAI API key")
        print()

    print("🔧 Setting up database...")
    if create_database():
        print("\n🧪 Testing connection...")
        test_connection()

    print("\n📚 Setup complete! You can now run the AI Discussion Manager:")
    print("   streamlit run main.py")
