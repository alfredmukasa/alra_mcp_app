#!/usr/bin/env python3
"""
GitHub Deployment Script for AI Discussion Manager
This script helps deploy the application to GitHub with proper setup.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description=""):
    """Run a shell command and return success status"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return False, e.stderr

def create_github_repo():
    """Guide user through GitHub repository creation"""
    print("\n" + "="*60)
    print("🚀 GITHUB REPOSITORY DEPLOYMENT")
    print("="*60)

    # Check if GitHub CLI is available
    success, _ = run_command("gh --version", "Checking GitHub CLI installation")
    if not success:
        print("\n❌ GitHub CLI not found. Please install it first:")
        print("   https://cli.github.com/")
        print("\nAlternatively, create repository manually at: https://github.com/new")
        return False

    # Get repository details from user
    repo_name = input("\n📝 Enter repository name (ai-discussion-manager): ").strip()
    if not repo_name:
        repo_name = "ai-discussion-manager"

    repo_description = "🤖 AI-powered collaborative development tool for multi-disciplinary project analysis and planning"

    visibility = input("🔒 Repository visibility (public/private) [public]: ").strip().lower()
    if visibility not in ['private', 'public']:
        visibility = 'public'

    # Create GitHub repository
    print(f"\n📦 Creating GitHub repository: {repo_name}")
    cmd = f'gh repo create {repo_name} --description "{repo_description}" --{visibility} --source=. --remote=origin --push'
    success, output = run_command(cmd, "Creating GitHub repository")

    if success:
        print(f"\n🎉 Repository created successfully!")
        print(f"🌐 Repository URL: https://github.com/{get_github_username()}/{repo_name}")
        return True
    else:
        print("\n❌ Failed to create repository automatically.")
        print("Please create it manually at: https://github.com/new")
        print(f"Then run: git remote add origin https://github.com/YOUR_USERNAME/{repo_name}.git")
        print("         git push -u origin master")
        return False

def get_github_username():
    """Get GitHub username from gh CLI"""
    try:
        result = subprocess.run("gh api user -q .login", shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        return "YOUR_USERNAME"

def push_to_github():
    """Push code to existing GitHub repository"""
    print("\n" + "="*60)
    print("📤 PUSHING TO GITHUB")
    print("="*60)

    # Check for existing remote
    success, remotes = run_command("git remote -v", "Checking existing remotes")
    if "origin" in remotes:
        print("✅ Remote 'origin' already exists")
    else:
        # Ask for repository URL
        repo_url = input("\n🔗 Enter your GitHub repository URL: ").strip()
        if not repo_url:
            print("❌ Repository URL is required")
            return False

        success, _ = run_command(f"git remote add origin {repo_url}", "Adding remote origin")
        if not success:
            return False

    # Push to GitHub
    success, _ = run_command("git push -u origin master", "Pushing code to GitHub")
    if success:
        print("\n🎉 Code successfully pushed to GitHub!")
        return True
    else:
        return False

def setup_deployment_files():
    """Ensure all deployment files are present"""
    print("\n" + "="*60)
    print("📋 DEPLOYMENT FILE CHECK")
    print("="*60)

    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        '.gitignore',
        'setup_database.py',
        'test_connection.py'
    ]

    optional_files = [
        'CONTRIBUTING.md',
        'LICENSE',
        '.github/workflows/ci.yml',
        'push_to_github.py',
        'deploy_to_github.py'
    ]

    print("Required files:")
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")

    print("\nOptional files:")
    for file in optional_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"⚠️  {file} - Not found")

def main():
    """Main deployment function"""
    print("🤖 AI Discussion Manager - GitHub Deployment")
    print("==========================================")

    # Check if we're in the right directory
    if not Path('main.py').exists():
        print("❌ Error: main.py not found. Please run this script from the project root directory.")
        sys.exit(1)

    # Setup deployment files check
    setup_deployment_files()

    # Choose deployment method
    print("\n" + "="*60)
    print("DEPLOYMENT OPTIONS")
    print("="*60)
    print("1. 🚀 Create new GitHub repository (requires GitHub CLI)")
    print("2. 📤 Push to existing GitHub repository")
    print("3. ❓ Help with manual setup")

    choice = input("\nChoose option (1-3): ").strip()

    if choice == '1':
        if create_github_repo():
            print("\n✅ Deployment completed successfully!")
        else:
            print("\n❌ Deployment failed. Please try manual setup.")
    elif choice == '2':
        if push_to_github():
            print("\n✅ Code pushed to GitHub successfully!")
        else:
            print("\n❌ Push failed. Please check your repository URL and try again.")
    elif choice == '3':
        show_manual_setup_help()
    else:
        print("❌ Invalid choice. Please run the script again.")

    # If GitHub CLI is not available, automatically show manual help
    if choice == '1' and not success:
        print("\n" + "="*60)
        print("📖 AUTOMATIC MANUAL SETUP (Since GitHub CLI is not available)")
        print("="*60)
        show_manual_setup_help()

def show_manual_setup_help():
    """Show manual setup instructions"""
    print("\n" + "="*60)
    print("📖 MANUAL GITHUB SETUP INSTRUCTIONS")
    print("="*60)

    print("\n1. 🌐 Go to GitHub.com and create a new repository:")
    print("   - Click the '+' icon → 'New repository'")
    print("   - Repository name: ai-discussion-manager")
    print("   - Description: AI-powered collaborative development tool")
    print("   - Make it Public or Private")
    print("   - DON'T initialize with README, .gitignore, or license")

    print("\n2. 🔗 Copy the repository URL from GitHub")

    print("\n3. 🖥️  Run these commands in your terminal:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/ai-discussion-manager.git")
    print("   git push -u origin master")

    print("\n4. 🎯 After successful push, your repository will be live at:")
    print("   https://github.com/YOUR_USERNAME/ai-discussion-manager")

    print("\n5. 📚 Additional setup (optional):")
    print("   - Add repository topics: ai, machine-learning, development-tools")
    print("   - Enable GitHub Pages for documentation")
    print("   - Set up branch protection rules")
    print("   - Configure repository settings")

if __name__ == "__main__":
    main()
