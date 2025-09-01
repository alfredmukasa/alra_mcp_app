import streamlit as st
import openai
import time
from datetime import datetime
from supabase import create_client, Client
import os
import json
from dotenv import load_dotenv
import re
import hashlib
from typing import Dict, List, Optional, Tuple
import requests
import mimetypes
import zipfile
from io import BytesIO
import tempfile
import shutil

# Load environment variables from .env file
load_dotenv()

# API Configuration
DEFAULT_OPENAI_MODELS = ["gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"]

# Theme Configuration
THEMES = {
    "light": {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "background": "#ffffff",
        "text": "#2c3e50",
        "sidebar": "#f8f9fa",
        "card": "#ffffff",
        "border": "#e9ecef"
    },
    "dark": {
        "primary": "#00d4ff",
        "secondary": "#ff6b6b",
        "background": "#1a1a1a",
        "text": "#ffffff",
        "sidebar": "#2d2d2d",
        "card": "#333333",
        "border": "#444444"
    },
    "modern": {
        "primary": "#6366f1",
        "secondary": "#f59e0b",
        "background": "#0f172a",
        "text": "#f8fafc",
        "sidebar": "#1e293b",
        "card": "#334155",
        "border": "#475569"
    }
}

def verify_openai_api_key(api_key: str) -> Tuple[bool, str]:
    """Verify OpenAI API key by making a test request"""
    if not api_key or not api_key.startswith('sk-'):
        return False, "❌ Invalid API key format. OpenAI keys should start with 'sk-'"

    try:
        client = openai.OpenAI(api_key=api_key)
        # Test with a minimal request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        return True, "✅ OpenAI API key verified successfully!"
    except openai.AuthenticationError:
        return False, "❌ Invalid API key. Please check your OpenAI API key."
    except openai.RateLimitError:
        return False, "⚠️ Rate limit exceeded. Your API key is valid but you may have hit rate limits."
    except Exception as e:
        return False, f"❌ API verification failed: {str(e)}"

def verify_supabase_credentials(url: str, key: str) -> Tuple[bool, str]:
    """Verify Supabase credentials by testing connection"""
    if not url or not url.startswith('https://'):
        return False, "❌ Invalid Supabase URL format. Should start with 'https://'"

    if not key or len(key) < 50:
        return False, "❌ Invalid Supabase key format. Key should be longer."

    try:
        supabase = create_client(url, key)
        # Test connection by trying to get table info
        result = supabase.table('conversations').select('id').limit(1).execute()
        return True, "✅ Supabase credentials verified successfully!"
    except Exception as e:
        error_msg = str(e).lower()
        if "relation" in error_msg and "does not exist" in error_msg:
            return False, "⚠️ Supabase connection successful, but tables don't exist yet. Please create the database tables."
        elif "invalid" in error_msg or "unauthorized" in error_msg:
            return False, "❌ Invalid Supabase credentials. Please check your URL and key."
        else:
            return False, f"❌ Supabase verification failed: {str(e)}"

def initialize_apis(openai_key: str = None, supabase_url: str = None, supabase_key: str = None) -> Dict[str, any]:
    """Initialize and verify API connections"""
    results = {
        "openai": {"verified": False, "message": "", "client": None},
        "supabase": {"verified": False, "message": "", "client": None}
    }

    # Verify OpenAI
    if openai_key:
        verified, message = verify_openai_api_key(openai_key)
        results["openai"]["verified"] = verified
        results["openai"]["message"] = message
        if verified:
            results["openai"]["client"] = openai.OpenAI(api_key=openai_key)

    # Verify Supabase
    if supabase_url and supabase_key:
        verified, message = verify_supabase_credentials(supabase_url, supabase_key)
        results["supabase"]["verified"] = verified
        results["supabase"]["message"] = message
        if verified:
            results["supabase"]["client"] = create_client(supabase_url, supabase_key)

    return results

# File Analysis Functions
def detect_language_from_file(file_path: str, content: str = None) -> str:
    """Detect programming language from file extension and content"""
    if not file_path:
        return "unknown"

    # Language detection by extension
    ext_to_lang = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.tsx': 'typescript',
        '.jsx': 'javascript', '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.cs': 'csharp',
        '.php': 'php', '.rb': 'ruby', '.go': 'go', '.rs': 'rust', '.swift': 'swift',
        '.kt': 'kotlin', '.scala': 'scala', '.html': 'html', '.css': 'css', '.scss': 'scss',
        '.sass': 'sass', '.less': 'less', '.json': 'json', '.xml': 'xml', '.yaml': 'yaml',
        '.yml': 'yaml', '.toml': 'toml', '.md': 'markdown', '.txt': 'text', '.sql': 'sql',
        '.sh': 'bash', '.ps1': 'powershell', '.r': 'r', '.m': 'matlab', '.pl': 'perl',
        '.lua': 'lua', '.dart': 'dart', '.vb': 'vb', '.fs': 'fsharp'
    }

    _, ext = os.path.splitext(file_path.lower())
    if ext in ext_to_lang:
        return ext_to_lang[ext]

    # Content-based detection for files without extensions
    if content:
        content_lower = content.lower()
        if 'import ' in content_lower and ('def ' in content_lower or 'class ' in content_lower):
            return 'python'
        if ('function' in content_lower or 'const ' in content_lower) and ('=>' in content or 'export' in content_lower):
            return 'javascript'
        if '<?php' in content_lower:
            return 'php'
        if ('public class' in content_lower or 'import java' in content_lower):
            return 'java'
        if ('#include' in content_lower and ('int main' in content_lower or 'cout' in content_lower)):
            return 'cpp'
        if 'using system' in content_lower:
            return 'csharp'

    return 'unknown'

def analyze_code_file(file_path: str, content: str) -> Dict[str, any]:
    """Analyze a code file and extract useful information"""
    analysis = {
        "language": detect_language_from_file(file_path, content),
        "lines": len(content.split('\n')),
        "characters": len(content),
        "functions": [],
        "classes": [],
        "imports": [],
        "complexity": "simple",
        "patterns": [],
        "suggestions": []
    }

    # Language-specific analysis
    if analysis["language"] == "python":
        analysis.update(analyze_python_file(content))
    elif analysis["language"] in ["javascript", "typescript"]:
        analysis.update(analyze_js_file(content))
    elif analysis["language"] == "java":
        analysis.update(analyze_java_file(content))

    # Calculate complexity
    analysis["complexity"] = calculate_complexity(content, analysis["language"])

    # Generate suggestions
    analysis["suggestions"] = generate_code_suggestions(analysis)

    return analysis

def analyze_python_file(content: str) -> Dict[str, List[str]]:
    """Analyze Python file content"""
    functions = re.findall(r'def\s+(\w+)\s*\(', content)
    classes = re.findall(r'class\s+(\w+)\s*[:\(]', content)
    imports = re.findall(r'(?:from\s+[\w.]+\s+import|import\s+[\w.]+)', content)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports
    }

def analyze_js_file(content: str) -> Dict[str, List[str]]:
    """Analyze JavaScript/TypeScript file content"""
    functions = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:\([^)]*\)\s*)?=>\s*\{?|(?:async\s+)?(?:function\s+)?(\w+)\s*\([^)]*\)\s*\{)', content)
    functions = [f for group in functions for f in group if f]  # Flatten and filter

    classes = re.findall(r'class\s+(\w+)', content)
    imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports
    }

def analyze_java_file(content: str) -> Dict[str, List[str]]:
    """Analyze Java file content"""
    functions = re.findall(r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\([^)]*\)', content)
    classes = re.findall(r'class\s+(\w+)', content)
    imports = re.findall(r'import\s+([^;]+);', content)

    return {
        "functions": functions,
        "classes": classes,
        "imports": imports
    }

def calculate_complexity(content: str, language: str) -> str:
    """Calculate code complexity"""
    lines = len(content.split('\n'))
    functions = len(re.findall(r'def\s+\w+' if language == 'python' else r'function\s+\w+', content))
    loops = len(re.findall(r'(for|while|if)\s*\(', content))
    complexity_score = functions + loops + (lines // 50)

    if complexity_score < 5:
        return "simple"
    elif complexity_score < 15:
        return "moderate"
    else:
        return "complex"

def generate_code_suggestions(analysis: Dict[str, any]) -> List[str]:
    """Generate code improvement suggestions"""
    suggestions = []

    if analysis["lines"] > 300:
        suggestions.append("Consider breaking this file into smaller modules")

    if len(analysis["functions"]) > 15:
        suggestions.append("This file has many functions - consider splitting into multiple files")

    if analysis["complexity"] == "complex":
        suggestions.append("Consider refactoring for better maintainability")

    if not analysis["classes"] and len(analysis["functions"]) > 5:
        suggestions.append("Consider organizing functions into classes")

    return suggestions

def analyze_folder_structure(folder_path: str) -> Dict[str, any]:
    """Analyze project folder structure"""
    structure = {
        "total_files": 0,
        "languages": {},
        "folders": [],
        "file_types": {},
        "largest_files": [],
        "project_type": "unknown"
    }

    for root, dirs, files in os.walk(folder_path):
        # Count folders
        for dir_name in dirs:
            structure["folders"].append(os.path.join(root, dir_name))

        # Analyze files
        for file in files:
            file_path = os.path.join(root, file)
            structure["total_files"] += 1

            # Get file size
            try:
                size = os.path.getsize(file_path)
                structure["largest_files"].append((file, size))
            except:
                pass

            # Detect language
            lang = detect_language_from_file(file)
            structure["languages"][lang] = structure["languages"].get(lang, 0) + 1

            # File type analysis
            _, ext = os.path.splitext(file.lower())
            structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1

    # Sort largest files
    structure["largest_files"] = sorted(structure["largest_files"], key=lambda x: x[1], reverse=True)[:10]

    # Determine project type
    if structure["languages"].get("python", 0) > structure["total_files"] * 0.3:
        structure["project_type"] = "python"
    elif structure["languages"].get("javascript", 0) > structure["total_files"] * 0.3:
        structure["project_type"] = "javascript"
    elif structure["languages"].get("java", 0) > structure["total_files"] * 0.3:
        structure["project_type"] = "java"

    return structure

def get_db_connection():
    """Create and return Supabase client"""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("Supabase configuration missing. Please check SUPABASE_URL and SUPABASE_KEY environment variables.")
            return None
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        st.error(f"Supabase connection failed: {e}")
        return None

def create_database_schema():
    """Create database tables if they don't exist"""
    supabase = get_db_connection()
    if not supabase:
        return False

    try:
        # Create conversations table
        supabase.table('conversations').select('*').limit(1).execute()  # Test if table exists
    except:
        # Table doesn't exist, create it
        try:
            # Note: In Supabase, tables are typically created via the dashboard or migrations
            # This is a placeholder - actual table creation should be done in Supabase dashboard
            st.warning("Tables need to be created in Supabase dashboard. Please create the following tables:")
            st.code("""
conversations:
- id: integer (primary key, auto-increment)
- session_id: text
- project_title: text
- created_at: timestamp with time zone (default: now())
- updated_at: timestamp with time zone (default: now())
- status: text (check constraint: 'active', 'completed', 'cancelled')
- teams: text
- uploaded_file_name: text
- uploaded_file_content: text

messages:
- id: integer (primary key, auto-increment)
- conversation_id: integer (foreign key to conversations.id)
- role: text (check constraint: 'user', 'assistant')
- content: text
- model: text
- timestamp: timestamp with time zone (default: now())

generated_files:
- id: integer (primary key, auto-increment)
- conversation_id: integer (foreign key to conversations.id)
- file_type: text (check constraint: 'markdown', 'prompt', 'cursor_guide')
- file_name: text
- file_content: text
- created_at: timestamp with time zone (default: now())
            """)
            return False
        except Exception as e:
            st.error(f"Failed to create database schema: {e}")
            return False

        return True

def save_conversation_to_db(session_id, project_title, teams, uploaded_file_name=None, uploaded_file_content=None):
    """Save conversation metadata to database"""
    supabase = get_db_connection()
    if not supabase:
        return None

    try:
        data = {
            'session_id': session_id,
            'project_title': project_title,
            'teams': json.dumps(teams) if teams else None,
            'uploaded_file_name': uploaded_file_name,
            'uploaded_file_content': uploaded_file_content
        }
        result = supabase.table('conversations').insert(data).execute()
        if result.data:
            return result.data[0]['id']
        return None
    except Exception as e:
        st.error(f"Failed to save conversation: {e}")
        return None

def save_message_to_db(conversation_id, role, content, model=None):
    """Save individual message to database"""
    supabase = get_db_connection()
    if not supabase:
        return False

    try:
        data = {
            'conversation_id': conversation_id,
            'role': role,
            'content': content,
            'model': model
        }
        result = supabase.table('messages').insert(data).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Failed to save message: {e}")
        return False

def save_generated_file_to_db(conversation_id, file_type, file_name, file_content):
    """Save generated file to database"""
    supabase = get_db_connection()
    if not supabase:
        return False

    try:
        data = {
            'conversation_id': conversation_id,
            'file_type': file_type,
            'file_name': file_name,
            'file_content': file_content
        }
        result = supabase.table('generated_files').insert(data).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Failed to save generated file: {e}")
        return False

def load_conversation_history():
    """Load conversation history list from database"""
    supabase = get_db_connection()
    if not supabase:
        return None

    try:
        result = supabase.table('conversations').select('id, session_id, project_title, created_at, status, teams').order('created_at', desc=True).execute()

        conversations = result.data

        # Convert teams JSON string back to list
        for conv in conversations:
            if conv.get('teams'):
                try:
                    conv['teams'] = json.loads(conv['teams'])
                except:
                    conv['teams'] = []

        return conversations

    except Exception as e:
        st.error(f"Failed to load conversation history: {e}")
        return None

def load_conversation_from_db(session_id):
    """Load conversation data from database"""
    supabase = get_db_connection()
    if not supabase:
        return None

    try:
        # Get conversation
        conv_result = supabase.table('conversations').select('*').eq('session_id', session_id).execute()
        if not conv_result.data:
            return None

        conversation = conv_result.data[0]

        # Get messages
        msg_result = supabase.table('messages').select('role, content, model, timestamp').eq('conversation_id', conversation['id']).order('timestamp').execute()
        messages = msg_result.data

        # Get generated files
        files_result = supabase.table('generated_files').select('file_type, file_name, file_content, created_at').eq('conversation_id', conversation['id']).order('created_at', desc=True).execute()
        files = files_result.data

        return {
            'conversation': conversation,
            'messages': messages,
            'files': files
        }

    except Exception as e:
        st.error(f"Failed to load conversation: {e}")
        return None

# Modern Page Configuration
st.set_page_config(
    page_title="🚀 AI Code Analyst Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/alfredmukasa/alra_mcp_app',
        'Report a bug': 'https://github.com/alfredmukasa/alra_mcp_app/issues',
        'About': '''
        ### 🚀 AI Code Analyst Pro
        An advanced AI-powered code analysis and project management tool.

        **Features:**
        - 🔍 Multi-language code analysis
        - 📁 Project structure insights
        - 🤖 AI-powered recommendations
        - 🎨 Modern UI with themes
        - 📊 Real-time collaboration
        - 📈 Performance monitoring
        '''
    }
)

# Custom CSS for Modern UI
def load_css():
    """Load custom CSS for modern styling"""
    st.markdown("""
    <style>
    /* Modern CSS for AI Code Analyst Pro */

    /* Main container styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    .main-header h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }

    /* Card styling */
    .modern-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 1px solid #e1e5e9;
        transition: all 0.3s ease;
    }

    .modern-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
    }

    .modern-card h3 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }

    /* Status indicators */
    .status-success {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
    }

    .status-error {
        background: linear-gradient(135deg, #f44336, #d32f2f);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
    }

    .status-warning {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
    }

    /* Button styling */
    .modern-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        display: inline-block;
        margin: 0.5rem;
    }

    .modern-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    /* Progress bar styling */
    .progress-container {
        background: #f0f2f5;
        border-radius: 10px;
        height: 8px;
        margin: 1rem 0;
        overflow: hidden;
    }

    .progress-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    /* Code analysis cards */
    .analysis-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
    }

    .analysis-card h4 {
        margin: 0 0 0.5rem 0;
        font-size: 1.2rem;
    }

    .analysis-card .metric {
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
    }

    /* File upload styling */
    .upload-zone {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
        transition: all 0.3s ease;
        margin: 1rem 0;
    }

    .upload-zone:hover {
        background: #eef2ff;
        border-color: #764ba2;
    }

    /* Sidebar styling */
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }

    /* Animation for loading states */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }

    .loading {
        animation: pulse 1.5s infinite;
    }

    /* Theme toggle */
    .theme-toggle {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 1rem 0;
    }

    .theme-toggle button {
        background: none;
        border: 2px solid #667eea;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
    }

    .theme-toggle button:hover {
        background: #667eea;
        color: white;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }

        .modern-card {
            padding: 1rem;
        }

        .main-header {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'apis_verified' not in st.session_state:
        st.session_state.apis_verified = False
    if 'openai_client' not in st.session_state:
        st.session_state.openai_client = None
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = None
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "dashboard"

# Load CSS and initialize session state
load_css()
initialize_session_state()

# Initialize database schema on startup
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = create_database_schema()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'discussion_active' not in st.session_state:
    st.session_state.discussion_active = False
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = None
if 'teams' not in st.session_state:
    st.session_state.teams = []
if 'uploaded_file_content' not in st.session_state:
    st.session_state.uploaded_file_content = ""
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = ""
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None
if 'generated_files' not in st.session_state:
    st.session_state.generated_files = []
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

def initialize_openai():
    """Initialize OpenAI client using environment variable"""
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            return False, "❌ OPENAI_API_KEY not found in environment variables. Please set it in your .env file."

        st.session_state.openai_client = openai.OpenAI(api_key=openai_key)
        # Test call
        _ = st.session_state.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        return True, "✅ OpenAI initialized successfully!"
    except Exception as e:
        return False, f"Error initializing OpenAI: {str(e)}"

def call_openai(messages, system_prompt=""):
    """Call OpenAI API"""
    try:
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = st.session_state.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_messages,
            max_tokens=800,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"OpenAI Error: {str(e)}"

def add_message(role, content, model=""):
    """Add message to conversation history"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.messages.append({
        "role": role,
        "content": content,
        "model": model,
        "timestamp": timestamp
    })

def display_conversation():
    """Display conversation history"""
    for msg in st.session_state.messages:
        if msg["model"]:
            with st.chat_message("assistant", avatar="🟢"):
                st.write(f"**{msg['model']}** - {msg['timestamp']}")
                st.write(msg["content"])
        else:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract content"""
    if uploaded_file is not None:
        try:
            # Read file content based on type
            if uploaded_file.name.lower().endswith('.md'):
                content = uploaded_file.read().decode('utf-8')
            elif uploaded_file.name.lower().endswith('.txt'):
                content = uploaded_file.read().decode('utf-8')
            else:
                return False, "Unsupported file type. Please upload .md or .txt files only."

            st.session_state.uploaded_file_content = content
            st.session_state.uploaded_file_name = uploaded_file.name
            return True, f"✅ File '{uploaded_file.name}' loaded successfully!"

        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    return False, "No file uploaded."

def generate_project_md_file(messages, project_title, teams):
    """Generate a comprehensive MD file with project specifications and guidelines"""
    md_content = f"""# {project_title}

## 📋 Project Overview

**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Teams Involved:** {", ".join(teams)}
**Status:** Active Development

---

## 🎯 Project Goals & Requirements

"""

    # Extract user/project description from first message
    if messages and messages[0]['role'] == 'user':
        md_content += f"{messages[0]['content']}\n\n"

    md_content += "## 👥 Team Analysis & Recommendations\n\n"

    # Group messages by team
    team_contributions = {}
    for msg in messages[1:]:  # Skip the initial user message
        if msg.get('model'):
            team = msg['model']
            if team not in team_contributions:
                team_contributions[team] = []
            team_contributions[team].append(msg['content'])

    # Add team-specific sections
    for team, contributions in team_contributions.items():
        md_content += f"### 🔧 {team} Analysis\n\n"
        for i, contribution in enumerate(contributions, 1):
            # Clean and format the contribution
            clean_contribution = contribution.replace("**", "").replace("*", "")
            md_content += f"#### Contribution {i}\n{contribution}\n\n"

    md_content += """## 📚 Implementation Guidelines

### 🏗️ Architecture Recommendations
- Follow modular design principles
- Implement proper error handling
- Use appropriate design patterns
- Consider scalability from the start

### 🔒 Security Considerations
- Implement authentication and authorization
- Use secure coding practices
- Regular security audits
- Data encryption where necessary

### 🚀 Performance Optimization
- Optimize database queries
- Implement caching strategies
- Use CDN for static assets
- Monitor and profile application performance

### 🧪 Testing Strategy
- Unit tests for all components
- Integration tests for API endpoints
- End-to-end testing for critical workflows
- Performance testing

### 📦 Deployment & DevOps
- CI/CD pipeline implementation
- Containerization with Docker
- Infrastructure as Code
- Monitoring and logging

## 🎯 Next Steps

1. **Review and Approval**: All team leads should review this specification
2. **Architecture Design**: Create detailed system architecture diagrams
3. **Technology Stack Finalization**: Confirm all technology choices
4. **Development Timeline**: Create detailed project timeline
5. **Resource Allocation**: Assign team members to specific tasks

---

*This document was generated by AI Discussion Manager - An intelligent collaborative development tool*
"""

    return md_content

def generate_cursor_prompt_file(messages, project_title, teams):
    """Generate a comprehensive prompt file for Cursor IDE development"""
    prompt_content = f"""# Cursor IDE Development Guidelines for {project_title}

## 📋 Project Context

**Project:** {project_title}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Teams:** {", ".join(teams)}

## 🎯 Development Objectives

"""

    # Extract project goals from messages
    if messages and messages[0]['role'] == 'user':
        prompt_content += f"{messages[0]['content']}\n\n"

    prompt_content += """## 🛠️ Technology Stack & Best Practices

### Frontend Development
```javascript
// Modern React/Vue/Angular patterns
- Use functional components with hooks
- Implement TypeScript for type safety
- Follow component composition patterns
- Use CSS-in-JS or utility-first CSS frameworks
- Implement responsive design principles
```

### Backend Development
```python
# Python/Node.js/Java backend patterns
- Follow RESTful API design principles
- Implement proper error handling and logging
- Use async/await for asynchronous operations
- Implement data validation and sanitization
- Use environment variables for configuration
```

### Database Design
```sql
-- Database best practices
- Use proper indexing strategies
- Implement foreign key relationships
- Use transactions for data consistency
- Implement database migrations
- Regular backup and recovery procedures
```

## 🤖 AI-Assisted Development Guidelines

### Code Generation Prompts
```
"Create a REST API endpoint for user authentication with JWT tokens"
"Generate a React component for data visualization with error handling"
"Create database models with relationships and validation"
"Implement middleware for request logging and error handling"
```

### Code Review Prompts
```
"Review this code for security vulnerabilities"
"Optimize this database query for better performance"
"Refactor this component for better maintainability"
"Suggest improvements for error handling"
```

### Testing Prompts
```
"Generate unit tests for this function"
"Create integration tests for this API endpoint"
"Write end-to-end test scenarios"
"Generate mock data for testing"
```

## 🔧 Development Workflow

### 1. Feature Development
```bash
# Standard workflow
1. Create feature branch
2. Implement feature with tests
3. Code review and AI-assisted improvements
4. Merge to main branch
```

### 2. Code Quality Checks
```javascript
// ESLint configuration
{
  "extends": ["eslint:recommended", "@typescript-eslint/recommended"],
  "parser": "@typescript-eslint/parser",
  "rules": {
    "no-unused-vars": "error",
    "prefer-const": "error",
    "no-console": "warn"
  }
}
```

### 3. Performance Optimization
```javascript
// Performance monitoring
- Use React DevTools for component analysis
- Implement lazy loading for routes
- Optimize bundle size with code splitting
- Use service workers for caching
```

## 📚 Team-Specific Guidelines

"""

    # Add team-specific guidelines based on the discussion
    team_guidelines = {
        "Frontend Dev": """
### 🎨 Frontend Guidelines
- Prioritize user experience and accessibility
- Use semantic HTML and ARIA attributes
- Implement responsive design with mobile-first approach
- Optimize for Core Web Vitals metrics
- Use modern CSS features and animations judiciously""",

        "Backend Dev": """
### ⚙️ Backend Guidelines
- Implement proper API versioning
- Use middleware for cross-cutting concerns
- Implement rate limiting and request validation
- Use connection pooling for database operations
- Implement proper logging and monitoring""",

        "Database Expert": """
### 🗄️ Database Guidelines
- Design normalized database schemas
- Implement proper indexing strategies
- Use database transactions for data consistency
- Implement database connection pooling
- Regular database maintenance and optimization""",

        "Security Specialist": """
### 🔒 Security Guidelines
- Implement input validation and sanitization
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Regular security audits and penetration testing
- Keep dependencies updated and monitor vulnerabilities""",

        "AI Engineer": """
### 🤖 AI/ML Guidelines
- Implement proper data preprocessing pipelines
- Use version control for ML models
- Implement model validation and testing
- Monitor model performance and drift
- Document model decisions and limitations""",

        "Project Manager": """
### 📊 Project Management Guidelines
- Maintain clear project documentation
- Regular progress updates and status reports
- Risk assessment and mitigation planning
- Stakeholder communication and management
- Quality assurance and testing coordination"""
    }

    for team in teams:
        if team in team_guidelines:
            prompt_content += team_guidelines[team] + "\n\n"

    prompt_content += """## 🚀 Deployment & Production

### Environment Setup
```bash
# Production environment variables
NODE_ENV=production
DATABASE_URL=production_database_url
REDIS_URL=production_redis_url
JWT_SECRET=secure_random_secret
```

### Monitoring & Logging
```javascript
// Application monitoring
- Implement health check endpoints
- Set up error tracking (Sentry, Bugsnag)
- Configure application metrics (Prometheus, Grafana)
- Set up log aggregation (ELK stack)
```

### Performance Optimization
```javascript
// Production optimizations
- Enable gzip compression
- Implement CDN for static assets
- Configure database connection pooling
- Set up horizontal scaling if needed
```

## 📝 Code Documentation Standards

### JSDoc Comments
```javascript
/**
 * User authentication function
 * @param {string} username - User's username
 * @param {string} password - User's password
 * @returns {Promise<Object>} Authentication result
 */
async function authenticateUser(username, password) {
  // Implementation
}
```

### README Files
```markdown
# Project Name

## Setup Instructions
## API Documentation
## Development Guidelines
## Deployment Instructions
```

## 🎯 Success Metrics

- **Code Quality**: Maintain high test coverage (>80%)
- **Performance**: Response times <200ms for API calls
- **Security**: Zero critical vulnerabilities
- **User Experience**: High user satisfaction scores
- **Maintainability**: Clean, well-documented code

---

*This prompt file was generated by AI Discussion Manager to guide Cursor IDE development*
"""

    return prompt_content

def generate_manager_summary(messages, project_title, teams):
    """Generate a comprehensive project manager summary"""
    summary_content = f"""# 📊 Project Manager Summary: {project_title}

## 📅 Executive Summary

**Project:** {project_title}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status:** Analysis Complete
**Team Size:** {len(teams)} specialists

---

## 🎯 Project Objectives & Scope

"""

    # Extract project objectives from initial message
    if messages and messages[0]['role'] == 'user':
        summary_content += f"{messages[0]['content']}\n\n"

    summary_content += "## 👥 Team Contributions Overview\n\n"

    # Analyze team contributions
    team_stats = {}
    for msg in messages[1:]:
        if msg.get('model'):
            team = msg['model']
            if team not in team_stats:
                team_stats[team] = {'count': 0, 'total_chars': 0}
            team_stats[team]['count'] += 1
            team_stats[team]['total_chars'] += len(msg['content'])

    for team, stats in team_stats.items():
        summary_content += f"### {team}\n"
        summary_content += f"- **Contributions:** {stats['count']} responses\n"
        summary_content += f"- **Content Volume:** {stats['total_chars']} characters\n\n"

    summary_content += """## 🔍 Key Findings & Recommendations

### ✅ Strengths Identified
- Comprehensive technical analysis across all domains
- Collaborative approach with diverse expertise
- Detailed implementation recommendations
- Security and performance considerations addressed

### ⚠️ Potential Challenges
- Integration complexity between different components
- Timeline management for comprehensive implementation
- Resource allocation across multiple specialties
- Technology stack compatibility and learning curves

### 🎯 Critical Success Factors
1. **Clear Communication**: Regular team standups and progress updates
2. **Modular Architecture**: Well-defined interfaces between components
3. **Quality Assurance**: Comprehensive testing strategy
4. **Documentation**: Maintain up-to-date technical documentation

## 📋 Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [ ] Requirements finalization and approval
- [ ] Technology stack confirmation
- [ ] Development environment setup
- [ ] Initial project structure creation

### Phase 2: Core Development (Weeks 3-6)
- [ ] Database design and implementation
- [ ] Backend API development
- [ ] Frontend component development
- [ ] Integration testing

### Phase 3: Enhancement & Testing (Weeks 7-8)
- [ ] Security implementation and testing
- [ ] Performance optimization
- [ ] User acceptance testing
- [ ] Documentation completion

### Phase 4: Deployment & Launch (Week 9)
- [ ] Production environment setup
- [ ] Data migration and testing
- [ ] User training and documentation
- [ ] Go-live and monitoring

## 💰 Resource Requirements

### Team Composition
"""

    for team in teams:
        summary_content += f"- [ ] {team}\n"

    summary_content += """

### Infrastructure Needs
- [ ] Development servers and environments
- [ ] Database servers (development, staging, production)
- [ ] CI/CD pipeline and tools
- [ ] Monitoring and logging infrastructure
- [ ] Security scanning tools

## 📊 Risk Assessment

### High Risk Items
- **Technology Integration**: Complex integration between multiple technologies
- **Timeline Pressure**: Aggressive development timeline
- **Resource Availability**: Specialist availability and expertise

### Mitigation Strategies
- **Prototype Early**: Create proof-of-concept for critical integrations
- **Agile Methodology**: Regular iterations with stakeholder feedback
- **Knowledge Transfer**: Document critical processes and decisions
- **Contingency Planning**: Identify backup approaches for high-risk items

## 🎯 Success Metrics

### Technical Metrics
- [ ] Code coverage > 80%
- [ ] Performance benchmarks met (response time < 200ms)
- [ ] Security scan results - zero critical vulnerabilities
- [ ] System uptime > 99.9%

### Business Metrics
- [ ] User adoption rate within first month
- [ ] Stakeholder satisfaction survey results
- [ ] Feature utilization analytics
- [ ] Return on investment projections

## 📞 Next Steps & Action Items

### Immediate Actions (Next 24-48 hours)
1. Schedule project kickoff meeting with all stakeholders
2. Confirm team availability and resource allocation
3. Set up development environments and access
4. Create initial project timeline and milestones

### Short-term Goals (Next 1-2 weeks)
1. Finalize detailed technical specifications
2. Complete technology stack evaluation
3. Establish coding standards and guidelines
4. Set up project management tools and processes

### Communication Plan
- **Daily Standups**: Technical team coordination
- **Weekly Updates**: Stakeholder progress reports
- **Monthly Reviews**: Executive summary and adjustments
- **Ad-hoc**: Critical issues and blocker resolution

---

## 📞 Contact & Support

**Project Manager:** AI Discussion Manager System
**Technical Lead:** Development Team
**Stakeholder Contact:** Project Sponsors

*This summary was generated by AI Discussion Manager for comprehensive project oversight and coordination.*
"""

    return summary_content

def generate_all_files(messages, project_title, teams):
    """Generate all documentation files and save to database"""
    if not st.session_state.conversation_id:
        return False, "No active conversation to generate files for"

    files_generated = []

    try:
        # Generate MD project specification file
        md_content = generate_project_md_file(messages, project_title, teams)
        md_filename = f"{project_title.replace(' ', '_')}_Specification.md"
        if save_generated_file_to_db(st.session_state.conversation_id, 'markdown', md_filename, md_content):
            files_generated.append(('markdown', md_filename, md_content))

        # Generate Cursor IDE prompt file
        cursor_content = generate_cursor_prompt_file(messages, project_title, teams)
        cursor_filename = f"{project_title.replace(' ', '_')}_Cursor_Prompts.md"
        if save_generated_file_to_db(st.session_state.conversation_id, 'cursor_guide', cursor_filename, cursor_content):
            files_generated.append(('cursor_guide', cursor_filename, cursor_content))

        # Generate Manager Summary
        manager_content = generate_manager_summary(messages, project_title, teams)
        manager_filename = f"{project_title.replace(' ', '_')}_Manager_Summary.md"
        if save_generated_file_to_db(st.session_state.conversation_id, 'markdown', manager_filename, manager_content):
            files_generated.append(('markdown', manager_filename, manager_content))

        # Update session state with generated files
        st.session_state.generated_files = files_generated

        return True, f"✅ Successfully generated {len(files_generated)} documentation files!"

    except Exception as e:
        return False, f"❌ Error generating files: {str(e)}"

# Modern Main UI
def render_main_header():
    """Render the main header with modern styling"""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 AI Code Analyst Pro</h1>
        <p>Advanced AI-powered code analysis, project insights, and intelligent recommendations</p>
    </div>
    """, unsafe_allow_html=True)

def render_api_verification_section():
    """Render API verification section"""
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 🔑 API Configuration & Verification")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🤖 OpenAI API")
        openai_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Enter your OpenAI API key to enable AI analysis"
        )

        if openai_key:
            if st.button("🔍 Verify OpenAI API", key="verify_openai"):
                with st.spinner("Verifying OpenAI API..."):
                    verified, message = verify_openai_api_key(openai_key)
                    if verified:
                        st.success(message)
                        st.session_state.openai_client = openai.OpenAI(api_key=openai_key)
                        st.session_state.openai_verified = True
                    else:
                        st.error(message)

        if st.session_state.get('openai_verified', False):
            st.markdown('<span class="status-success">✅ OpenAI API Connected</span>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### 🗄️ Supabase Database")
        supabase_url = st.text_input(
            "Supabase URL",
            placeholder="https://your-project-id.supabase.co",
            help="Enter your Supabase project URL"
        )
        supabase_key = st.text_input(
            "Supabase Key",
            type="password",
            placeholder="your-supabase-anon-key",
            help="Enter your Supabase anon key"
        )

        if supabase_url and supabase_key:
            if st.button("🔍 Verify Supabase", key="verify_supabase"):
                with st.spinner("Verifying Supabase connection..."):
                    verified, message = verify_supabase_credentials(supabase_url, supabase_key)
                    if verified:
                        st.success(message)
                        st.session_state.supabase_client = create_client(supabase_url, supabase_key)
                        st.session_state.supabase_verified = True
                    else:
                        st.error(message)

        if st.session_state.get('supabase_verified', False):
            st.markdown('<span class="status-success">✅ Supabase Connected</span>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def render_navigation():
    """Render modern navigation"""
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 🧭 Navigation")

    col1, col2, col3, col4 = st.columns(4)

    pages = [
        ("🏠 Dashboard", "dashboard", col1),
        ("📁 File Analysis", "analysis", col2),
        ("📊 Project Insights", "insights", col3),
        ("⚙️ Settings", "settings", col4)
    ]

    for label, page, col in pages:
        with col:
            # Use unique keys and handle navigation
            button_key = f"nav_{page}_{hash(label)}"
            is_current_page = st.session_state.current_page == page

            if st.button(label, key=button_key, type="primary" if is_current_page else "secondary"):
                st.session_state.current_page = page
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_file_upload_section():
    """Render enhanced file upload section"""
    st.markdown('<div class="modern-card">', unsafe_allow_html=True)
    st.markdown("### 📁 File & Folder Analysis")

    tab1, tab2, tab3 = st.tabs(["📄 Single Files", "📂 Folder Upload", "🔗 URL Import"])

    with tab1:
        uploaded_files = st.file_uploader(
            "Upload code files for analysis",
            accept_multiple_files=True,
            type=['py', 'js', 'ts', 'java', 'cpp', 'c', 'cs', 'php', 'rb', 'go', 'html', 'css', 'md', 'txt']
        )

        if uploaded_files and st.button("🔍 Analyze Files", key="analyze_files"):
            with st.spinner("Analyzing files..."):
                analyze_uploaded_files(uploaded_files)

    with tab2:
        st.markdown('<div class="upload-zone">', unsafe_allow_html=True)
        st.markdown("### 📂 Drag & Drop Folder")
        st.markdown("Support for ZIP files containing project folders")
        uploaded_zip = st.file_uploader("Upload ZIP file", type=['zip'])

        if uploaded_zip and st.button("📦 Extract & Analyze", key="analyze_zip"):
            with st.spinner("Extracting and analyzing folder..."):
                analyze_zip_folder(uploaded_zip)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/user/repo")
        if repo_url and st.button("📥 Clone & Analyze", key="analyze_repo"):
            with st.spinner("Cloning and analyzing repository..."):
                analyze_github_repo(repo_url)

    st.markdown('</div>', unsafe_allow_html=True)

def analyze_zip_folder(zip_file):
    """Analyze ZIP folder structure"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Analyze the extracted folder
            structure = analyze_folder_structure(temp_dir)

            st.success("✅ Folder extracted and analyzed!")
            display_folder_analysis(structure)

    except Exception as e:
        st.error(f"❌ Error analyzing ZIP folder: {str(e)}")

def analyze_github_repo(repo_url):
    """Analyze GitHub repository"""
    st.info("🚧 GitHub repository analysis coming soon!")
    # TODO: Implement GitHub API integration for repository analysis

def display_folder_analysis(structure):
    """Display folder structure analysis"""
    st.markdown("### 📂 Folder Analysis Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>📁 Total Files</h4>
            <div class="metric">{structure['total_files']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>🗂️ Folders</h4>
            <div class="metric">{len(structure['folders'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>🗣️ Languages</h4>
            <div class="metric">{len(structure['languages'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>📋 Types</h4>
            <div class="metric">{len(structure['file_types'])}</div>
        </div>
        """, unsafe_allow_html=True)

    # Language breakdown
    if structure['languages']:
        st.markdown("#### 🗣️ Language Distribution")
        lang_data = {k: v for k, v in structure['languages'].items() if k != 'unknown'}
        if lang_data:
            st.bar_chart(lang_data)

    # Largest files
    if structure['largest_files']:
        st.markdown("#### 📊 Largest Files")
        for file_name, size in structure['largest_files'][:5]:
            st.write(f"📄 {file_name}: {size:,} bytes")

    # Project type detection
    if structure['project_type'] != 'unknown':
        st.success(f"🎯 Detected project type: **{structure['project_type'].title()}**")

def analyze_uploaded_files(files):
    """Analyze uploaded files"""
    results = {}
    progress_bar = st.progress(0)

    for i, file in enumerate(files):
        file_content = file.read().decode('utf-8')
        file_path = file.name

        # Analyze the file
        analysis = analyze_code_file(file_path, file_content)
        results[file_path] = analysis

        # Update progress
        progress_bar.progress((i + 1) / len(files))

    st.session_state.analysis_results = results
    display_analysis_results(results)

def display_analysis_results(results):
    """Display analysis results in modern cards"""
    if not results:
        return

    st.markdown("### 📊 Analysis Results")

    # Summary metrics
    total_files = len(results)
    languages = {}
    total_lines = 0

    for file_path, analysis in results.items():
        lang = analysis['language']
        languages[lang] = languages.get(lang, 0) + 1
        total_lines += analysis['lines']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>📄 Files</h4>
            <div class="metric">{total_files}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>📝 Lines</h4>
            <div class="metric">{total_lines:,}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>🗣️ Languages</h4>
            <div class="metric">{len(languages)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="analysis-card">
            <h4>🔧 Functions</h4>
            <div class="metric">{sum(len(a.get('functions', [])) for a in results.values())}</div>
        </div>
        """, unsafe_allow_html=True)

    # Detailed file analysis
    for file_path, analysis in results.items():
        with st.expander(f"📄 {file_path}", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Language", analysis['language'].title())
                st.metric("Lines", analysis['lines'])
                st.metric("Complexity", analysis['complexity'].title())

            with col2:
                st.metric("Functions", len(analysis.get('functions', [])))
                st.metric("Classes", len(analysis.get('classes', [])))
                st.metric("Imports", len(analysis.get('imports', [])))

            with col3:
                st.metric("Characters", f"{analysis['characters']:,}")

            # Suggestions
            if analysis.get('suggestions'):
                st.markdown("#### 💡 Suggestions")
                for suggestion in analysis['suggestions']:
                    st.info(f"• {suggestion}")

# Main Application Flow
def main():
    """Main application function"""
    render_main_header()

    # Check if APIs are verified
    apis_ready = st.session_state.get('openai_verified', False) and st.session_state.get('supabase_verified', False)

    if not apis_ready:
        render_api_verification_section()
        st.warning("⚠️ Please verify your API credentials above to unlock all features")
        return

    # Main navigation and content
    render_navigation()

    current_page = st.session_state.current_page

    if current_page == "dashboard":
        render_dashboard()
    elif current_page == "analysis":
        render_analysis_page()
    elif current_page == "insights":
        render_insights_page()
    elif current_page == "settings":
        render_settings_page()

def render_dashboard():
    """Render dashboard page"""
    st.markdown("### 📈 Dashboard Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Analysis Summary")
        if st.session_state.analysis_results:
            st.metric("Files Analyzed", len(st.session_state.analysis_results))
        else:
            st.info("No files analyzed yet")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("#### 🤖 AI Status")
        st.success("✅ OpenAI Connected")
        st.success("✅ Supabase Connected")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="modern-card">', unsafe_allow_html=True)
        st.markdown("#### 📁 Recent Activity")
        st.info("Upload files to get started")
        st.markdown('</div>', unsafe_allow_html=True)

    render_file_upload_section()

def render_analysis_page():
    """Render analysis page"""
    st.markdown("### 🔍 Code Analysis")

    if not st.session_state.analysis_results:
        st.info("📄 Upload files to see analysis results")
        render_file_upload_section()
    else:
        display_analysis_results(st.session_state.analysis_results)

def render_insights_page():
    """Render insights page"""
    st.markdown("### 📊 Project Insights")
    st.info("🚧 Insights feature coming soon!")

def render_settings_page():
    """Render settings page"""
    st.markdown("### ⚙️ Settings")

    # Theme selection
    st.markdown("#### 🎨 Theme")
    theme_options = ["light", "dark", "modern"]
    selected_theme = st.selectbox("Choose theme", theme_options, index=theme_options.index(st.session_state.theme))
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.success(f"✅ Theme changed to {selected_theme}")

    # API settings
    st.markdown("#### 🔑 API Settings")
    if st.button("🔄 Re-verify APIs", key="reverify"):
        st.session_state.openai_verified = False
        st.session_state.supabase_verified = False
        st.success("API verification reset. Please re-verify your credentials.")

# Run the main application
if __name__ == "__main__":
    main()

# Sidebar configuration
with st.sidebar:
    st.header("🔧 Configuration")

    # OpenAI Initialization
    if st.button("🔗 Initialize OpenAI"):
        with st.spinner("Connecting to OpenAI..."):
            success, msg = initialize_openai()
            if success:
                st.success(msg)
            else:
                st.error(msg)

    if st.session_state.openai_client:
        st.success("✅ OpenAI Connected")
    else:
        st.warning("⚠️ Not connected")

    st.divider()

    # Teams
    st.subheader("👨‍💻 Select Teams (max 7)")
    available_teams = ["Frontend Dev", "Backend Dev", "Database Expert", "Security Specialist", "AI Engineer", "Project Manager", "DevOps Engineer"]
    selected = st.multiselect("Choose teams:", available_teams, max_selections=7)

    if selected:
        st.session_state.teams = selected

    st.divider()

    # Conversation History
    st.subheader("📚 History")
    if st.button("🔄 Load History"):
        with st.spinner("Loading conversation history..."):
            history = load_conversation_history()
            if history:
                st.session_state.conversation_history = history
                st.success(f"✅ Loaded {len(history)} conversations")
            else:
                st.info("No conversation history found")

    # Display conversation history
    if 'conversation_history' in st.session_state and st.session_state.conversation_history:
        st.markdown("**Recent Conversations:**")
        for conv in st.session_state.conversation_history[-5:]:  # Show last 5
            title = conv.get('project_title', f"Conversation {conv.get('id', 'Unknown')}")
            created_date = conv.get('created_at', 'Unknown').strftime('%Y-%m-%d %H:%M') if conv.get('created_at') else 'Unknown'

            if st.button(f"📄 {title[:30]}... ({created_date})", key=f"hist_{conv.get('id')}_{hash(title)}"):
                # Load this conversation
                full_conv = load_conversation_from_db(conv.get('session_id'))
                if full_conv:
                    st.session_state.messages = [
                        {'role': msg['role'], 'content': msg['content'], 'model': msg.get('model')}
                        for msg in full_conv['messages']
                    ]
                    st.session_state.generated_files = [
                        (file['file_type'], file['file_name'], file['file_content'])
                        for file in full_conv['files']
                    ]
                    st.session_state.conversation_id = conv.get('id')
                    st.success(f"✅ Loaded conversation: {title}")
                    st.rerun()
                else:
                    st.error("Failed to load conversation details")

    st.divider()

    # Discussion Settings
    st.subheader("Discussion Settings")
    max_rounds = st.slider("Max Discussion Rounds", 1, 10, 5)
    discussion_style = st.selectbox(
        "Discussion Style",
        ["Collaborative", "Debate", "Technical Review", "Creative Brainstorm"]
    )

    # Clear chat
    if st.button("🗑️ Clear Discussion"):
        st.session_state.messages = []
        st.session_state.discussion_active = False
        st.session_state.uploaded_file_content = ""
        st.session_state.uploaded_file_name = ""
        st.session_state.conversation_id = None
        st.session_state.generated_files = []
        st.rerun()

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 AI Discussion")

    if not st.session_state.discussion_active:
        st.subheader("Project Definition")

        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["📝 Manual Input", "📁 Upload File"],
            horizontal=True
        )

        project_content = ""
        project_title = ""

        if input_method == "📝 Manual Input":
            # Manual text input with word limits
            col1, col2 = st.columns([2, 1])

            with col1:
                topic = st.text_area("Describe your project:", height=100, max_chars=1500, help="Maximum 150 words (approximately 1500 characters)")

            with col2:
                topic_word_count = len(topic.split()) if topic else 0
                st.metric("Topic Words", f"{topic_word_count}/150")
                if topic_word_count > 150:
                    st.error("⚠️ Topic exceeds 150 word limit!")

            goals = st.text_area("Goals & Features:", height=100, max_chars=1500, help="Maximum 150 words (approximately 1500 characters)")
            goals_word_count = len(goals.split()) if goals else 0

            col3, col4 = st.columns([2, 1])
            with col4:
                st.metric("Goals Words", f"{goals_word_count}/150")
                if goals_word_count > 150:
                    st.error("⚠️ Goals exceed 150 word limit!")

            # Validate word limits
            word_limit_valid = topic_word_count <= 150 and goals_word_count <= 150

            if topic and goals and word_limit_valid:
                project_content = f"Topic: {topic}\n\nGoals: {goals}"
                project_title = "Manual Project Description"
            elif not word_limit_valid:
                st.error("❌ Please reduce content to stay within 150 word limits.")

        else:  # File Upload
            st.markdown("**Upload your project documentation (.md or .txt):**")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["md", "txt"],
                help="Upload markdown (.md) or text (.txt) files containing project specifications"
            )

            if uploaded_file:
                if st.button("📖 Process File"):
                    success, message = process_uploaded_file(uploaded_file)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            # Display uploaded file content if available
            if st.session_state.uploaded_file_content:
                st.success(f"📄 **{st.session_state.uploaded_file_name}** loaded successfully!")
                with st.expander("📋 Preview File Content", expanded=False):
                    st.code(st.session_state.uploaded_file_content[:1000] + ("..." if len(st.session_state.uploaded_file_content) > 1000 else ""), language="markdown")

                project_content = f"File: {st.session_state.uploaded_file_name}\n\nContent:\n{st.session_state.uploaded_file_content}"
                project_title = f"Analysis of {st.session_state.uploaded_file_name}"

        # Start discussion button
        if st.button("🚀 Start Discussion", type="primary"):
            # Validate all requirements
            has_content = bool(project_content.strip()) if project_content else False
            has_openai = bool(st.session_state.openai_client)
            has_teams = bool(st.session_state.teams)

            # Additional validation for manual input
            word_limit_ok = True
            if input_method == "📝 Manual Input":
                topic_words = len((topic or "").split())
                goals_words = len((goals or "").split())
                word_limit_ok = topic_words <= 150 and goals_words <= 150

            if has_content and has_openai and has_teams and word_limit_ok:
                st.session_state.discussion_active = True

                # Save conversation to database
                final_project_title = project_title if input_method == "📝 Manual Input" else st.session_state.uploaded_file_name.replace('.md', '').replace('.txt', '').replace('_', ' ')
                conversation_id = save_conversation_to_db(
                    st.session_state.session_id,
                    final_project_title,
                    st.session_state.teams,
                    st.session_state.uploaded_file_name if input_method == "📁 Upload File" else None,
                    st.session_state.uploaded_file_content if input_method == "📁 Upload File" else None
                )

                if conversation_id:
                    st.session_state.conversation_id = conversation_id
                    add_message("user", project_content)

                    # Save initial message to database
                    save_message_to_db(conversation_id, "user", project_content)
                else:
                    st.error("Failed to save conversation to database")

                st.rerun()
            else:
                error_msg = "Please fix the following issues:\n"
                if not has_content:
                    error_msg += "• Enter project details or upload a file\n"
                if not has_openai:
                    error_msg += "• Initialize OpenAI connection\n"
                if not has_teams:
                    error_msg += "• Select at least one team\n"
                if input_method == "📝 Manual Input" and not word_limit_ok:
                    error_msg += "• Keep content within 150 word limits\n"
                st.error(error_msg)

    # Show messages
    display_conversation()

    # Auto discussion
    if st.session_state.discussion_active and st.session_state.teams:
        ai_count = len([m for m in st.session_state.messages if m["model"]])
        if ai_count < max_rounds * len(st.session_state.teams):
            last_model = st.session_state.messages[-1].get("model", "")
            team_index = ai_count % len(st.session_state.teams)
            next_team = st.session_state.teams[team_index]

            # Build context
            context = [{"role": "user", "content": st.session_state.messages[0]["content"]}]
            for msg in st.session_state.messages[1:]:
                if msg["model"]:
                    context.append({"role": "assistant", "content": msg["content"]})

            # Determine if this is file-based content
            is_file_content = bool(st.session_state.uploaded_file_content)

            # Base system prompt for the team
            team_base_prompts = {
                "Frontend Dev": f"""You are {next_team}, a frontend development expert specializing in modern web technologies.

{f'Analyze the uploaded documentation and provide frontend-specific insights. Consider UI/UX best practices, responsive design, performance optimization, and integration with backend APIs.' if is_file_content else 'Provide frontend development expertise for the described project.'}

Focus on user experience, accessibility, and modern frontend frameworks like React, Vue, or Angular.""",

                "Backend Dev": f"""You are {next_team}, a backend development expert specializing in server-side technologies.

{f'Analyze the uploaded documentation and provide backend architecture insights. Consider API design, database integration, security, scalability, and microservices architecture.' if is_file_content else 'Provide backend development expertise for the described project.'}

Focus on robust, scalable, and maintainable server-side solutions.""",

                "Database Expert": f"""You are {next_team}, a database and data architecture specialist.

{f'Analyze the uploaded documentation and provide database design insights. Consider data modeling, performance optimization, security, and scalability requirements.' if is_file_content else 'Provide database design expertise for the described project.'}

Focus on efficient data storage, retrieval, and management solutions.""",

                "Security Specialist": f"""You are {next_team}, a cybersecurity and application security expert.

{f'Analyze the uploaded documentation and identify security vulnerabilities, risks, and compliance requirements. Provide security best practices and implementation recommendations.' if is_file_content else 'Provide security expertise for the described project.'}

Focus on secure coding practices, authentication, authorization, and data protection.""",

                "AI Engineer": f"""You are {next_team}, an AI/ML engineering specialist.

{f'Analyze the uploaded documentation and identify opportunities for AI/ML integration. Consider machine learning models, data processing pipelines, and AI-powered features.' if is_file_content else 'Provide AI/ML engineering expertise for the described project.'}

Focus on intelligent features, automation, and data-driven solutions.""",

                "Project Manager": f"""You are {next_team}, a project management and coordination specialist overseeing the entire development process.

{f'Analyze the uploaded documentation and provide project management insights. Coordinate between different teams, manage timelines, identify dependencies, and ensure project success.' if is_file_content else 'Provide project management expertise for the described project.'}

Focus on project planning, team coordination, risk management, and delivery milestones.""",

                "DevOps Engineer": f"""You are {next_team}, a DevOps and infrastructure specialist focusing on deployment, automation, and system reliability.

{f'Analyze the uploaded documentation and provide DevOps insights. Consider CI/CD pipelines, containerization, monitoring, scalability, and infrastructure automation.' if is_file_content else 'Provide DevOps engineering expertise for the described project.'}

Focus on deployment automation, infrastructure as code, monitoring, and operational excellence."""
            }

            # Get the base team prompt
            system_prompt = team_base_prompts.get(next_team, f"You are {next_team}, an expert in your field. Provide valuable insights for this project.")

            # Add discussion style context
            if discussion_style == "Collaborative":
                system_prompt += "\n\nApproach this collaboratively, building on previous suggestions and finding common ground between different perspectives."
            elif discussion_style == "Debate":
                system_prompt += "\n\nApproach this as a constructive debate, presenting well-reasoned arguments and considering alternative viewpoints."
            elif discussion_style == "Technical Review":
                system_prompt += "\n\nConduct a thorough technical review, focusing on best practices, potential issues, and optimization opportunities."
            elif discussion_style == "Creative Brainstorm":
                system_prompt += "\n\nBrainstorm creative and innovative solutions, thinking outside the box while maintaining technical feasibility."

            with st.spinner(f"🟢 {next_team} is thinking..."):
                response = call_openai(context, system_prompt)
                add_message("assistant", response, next_team)

                # Save AI response to database
                if st.session_state.conversation_id:
                    save_message_to_db(st.session_state.conversation_id, "assistant", response, next_team)

                time.sleep(1)
                st.rerun()
        else:
            st.success("🎉 Discussion completed!")

            # Generate Documentation Files
            st.subheader("📄 Generate Documentation")

            col_gen1, col_gen2 = st.columns([1, 1])
            with col_gen1:
                if st.button("📝 Generate All Files", type="primary"):
                    project_title = st.session_state.messages[0]['content'].split('\n')[0] if st.session_state.messages else "AI_Project"
                    success, message = generate_all_files(st.session_state.messages, project_title, st.session_state.teams)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                    st.rerun()

            with col_gen2:
                if st.button("📊 Generate Manager Summary Only"):
                    project_title = st.session_state.messages[0]['content'].split('\n')[0] if st.session_state.messages else "AI_Project"
                    if st.session_state.conversation_id:
                        manager_content = generate_manager_summary(st.session_state.messages, project_title, st.session_state.teams)
                        manager_filename = f"{project_title.replace(' ', '_')}_Manager_Summary.md"
                        if save_generated_file_to_db(st.session_state.conversation_id, 'markdown', manager_filename, manager_content):
                            st.success("✅ Manager Summary generated successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to generate Manager Summary")
                    else:
                        st.error("No active conversation found")

            st.session_state.discussion_active = False

with col2:
    st.header("📊 Stats")

    if st.session_state.messages:
        counts = {team: len([m for m in st.session_state.messages if m["model"] == team]) for team in st.session_state.teams}
        total = sum(counts.values())

        for team, c in counts.items():
            st.metric(f"{team} Responses", c)
        st.metric("Total Exchanges", total)

        progress = min(total / (max_rounds * len(st.session_state.teams)), 1.0)
        st.progress(progress, text=f"{total}/{max_rounds * len(st.session_state.teams)}")

        # Generated Files Section
        if st.session_state.generated_files:
            st.subheader("📁 Generated Files")

            # File statistics
            file_types = {}
            for file_type, file_name, file_content in st.session_state.generated_files:
                if file_type not in file_types:
                    file_types[file_type] = []
                file_types[file_type].append((file_name, file_content))

            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.metric("Total Files", len(st.session_state.generated_files))
            with col_stats2:
                st.metric("File Types", len(file_types))

            # File type filter
            file_type_filter = st.selectbox(
                "Filter by type:",
                ["All"] + list(file_types.keys()),
                key="file_filter"
            )

            # Display files
            files_to_show = st.session_state.generated_files
            if file_type_filter != "All":
                files_to_show = [(ft, fn, fc) for ft, fn, fc in st.session_state.generated_files if ft == file_type_filter]

            for file_type, file_name, file_content in files_to_show:
                file_icon = {
                    'markdown': '📄',
                    'cursor_guide': '🎯',
                    'prompt': '💬'
                }.get(file_type, '📄')

                with st.expander(f"{file_icon} {file_name}", expanded=False):
                    # File info
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Type", file_type.replace('_', ' ').title())
                    with col_info2:
                        st.metric("Size", f"{len(file_content)} chars")
                    with col_info3:
                        st.metric("Lines", file_content.count('\n') + 1)

                    # Content preview
                    st.markdown("**Preview:**")
                    preview_length = min(2000, len(file_content))
                    st.code(file_content[:preview_length] + ("..." if len(file_content) > preview_length else ""),
                           language="markdown")

                    # Action buttons
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        st.download_button(
                            label="📥 Download",
                            data=file_content,
                            file_name=file_name,
                            mime="text/markdown",
                            key=f"download_{file_name}_{hash(file_content)}"
                        )
                    with col_btn2:
                        if st.button("👁️ Full View", key=f"fullview_{file_name}_{hash(file_content[:100])}"):
                            st.text_area("Full Content:", file_content, height=400, key=f"textarea_{file_name}_{hash(file_content[:100])}")
                    with col_btn3:
                        if st.button("📋 Copy", key=f"copy_{file_name}_{hash(file_content[:100])}"):
                            st.code(file_content, language="markdown")
                            st.success("Content copied to clipboard area above!")

            # Bulk download option
            if len(files_to_show) > 1:
                st.markdown("---")
                if st.button("📦 Download All Files (ZIP)", key="bulk_download"):
                    # This would require additional zip functionality
                    st.info("Bulk download feature coming soon! Please download files individually for now.")

    else:
        st.info("No discussion started yet")

    # Database Connection Status
    st.subheader("🗄️ Database Status")
    if st.session_state.db_initialized:
        st.success("✅ Database connected and initialized")
    else:
        st.error("❌ Database connection failed")

    # Session Information
    with st.expander("ℹ️ Session Info", expanded=False):
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.write(f"**Session ID:** {st.session_state.session_id[:8]}...")
            st.write(f"**Conversation ID:** {st.session_state.conversation_id or 'None'}")
            st.write(f"**Database Status:** {'✅ Connected' if st.session_state.db_initialized else '❌ Disconnected'}")

        with col_info2:
            st.write(f"**Messages:** {len(st.session_state.messages)}")
            st.write(f"**Generated Files:** {len(st.session_state.generated_files) if st.session_state.generated_files else 0}")
            if st.session_state.teams:
                st.write(f"**Active Teams:** {len(st.session_state.teams)}")

        # Show uploaded file info if available
        if st.session_state.uploaded_file_name:
            st.markdown("**Uploaded File:**")
            st.info(f"📄 {st.session_state.uploaded_file_name}")
            if st.button("👁️ Review Uploaded File", key="review_uploaded"):
                with st.expander("📋 Uploaded File Content", expanded=True):
                    if st.session_state.uploaded_file_content:
                        st.code(st.session_state.uploaded_file_content[:2000] +
                               ("..." if len(st.session_state.uploaded_file_content) > 2000 else ""),
                               language="markdown")
                    else:
                        st.warning("No file content available")

    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col_action1, col_action2, col_action3 = st.columns(3)

    with col_action1:
        if st.button("🆕 New Discussion", key="new_discussion"):
            # Clear current session but keep history
            st.session_state.messages = []
            st.session_state.discussion_active = False
            st.session_state.uploaded_file_content = ""
            st.session_state.uploaded_file_name = ""
            st.session_state.conversation_id = None
            st.session_state.generated_files = []
            import uuid
            st.session_state.session_id = str(uuid.uuid4())
            st.success("✅ Started new discussion session!")
            st.rerun()

    with col_action2:
        if st.button("💾 Save Current State", key="save_state"):
            if st.session_state.conversation_id and st.session_state.messages:
                st.success("✅ Current conversation is automatically saved to database!")
            else:
                st.info("No active conversation to save")

    with col_action3:
        if st.button("📊 Export Summary", key="export_summary"):
            if st.session_state.messages:
                summary = f"""# Discussion Summary

**Session:** {st.session_state.session_id[:8]}...
**Messages:** {len(st.session_state.messages)}
**Teams:** {', '.join(st.session_state.teams) if st.session_state.teams else 'None'}
**Files Generated:** {len(st.session_state.generated_files) if st.session_state.generated_files else 0}

## Messages:
"""
                for i, msg in enumerate(st.session_state.messages, 1):
                    summary += f"\n### Message {i}\n**{msg['role'].title()}:** {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"

                st.download_button(
                    label="📥 Download Summary",
                    data=summary,
                    file_name=f"discussion_summary_{st.session_state.session_id[:8]}.md",
                    mime="text/markdown",
                    key="download_summary"
                )
            else:
                st.info("No discussion data to export")
