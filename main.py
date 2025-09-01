import streamlit as st
import openai
import time
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'ai_discussion_manager')
}

def get_db_connection():
    """Create and return database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Database connection failed: {e}")
        return None

def create_database_schema():
    """Create database tables if they don't exist"""
    connection = None
    try:
        # Connect without database first
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database', None)
        connection = mysql.connector.connect(**temp_config)
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Create conversations table
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

        # Create messages table
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

        # Create generated_files table
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

        connection.commit()
        return True

    except Error as e:
        st.error(f"Database schema creation failed: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def save_conversation_to_db(session_id, project_title, teams, uploaded_file_name=None, uploaded_file_content=None):
    """Save conversation metadata to database"""
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO conversations (session_id, project_title, teams, uploaded_file_name, uploaded_file_content)
            VALUES (%s, %s, %s, %s, %s)
        """, (session_id, project_title, json.dumps(teams) if teams else None, uploaded_file_name, uploaded_file_content))
        conversation_id = cursor.lastrowid
        connection.commit()
        return conversation_id
    except Error as e:
        st.error(f"Failed to save conversation: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_message_to_db(conversation_id, role, content, model=None):
    """Save individual message to database"""
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content, model)
            VALUES (%s, %s, %s, %s)
        """, (conversation_id, role, content, model))
        connection.commit()
        return True
    except Error as e:
        st.error(f"Failed to save message: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_generated_file_to_db(conversation_id, file_type, file_name, file_content):
    """Save generated file to database"""
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO generated_files (conversation_id, file_type, file_name, file_content)
            VALUES (%s, %s, %s, %s)
        """, (conversation_id, file_type, file_name, file_content))
        connection.commit()
        return True
    except Error as e:
        st.error(f"Failed to save generated file: {e}")
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_conversation_history():
    """Load conversation history list from database"""
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)

        # Get all conversations ordered by creation date
        cursor.execute("""
            SELECT id, session_id, project_title, created_at, status, teams
            FROM conversations
            ORDER BY created_at DESC
        """)

        conversations = cursor.fetchall()

        # Convert teams JSON string back to list
        for conv in conversations:
            if conv.get('teams'):
                try:
                    conv['teams'] = json.loads(conv['teams'])
                except:
                    conv['teams'] = []

        return conversations

    except Error as e:
        st.error(f"Failed to load conversation history: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_conversation_from_db(session_id):
    """Load conversation data from database"""
    connection = get_db_connection()
    if not connection:
        return None

    try:
        cursor = connection.cursor(dictionary=True)

        # Get conversation
        cursor.execute("SELECT * FROM conversations WHERE session_id = %s", (session_id,))
        conversation = cursor.fetchone()

        if not conversation:
            return None

        # Get messages
        cursor.execute("""
            SELECT role, content, model, timestamp
            FROM messages
            WHERE conversation_id = %s
            ORDER BY timestamp ASC
        """, (conversation['id'],))

        messages = cursor.fetchall()

        # Get generated files
        cursor.execute("""
            SELECT file_type, file_name, file_content, created_at
            FROM generated_files
            WHERE conversation_id = %s
            ORDER BY created_at DESC
        """, (conversation['id'],))

        files = cursor.fetchall()

        return {
            'conversation': conversation,
            'messages': messages,
            'files': files
        }

    except Error as e:
        st.error(f"Failed to load conversation: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Page configuration
st.set_page_config(
    page_title="AI Discussion Manager",
    page_icon="🤖",
    layout="wide"
)

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

# Main UI
st.title("🤖 AI Discussion Manager")
st.markdown("*Watch multiple OpenAI developer teams collaborate on your project in real-time. Upload documentation or describe your project for comprehensive analysis and planning.*")

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

            if st.button(f"📄 {title[:30]}... ({created_date})", key=f"hist_{conv.get('id')}"):
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
                        if st.button("👁️ Full View", key=f"fullview_{file_name}"):
                            st.text_area("Full Content:", file_content, height=400, key=f"textarea_{file_name}")
                    with col_btn3:
                        if st.button("📋 Copy", key=f"copy_{file_name}"):
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
