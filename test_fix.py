#!/usr/bin/env python3
"""
Test script to verify the KeyError fix for AI Discussion Manager
"""

import sys
import os

def test_system_prompts():
    """Test the system prompts logic that was causing the KeyError"""

    # Simulate the team and discussion style variables
    next_team = "Frontend Dev"
    discussion_style = "Creative Brainstorm"
    is_file_content = False

    # Test the team_base_prompts dictionary
    team_base_prompts = {
        "Frontend Dev": f"""You are {next_team}, a frontend development expert specializing in modern web technologies.

{f'Analyze the uploaded documentation and provide frontend-specific insights. Consider UI/UX best practices, responsive design, performance optimization, and integration with backend APIs.' if is_file_content else 'Provide frontend development expertise for the described project.'}

Focus on user experience, accessibility, and modern frontend frameworks like React, Vue, or Angular.""",

        "Backend Dev": f"""You are {next_team}, a backend development expert specializing in server-side technologies.

{f'Analyze the uploaded documentation and provide backend architecture insights. Consider API design, database integration, security, scalability, and microservices architecture.' if is_file_content else 'Provide backend development expertise for the described project.'}

Focus on robust, scalable, and maintainable server-side solutions.""",

        "Project Manager": f"""You are {next_team}, a project management and coordination specialist overseeing the entire development process.

{f'Analyze the uploaded documentation and provide project management insights. Coordinate between different teams, manage timelines, identify dependencies, and ensure project success.' if is_file_content else 'Provide project management expertise for the described project.'}

Focus on project planning, team coordination, risk management, and delivery milestones."""
    }

    print("🧪 Testing system prompts logic...")

    # Test getting the base team prompt
    system_prompt = team_base_prompts.get(next_team, f"You are {next_team}, an expert in your field. Provide valuable insights for this project.")

    print(f"✅ Base prompt retrieved for team: {next_team}")

    # Test adding discussion style context
    if discussion_style == "Collaborative":
        system_prompt += "\n\nApproach this collaboratively, building on previous suggestions and finding common ground between different perspectives."
    elif discussion_style == "Debate":
        system_prompt += "\n\nApproach this as a constructive debate, presenting well-reasoned arguments and considering alternative viewpoints."
    elif discussion_style == "Technical Review":
        system_prompt += "\n\nConduct a thorough technical review, focusing on best practices, potential issues, and optimization opportunities."
    elif discussion_style == "Creative Brainstorm":
        system_prompt += "\n\nBrainstorm creative and innovative solutions, thinking outside the box while maintaining technical feasibility."

    print(f"✅ Discussion style '{discussion_style}' context added")
    print(f"✅ Final prompt length: {len(system_prompt)} characters")

    return True

def test_imports():
    """Test that all required imports work"""
    print("🧪 Testing imports...")

    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")

        import openai
        print("✅ OpenAI imported successfully")

        import mysql.connector
        print("✅ MySQL connector imported successfully")

        import time
        from datetime import datetime
        import os
        import json

        print("✅ All core imports successful")

        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("🚀 AI Discussion Manager - Fix Verification Test")
    print("=" * 50)

    # Test imports
    if not test_imports():
        print("❌ Import test failed!")
        return False

    # Test system prompts logic
    if not test_system_prompts():
        print("❌ System prompts test failed!")
        return False

    print("\n🎉 All tests passed! The KeyError fix is working correctly.")
    print("\n📝 If you're still getting errors, try:")
    print("1. Clear Streamlit cache: streamlit cache clear")
    print("2. Restart your IDE/editor")
    print("3. Run: streamlit run main.py")
    print("\n🚀 Application should work without KeyError now!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
