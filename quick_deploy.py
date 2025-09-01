#!/usr/bin/env python3
"""
Quick Deploy Script for AI Discussion Manager
"""

import subprocess
import sys

def main():
    print("🚀 Quick GitHub Deployment")
    print("=" * 40)

    # Ask for correct GitHub username
    print("\n📝 Please enter your CORRECT GitHub username:")
    print("   (Check: https://github.com/settings/profile)")
    print("   It should be just letters, numbers, and hyphens, no @ symbols")

    username = input("\nYour GitHub username: ").strip()

    if not username or '@' in username:
        print("❌ Invalid username. Please enter a valid GitHub username without @ symbols.")
        return

    # Confirm repository creation
    print(f"\n📦 Repository will be created at:")
    print(f"   https://github.com/{username}/ai-discussion-manager")
    print("\n⚠️  Make sure this repository exists on GitHub!")

    confirm = input("\nDoes this repository exist? (y/n): ").strip().lower()

    if confirm != 'y':
        print("\n❌ Please create the repository first, then run this script again.")
        return

    # Deploy
    repo_url = f"https://github.com/{username}/ai-discussion-manager.git"

    print(f"\n🚀 Deploying to: {repo_url}")

    try:
        # Remove existing remote if any
        subprocess.run("git remote remove origin", shell=True, capture_output=True)

        # Add new remote
        subprocess.run(f"git remote add origin {repo_url}", shell=True, check=True)

        # Push
        result = subprocess.run("git push -u origin master", shell=True, check=True, capture_output=True, text=True)

        print("\n" + "="*50)
        print("🎉 SUCCESS! DEPLOYMENT COMPLETE!")
        print("="*50)
        print(f"🌐 Live at: https://github.com/{username}/ai-discussion-manager")
        print(f"📖 README: https://github.com/{username}/ai-discussion-manager/blob/master/README.md")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Deployment failed: {e.stderr}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the repository exists")
        print("2. Check your GitHub username")
        print("3. Verify you have push permissions")
        print("4. Try again in a few minutes")

if __name__ == "__main__":
    main()
