# Contributing to AI Discussion Manager

Thank you for your interest in contributing to the AI Discussion Manager! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- MySQL Server 8.0+
- Git
- OpenAI API key

### Development Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-discussion-manager.git
   cd ai-discussion-manager
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database and OpenAI credentials
   ```

5. **Database Setup**
   ```bash
   python setup_database.py
   ```

6. **Run the Application**
   ```bash
   streamlit run main.py
   ```

## 🛠️ Development Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Add docstrings to all functions and classes
- Keep functions focused on single responsibilities

### Git Workflow
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes and test thoroughly
3. Commit with clear, descriptive messages
4. Push your branch and create a Pull Request

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep the first line under 50 characters
- Add detailed description if needed

Example:
```
Add word limit validation for project descriptions

- Implement real-time word counting
- Add visual indicators for word limits
- Prevent submission when limits exceeded
- Add helpful tooltips for users
```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python test_updates.py

# Run specific test components
python -c "from test_updates import test_word_count_logic; test_word_count_logic()"
```

### Test Coverage
- Test all new features before submitting
- Ensure backward compatibility
- Test edge cases and error conditions
- Verify database operations work correctly

## 📋 Feature Requests

### Before Submitting
1. Check existing issues and pull requests
2. Create a detailed issue describing the feature
3. Discuss the implementation approach
4. Get approval before starting development

### Feature Requirements
- Clear description of the problem being solved
- Proposed solution and implementation details
- Impact on existing functionality
- Testing strategy

## 🐛 Bug Reports

### Bug Report Template
Please include:
1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Step-by-step instructions
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: Python version, OS, browser (for web issues)
6. **Screenshots**: If applicable
7. **Error Logs**: Any relevant error messages

## 🔧 Pull Request Process

1. **Update Documentation**: Update README.md and docstrings as needed
2. **Add Tests**: Include tests for new functionality
3. **Update Requirements**: Add new dependencies to requirements.txt
4. **Verify Compatibility**: Test on multiple Python versions if possible

### PR Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No breaking changes without discussion
- [ ] Reviewed by at least one maintainer

## 📚 Documentation

### Code Documentation
- Add docstrings to all public functions
- Include type hints where possible
- Document complex algorithms and business logic
- Update inline comments as needed

### User Documentation
- Update README.md for new features
- Add examples and use cases
- Include troubleshooting information
- Keep setup instructions current

## 🎯 Areas for Contribution

### High Priority
- [ ] Add more AI specialist roles
- [ ] Improve error handling and user feedback
- [ ] Add export functionality for different formats
- [ ] Implement conversation templates

### Medium Priority
- [ ] Add user authentication and session management
- [ ] Implement real-time collaboration features
- [ ] Add analytics and usage tracking
- [ ] Create API endpoints for integrations

### Low Priority
- [ ] Add support for more file types
- [ ] Implement conversation branching
- [ ] Add voice input/output capabilities
- [ ] Create mobile-responsive interface

## 📞 Getting Help

If you need help or have questions:
1. Check the existing documentation
2. Search existing issues and discussions
3. Create a new issue with detailed information
4. Join our community discussions

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please:
- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers learn and contribute
- Follow our community guidelines

Thank you for contributing to the AI Discussion Manager! 🎉
