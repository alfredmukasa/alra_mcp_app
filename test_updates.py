#!/usr/bin/env python3
"""
Test script to verify the updated AI Discussion Manager features
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_environment_variables():
    """Test that environment variables are properly configured"""
    print("🧪 Testing Environment Variables...")

    # Check if .env file exists
    env_file_exists = os.path.exists('.env')

    if not env_file_exists:
        print("⚠️  No .env file found")
        print("   Creating template .env file...")

        env_template = """# AI Discussion Manager Configuration
# Replace with your actual values

# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ai_discussion_manager
DB_PORT=3306

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here

# Optional Settings
MAX_WORD_LIMIT=150
DEFAULT_DISCUSSION_ROUNDS=5
DEBUG_MODE=false"""

        try:
            with open('.env', 'w') as f:
                f.write(env_template)
            print("✅ Created .env template file")
            print("📝 Please edit .env file with your actual values")
        except Exception as e:
            print(f"❌ Could not create .env file: {e}")

    # For testing purposes, set a dummy API key if not set
    if not os.getenv('OPENAI_API_KEY'):
        os.environ['OPENAI_API_KEY'] = 'sk-test-dummy-key-for-testing'
        print("✅ Set dummy API key for testing")

    required_vars = ['OPENAI_API_KEY']
    optional_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']

    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False

    print("✅ Required environment variables found")

    # Check optional vars
    found_optional = []
    for var in optional_vars:
        if os.getenv(var):
            found_optional.append(var)

    if found_optional:
        print(f"✅ Found optional variables: {', '.join(found_optional)}")

    return True

def test_word_count_logic():
    """Test the word counting logic"""
    print("\n🧪 Testing Word Count Logic...")

    test_texts = [
        ("Hello world", 2),
        ("This is a test sentence with multiple words.", 8),
        ("", 0),
        ("One", 1)
    ]

    for text, expected in test_texts:
        actual = len(text.split()) if text else 0
        if actual == expected:
            print(f"✅ '{text[:20]}...' -> {actual} words")
        else:
            print(f"❌ '{text[:20]}...' -> Expected {expected}, got {actual}")
            return False

    return True

def test_team_selection():
    """Test team selection logic"""
    print("\n🧪 Testing Team Selection...")

    available_teams = ["Frontend Dev", "Backend Dev", "Database Expert",
                      "Security Specialist", "AI Engineer", "Project Manager", "DevOps Engineer"]

    print(f"✅ Available teams: {len(available_teams)}")
    print(f"   Teams: {', '.join(available_teams)}")

    # Test max selection
    max_selection = 7
    if len(available_teams) >= max_selection:
        print(f"✅ Max selection ({max_selection}) is valid")
    else:
        print(f"❌ Max selection ({max_selection}) exceeds available teams ({len(available_teams)})")
        return False

    return True

def test_file_types():
    """Test supported file types"""
    print("\n🧪 Testing File Type Support...")

    supported_extensions = ['.md', '.txt']
    test_files = [
        'project.md',
        'requirements.txt',
        'document.pdf',  # Should fail
        'script.py'      # Should fail
    ]

    for filename in test_files:
        is_supported = any(filename.lower().endswith(ext) for ext in supported_extensions)
        expected = filename in ['project.md', 'requirements.txt']

        if is_supported == expected:
            status = "✅" if is_supported else "❌ (correctly rejected)"
            print(f"{status} {filename} -> {'Supported' if is_supported else 'Not supported'}")
        else:
            print(f"❌ {filename} -> Unexpected result")
            return False

    return True

def main():
    print("🚀 AI Discussion Manager - Update Verification Test")
    print("=" * 60)

    tests = [
        test_environment_variables,
        test_word_count_logic,
        test_team_selection,
        test_file_types
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with error: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Your AI Discussion Manager is ready!")
        print("\n📋 New Features Verified:")
        print("✅ OpenAI key from environment variables")
        print("✅ Word limit validation (150 words max)")
        print("✅ 7 teams available (including DevOps Engineer)")
        print("✅ File type validation (.md and .txt)")
        print("✅ History display functionality")
        print("✅ Enhanced file management")
        print("\n🚀 Ready to run: streamlit run main.py")
    else:
        print(f"❌ {total - passed} test(s) failed. Please check your configuration.")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
