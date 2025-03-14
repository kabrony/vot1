# Contributing to VOT1

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-contributing-banner.png" alt="VOT1 Contributing" width="100%">
</div>

## 🌟 Welcome

Thank you for considering contributing to VOT1! This document provides guidelines and instructions for contributing to the project. By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Types of Contributions](#-types-of-contributions)
- [Getting Started](#-getting-started)
- [Development Workflow](#-development-workflow)
- [Pull Request Process](#-pull-request-process)
- [Commit Message Guidelines](#-commit-message-guidelines)
- [Documentation](#-documentation)
- [Testing](#-testing)
- [Style Guidelines](#-style-guidelines)
- [Community](#-community)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## 🎯 Types of Contributions

We welcome the following types of contributions:

- 🐛 **Bug reports and fixes**: If you find a bug, please open an issue or submit a fix
- ✨ **Feature requests and implementations**: Suggest new features or implement approved feature requests
- 📚 **Documentation improvements**: Help make our documentation more accessible, clear, and complete
- 🧪 **Test coverage improvements**: Add tests for features or fix existing tests
- 💻 **Code refactoring**: Improve code quality without changing functionality
- 🎨 **UI/UX enhancements**: Improve the user interface and experience
- 🌐 **Internationalization**: Help translate the project to other languages
- 🔧 **DevOps improvements**: Enhance CI/CD workflows, Docker configurations, etc.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Git
- Node.js 14+ (for dashboard development)

### Environment Setup

1. **Fork the repository** on GitHub.

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vot1.git
   cd vot1
   ```

3. **Set up the development environment**:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Add the upstream repository as a remote**:
   ```bash
   git remote add upstream https://github.com/kabrony/vot1.git
   ```

5. **Create a branch for your contribution**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🔄 Development Workflow

1. **Ensure your branch is up to date with the main repository**:
   ```bash
   git fetch upstream
   git merge upstream/main
   ```

2. **Make your changes** following the [style guidelines](#-style-guidelines).

3. **Run tests** to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```

4. **Run linting** to ensure code quality:
   ```bash
   flake8
   ```

5. **Commit your changes** using [conventional commit messages](#-commit-message-guidelines):
   ```bash
   git commit -m "feat: add new memory retrieval method"
   ```

6. **Push your changes** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a pull request** to the main repository from your fork on GitHub.

## 📋 Pull Request Process

1. **Fill out the pull request template** completely.
2. **Ensure your code passes all tests and linting checks**.
3. **Update documentation** to reflect any changes.
4. **Include tests** for new functionality.
5. **Request review** from the appropriate team members (see [CODEOWNERS](.github/CODEOWNERS)).
6. **Address any feedback** from reviewers promptly.

Pull requests will be merged once they have been approved by at least one maintainer and pass all automated checks.

## 📝 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This leads to more readable messages that are easy to follow when looking through the project history and helps with automatic versioning and changelog generation.

### Commit Message Format

Each commit message consists of a **header**, a **body**, and a **footer**:

```
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

Example:
```
feat(memory): add semantic search functionality

Implement vector-based semantic search in the memory module.
This allows for retrieval of memories based on semantic similarity
rather than exact keyword matching.

Closes #123
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (formatting, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Regular maintenance tasks

### Scope

The scope should be the name of the component affected (e.g., memory, api, dashboard, reasoning).

### Subject

The subject contains a succinct description of the change:
- Use the imperative, present tense: "change" not "changed" nor "changes"
- Don't capitalize the first letter
- No period (.) at the end

### Body

The body should include the motivation for the change and contrast this with previous behavior.

### Footer

The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit closes.

## 📚 Documentation

Good documentation is crucial for the success of the project. When contributing:

1. **Update the README.md** if your changes add or modify features.
2. **Update the API documentation** if you change any public interfaces.
3. **Add docstrings** to all functions, classes, and modules.
4. **Include examples** where appropriate.
5. **Use clear and concise language** that is accessible to non-experts.

## 🧪 Testing

We use pytest for testing. All new features should include appropriate test coverage:

1. **Unit tests** for individual functions and classes.
2. **Integration tests** for interactions between components.
3. **E2E tests** for complete user workflows.

To run tests:
```bash
# Run all tests
pytest

# Run specific tests
pytest tests/path/to/test_file.py

# Run tests with coverage
pytest --cov=src
```

## 🎨 Style Guidelines

We aim for a consistent codebase that is easy to read and maintain:

1. **Python Code**: Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines.
2. **JavaScript Code**: Follow [Airbnb's JavaScript Style Guide](https://github.com/airbnb/javascript).
3. **Docstrings**: Use [Google-style docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html).
4. **Type Hints**: Use Python's type hints for all function definitions.

We use automated tools to enforce these guidelines:
- **flake8** for Python linting
- **black** for Python formatting
- **isort** for sorting imports
- **eslint** for JavaScript linting

## 👥 Community

Getting involved in the community is a great way to contribute to the project:

- **Help answer questions** in issues and discussions
- **Review pull requests** from other contributors
- **Participate in discussions** about new features and improvements
- **Share your experience** using VOT1 on social media or blog posts

## 🙏 Thank You

Your contributions are invaluable to the project! By contributing, you help make VOT1 better for everyone. We appreciate your time and effort.

<div align="center" style="background-color: #3c1f3c; padding: 10px; border-radius: 5px; margin-top: 20px;">
  <p style="color: #f9f9fb;">
    Thank you for your contribution to the VOT1 community! 💜
  </p>
</div> 