#!/usr/bin/env python3
"""
Quick GitHub Push Script for AI Discussion Manager
Run this after creating your GitHub repository.
"""

import subprocess
import sys

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

def main():
    """Main push function"""
    print("🚀 AI Discussion Manager - GitHub Push")
    print("=====================================")

    # Get GitHub username
    username = input("Enter your GitHub username: ").strip()
    if not username:
        print("❌ GitHub username is required")
        sys.exit(1)

    repo_url = f"https://github.com/{username}/ai-discussion-manager.git"

    print(f"\n📦 Pushing to: {repo_url}")

    # Check if remote already exists
    success, remotes = run_command("git remote -v", "Checking existing remotes")

    if "origin" in remotes:
        print("⚠️  Remote 'origin' already exists. Removing it first...")
        run_command("git remote remove origin", "Removing existing origin")

    # Add remote
    success, _ = run_command(f"git remote add origin {repo_url}", "Adding GitHub remote")
    if not success:
        print("❌ Failed to add remote. Please check your username and try again.")
        sys.exit(1)

    # Push code
    success, _ = run_command("git push -u origin master", "Pushing code to GitHub")
    if success:
        print("\n" + "="*50)
        print("🎉 SUCCESS! Your AI Discussion Manager is now live on GitHub!")
        print("="*50)
        print(f"🌐 Repository URL: https://github.com/{username}/ai-discussion-manager")
        print("📖 View your README: https://github.com/{username}/ai-discussion-manager/blob/master/README.md")
        print("\n📋 What's next:")
        print("- ⭐ Star your repository")
        print("- 📝 Add a proper description")
        print("- 👥 Share with the community")
        print("- 🐛 Create issues for improvements")
        print("- 🔄 Fork and contribute!")
    else:
        print("\n❌ Push failed. Please check:")
        print("- Your GitHub username is correct")
        print("- You have created the repository on GitHub")
        print("- You have the necessary permissions")
        print("- Your internet connection is stable")

if __name__ == "__main__":
    main()