# 🤖 AI Discussion Manager v2.0

An intelligent collaborative development tool that simulates multiple AI developer teams working together on your project in real-time. Now with enhanced file management, word limits, and persistent storage!

## 🌟 Features

### Core Functionality
- **Multi-AI Collaboration**: Choose from 7 specialized AI teams (Frontend, Backend, Database, Security, AI Engineer, Project Manager, DevOps Engineer)
- **File Upload Support**: Upload `.md` or `.txt` files for comprehensive analysis
- **Real-time Discussion**: Watch AI teams collaborate and debate technical decisions
- **Discussion Styles**: Collaborative, Debate, Technical Review, or Creative Brainstorm
- **Word Limit Validation**: 150-word maximum for project descriptions
- **Environment Configuration**: Secure OpenAI key management via environment variables

### Advanced Features
- **MySQL Database Integration**: Persistent storage for conversations and generated files
- **Automatic Documentation Generation**: Creates project specifications, implementation guides, and Cursor IDE prompts
- **Manager Oversight**: Project Manager role coordinates team efforts and provides executive summaries
- **Enhanced File Management**: File filtering, preview, download, and review capabilities
- **Conversation History**: Browse and reload previous discussions by title
- **Session Persistence**: Conversations and files are automatically saved to database
- **Quick Actions**: New discussion, export summary, and file management tools

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL Server 8.0+
- OpenAI API Key

### Installation

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd ai-discussion-manager
pip install -r requirements.txt
```

2. **Environment Configuration**:
Create a `.env` file in the project root:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ai_discussion_manager
DB_PORT=3306

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional Settings
MAX_WORD_LIMIT=150
DEFAULT_DISCUSSION_ROUNDS=5
DEBUG_MODE=false
```

3. **Database Setup**:
```bash
# Run the database setup script
python setup_database.py
```

4. **Run the Application**:
```bash
streamlit run main.py
```

## 📁 Project Structure

```
ai-discussion-manager/
├── main.py                 # Main Streamlit application
├── setup_database.py       # Database setup script
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── test_connection.py     # API connection testing utility
```

## 🗄️ Database Schema

### Tables
- **conversations**: Stores conversation metadata and project information
- **messages**: Stores all conversation messages (user and AI responses)
- **generated_files**: Stores generated documentation files

### Database Configuration
The application uses the following environment variables:
- `DB_HOST`: MySQL server host (default: localhost)
- `DB_USER`: MySQL username (default: root)
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: Database name (default: ai_discussion_manager)

## 👥 AI Teams

### Available Specialists (7 Teams)
1. **Frontend Dev**: UI/UX, responsive design, modern frameworks
2. **Backend Dev**: APIs, server architecture, scalability
3. **Database Expert**: Data modeling, optimization, security
4. **Security Specialist**: Security best practices, vulnerability assessment
5. **AI Engineer**: ML integration, intelligent features
6. **Project Manager**: Coordination, planning, risk management
7. **DevOps Engineer**: Infrastructure, deployment, automation, monitoring

### Team Selection
- **Maximum**: 7 teams (increased from 4)
- **Minimum**: 1 team
- **Recommendation**: 3-5 teams for optimal collaboration

### Discussion Styles
- **Collaborative**: Team members work together constructively
- **Debate**: Technical discussions and alternative approaches
- **Technical Review**: Detailed analysis and recommendations
- **Creative Brainstorm**: Innovative solutions and forward-thinking

### Word Limits & Validation
- **Maximum Words**: 150 words per project description field
- **Real-time Validation**: Word count displayed as you type
- **Character Limit**: ~1500 characters (approximately 150 words)
- **Validation Feedback**: Clear error messages for exceeded limits

## 📄 Generated Files

The system automatically generates three types of documentation:

### 1. Project Specification (Markdown)
- Complete project overview with goals and requirements
- Team analysis and technical recommendations
- Implementation guidelines and best practices
- Architecture recommendations and next steps

### 2. Cursor IDE Prompts (Markdown)
- Development guidelines for Cursor IDE
- Technology stack recommendations
- AI-assisted development prompts
- Team-specific development guidelines
- Deployment and production setup

### 3. Manager Summary (Markdown)
- Executive summary and project status
- Team contribution analysis
- Implementation roadmap and timeline
- Risk assessment and mitigation strategies
- Success metrics and next steps

## 🔄 New Features in v2.0

### Enhanced User Interface
- **Environment-Based Configuration**: Secure OpenAI key management via `.env` file
- **Word Limit Validation**: Real-time word counting with 150-word limit
- **Improved Validation**: Better error messages and requirement checking

### Advanced File Management
- **File Filtering**: Filter generated files by type (markdown, cursor_guide, etc.)
- **File Statistics**: View file counts, sizes, and line numbers
- **Enhanced Preview**: Better file content preview with copy functionality
- **Bulk Actions**: Download individual files or prepare for bulk operations

### Conversation History
- **History Browser**: View previous conversations by title and date
- **Quick Reload**: Load any previous conversation with one click
- **Session Management**: New session creation without losing history

### Quick Actions Panel
- **New Discussion**: Start fresh conversations easily
- **Export Summary**: Download conversation summaries
- **File Review**: Review uploaded file content
- **Session Info**: Detailed session and database status

## 🔧 Usage

### Starting a Discussion

1. **Environment Setup**: Ensure `.env` file is configured with OpenAI API key
2. **Initialize OpenAI**: Click "🔗 Initialize OpenAI" button
3. **Select Teams**: Choose up to 7 AI specialists (max 7)
4. **Input Method**:
   - **Manual Input**: Describe your project (max 150 words) and goals
   - **File Upload**: Upload `.md` or `.txt` files for analysis
5. **Discussion Settings**: Choose discussion style and rounds
6. **Start Discussion**: Watch AI teams collaborate in real-time

### Word Limits & Validation

- **Real-time Word Counting**: See word count as you type (max 150 words)
- **Visual Indicators**: Green for under limit, red for over limit
- **Validation**: Cannot start discussion if word limits are exceeded
- **Help Text**: Tooltips show character limits (~1500 characters)

### Generating Documentation

After discussion completion:
1. Click "📝 Generate All Files" to create complete documentation
2. Or click "📊 Generate Manager Summary Only" for executive summary
3. Use file filtering to view specific types of generated files
4. Download individual files or review full content
5. Files are automatically saved to the database

### Managing History & Files

1. **View History**: Click "🔄 Load History" to browse previous conversations
2. **Reload Sessions**: Click on any conversation title to reload it
3. **File Management**: Filter, preview, and download generated files
4. **Quick Actions**: Start new discussions or export summaries

## 🔐 Security & Privacy

- **Environment Variables**: OpenAI API key stored securely in `.env` file
- **No API Key Input**: Removed from UI to prevent accidental exposure
- **File Processing**: File uploads processed in-memory only
- **Database Security**: Conversation data and generated files stored securely
- **Session Management**: Unique session IDs for conversation isolation
- **No External Data Transmission**: All processing done locally

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Test database connection
python setup_database.py
```

### OpenAI API Issues
```bash
# Test OpenAI connection
python test_connection.py your_openai_api_key
```

### Common Issues
- **"Module 'openai' has no attribute 'OpenAI'"**: Upgrade OpenAI library with `pip install --upgrade openai`
- **Database connection failed**: Check MySQL server is running and credentials are correct
- **File upload errors**: Ensure files are `.md` or `.txt` format and under size limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📋 Requirements

### Python Packages
- streamlit>=1.28.0
- openai>=1.0.0
- mysql-connector-python>=8.0.0
- pymysql>=1.0.0
- python-dotenv>=1.0.0

### System Requirements
- Python 3.8+
- MySQL 8.0+
- 4GB RAM minimum
- Stable internet connection

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the generated documentation files
3. Test with the provided setup scripts

## 📈 Future Enhancements

- [ ] Multiple language support for generated files
- [ ] Integration with GitHub/GitLab for project management
- [ ] Advanced analytics and reporting
- [ ] Custom AI team configurations
- [ ] Real-time collaboration features
- [ ] Integration with popular IDEs beyond Cursor

---

*Generated by AI Discussion Manager - Revolutionizing collaborative software development* 🚀
