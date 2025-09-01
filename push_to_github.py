#!/usr/bin/env python3
"""
Script to help set up and push the AI Discussion Manager to GitHub
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Command: {command}")

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 AI Discussion Manager - GitHub Setup Assistant")
    print("=" * 60)

    # Check if git is initialized
    if not os.path.exists('.git'):
        print("❌ Git repository not found. Please run 'git init' first.")
        sys.exit(1)

    # Get GitHub repository information
    print("\n📋 GitHub Repository Setup")
    print("1. Go to https://github.com and sign in")
    print("2. Click 'New repository'")
    print("3. Repository name: ai-discussion-manager")
    print("4. Make it public or private (your choice)")
    print("5. DO NOT initialize with README, .gitignore, or license")
    print("6. Click 'Create repository'")

    repo_url = input("\nEnter your GitHub repository URL: ").strip()

    if not repo_url:
        print("❌ Repository URL is required")
        sys.exit(1)

    # Remove .git directory if it exists (to start fresh)
    if os.path.exists('.git'):
        print("\n🧹 Preparing repository...")
        run_command("rmdir /s /q .git", "Remove existing git directory")

    # Initialize new repository
    run_command("git init", "Initialize new Git repository")

    # Add all files
    run_command("git add .", "Add all files to staging")

    # Initial commit
    commit_message = "Initial commit: AI Discussion Manager v2.0

🚀 Complete AI-powered collaborative development tool

Features:
- 7 AI specialist teams (Frontend, Backend, Database, Security, AI, Project Manager, DevOps)
- MySQL database integration for persistent storage
- File upload support (.md and .txt files)
- Word limit validation (150 words max)
- Automatic documentation generation
- Conversation history management
- Environment-based configuration

Tech Stack:
- Python 3.8+
- Streamlit (web interface)
- OpenAI API integration
- MySQL database

Setup:
1. Configure .env file with database and OpenAI credentials
2. Run: python setup_database.py
3. Start: streamlit run main.py"

    run_command(f'git commit -m "{commit_message}"', "Create initial commit")

    # Add remote origin
    run_command(f"git remote add origin {repo_url}", "Add GitHub remote")

    # Push to GitHub
    run_command("git push -u origin master", "Push to GitHub")

    print("\n🎉 Repository setup complete!")
    print("\n📋 Next steps:")
    print("1. Visit your GitHub repository")
    print("2. Enable GitHub Pages if desired")
    print("3. Add collaborators if needed")
    print("4. Create issues for features/bugs")
    print("5. Set up branch protection rules")

    print("\n📖 Repository URL:", repo_url)
    print("\n🚀 Your AI Discussion Manager is now live on GitHub!")

if __name__ == "__main__":
    main()
