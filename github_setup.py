#!/usr/bin/env python3
"""
Simple GitHub Setup Script for AI Discussion Manager
Provides step-by-step instructions for manual GitHub deployment.
"""

import subprocess
import sys
from pathlib import Path

def print_header():
    """Print deployment header"""
    print("\n" + "="*70)
    print("🚀 AI DISCUSSION MANAGER - GITHUB DEPLOYMENT")
    print("="*70)
    print("🤖 Your AI-powered collaborative development tool is ready for GitHub!")

def check_files():
    """Check if all necessary files are present"""
    print("\n📋 Checking deployment files...")

    required_files = [
        'main.py', 'requirements.txt', 'README.md', '.gitignore',
        'setup_database.py', 'test_connection.py'
    ]

    all_present = True
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING!")
            all_present = False

    if all_present:
        print("\n🎉 All required files are present!")
    else:
        print("\n⚠️  Some files are missing. Please check the project structure.")

    return all_present

def show_github_setup_steps():
    """Show step-by-step GitHub setup instructions"""
    print("\n" + "="*70)
    print("📖 STEP-BY-STEP GITHUB DEPLOYMENT GUIDE")
    print("="*70)

    print("\n🔥 STEP 1: Create GitHub Repository")
    print("-" * 40)
    print("1. Open your web browser and go to: https://github.com/new")
    print("2. Repository name: ai-discussion-manager")
    print("3. Description: 🤖 AI-powered collaborative development tool for multi-disciplinary project analysis")
    print("4. Make it Public (recommended for showcasing)")
    print("5. ⚠️  IMPORTANT: Leave all checkboxes UNCHECKED (no README, .gitignore, license)")
    print("6. Click 'Create repository'")

    print("\n🔗 STEP 2: Get Repository URL")
    print("-" * 40)
    print("After creating the repository, GitHub will show you the repository URL.")
    print("It will look like: https://github.com/YOUR_USERNAME/ai-discussion-manager.git")
    print("Copy this URL for the next step.")

    print("\n📤 STEP 3: Push Code to GitHub")
    print("-" * 40)
    print("Run these commands in your terminal (replace YOUR_USERNAME with your GitHub username):")

    print("\n   # Add the GitHub repository as remote origin")
    print("   git remote add origin https://github.com/YOUR_USERNAME/ai-discussion-manager.git")

    print("\n   # Push your code to GitHub")
    print("   git push -u origin master")

    print("\n🔧 STEP 4: Verify Deployment")
    print("-" * 40)
    print("1. Go to your repository URL in the browser")
    print("2. You should see all your files listed")
    print("3. Click on README.md to see the project description")

def show_additional_setup():
    """Show additional GitHub setup options"""
    print("\n" + "="*70)
    print("🎯 OPTIONAL: ENHANCE YOUR GITHUB REPOSITORY")
    print("="*70)

    print("\n📊 Repository Settings:")
    print("- Go to Settings → General")
    print("- Add topics: ai, machine-learning, development-tools, collaboration")
    print("- Add website: (leave empty for now)")

    print("\n📖 GitHub Pages (for documentation):")
    print("- Go to Settings → Pages")
    print("- Source: Deploy from a branch")
    print("- Branch: master, folder: / (root)")
    print("- Your docs will be available at: https://YOUR_USERNAME.github.io/ai-discussion-manager")

    print("\n🔒 Security:")
    print("- Go to Settings → Security → Code security and analysis")
    print("- Enable Dependabot alerts")
    print("- Enable Dependabot security updates")

    print("\n🤝 Contributing:")
    print("- The repository already has CONTRIBUTING.md")
    print("- Consider adding issue templates and PR templates")

def show_deployment_commands():
    """Show the exact commands to run"""
    print("\n" + "="*70)
    print("💻 EXACT COMMANDS TO RUN")
    print("="*70)

    print("\n# Replace YOUR_USERNAME with your actual GitHub username")
    print("git remote add origin https://github.com/YOUR_USERNAME/ai-discussion-manager.git")
    print("git push -u origin master")
    print("")
    print("# That's it! Your AI Discussion Manager will be live on GitHub!")

def main():
    """Main function"""
    print_header()

    if not check_files():
        print("\n❌ Cannot proceed with deployment. Missing required files.")
        sys.exit(1)

    show_github_setup_steps()
    show_deployment_commands()
    show_additional_setup()

    print("\n" + "="*70)
    print("🎉 READY FOR DEPLOYMENT!")
    print("="*70)
    print("Your AI Discussion Manager is ready to be deployed to GitHub!")
    print("Follow the steps above to make your project live.")
    print("\n📞 Need help? Check the README.md file for detailed setup instructions.")

if __name__ == "__main__":
    main()
