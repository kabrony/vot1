# Contributing to VOT1

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-contributing-banner.png" alt="VOT1 Contributing" width="100%">
</div>

## 🌟 Welcome

Thank you for considering contributing to VOT1! This document provides guidelines and instructions for contributing to the project. By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## 🎯 Types of Contributions

We welcome the following types of contributions:

- 🐛 **Bug reports and fixes**
- ✨ **Feature requests and implementations**
- 📚 **Documentation improvements**
- 🧪 **Test coverage improvements**
- 💻 **Code refactoring**
- 🎨 **UI/UX enhancements**
- 🌐 **Internationalization**

## 🚀 Getting Started

### Environment Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/vot1.git
   cd vot1
   ```

3. Set up the development environment:
   ```bash
   # Create a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Create a branch for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. Make your changes
2. Run tests to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```

3. Run linting to ensure code quality:
   ```bash
   flake8
   ```

4. Commit your changes using conventional commit messages:
   ```bash
   git commit -m "feat: add new memory retrieval method"
   ```

5. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a pull request to the main repository

## 📋 Pull Request Process

1. Ensure your code passes all tests and linting checks
2. Update documentation to reflect any changes
3. Include tests for new functionality
4. Fill out the pull request template completely
5. Request review from the appropriate team members (see [CODEOWNERS](.github/CODEOWNERS))
6. Address any feedback from reviewers

## 📝 Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This leads to more readable messages that are easy to follow when looking through the project history.

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
feat(memory): implement efficient retrieval using HNSW

This commit adds a new memory retrieval method using Hierarchical Navigable 
Small Worlds (HNSW) to improve search efficiency by 40% while maintaining 
accuracy.

Closes #123
```

### Types

* **feat**: A new feature
* **fix**: A bug fix
* **docs**: Documentation only changes
* **style**: Changes that do not affect the meaning of the code
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **perf**: A code change that improves performance
* **test**: Adding missing tests or correcting existing tests
* **chore**: Changes to the build process or auxiliary tools and libraries

## 🧪 Testing

We strive for high test coverage. When contributing:

- Write tests for new features
- Ensure existing tests pass with your changes
- Add regression tests for bug fixes

Run the test suite with:

```bash
pytest
```

For coverage reports:

```bash
pytest --cov=src
```

## 📚 Documentation

Good documentation is crucial. Please update the documentation when you change code:

- Update docstrings for any modified functions/classes
- Update README.md if necessary
- Update the relevant documentation in the `/docs` directory

## 🖌️ Code Style

We follow Python's PEP 8 style guide with a few modifications. Our code style is enforced using flake8.

Key style points:
- Use 4 spaces for indentation
- Line length: 100 characters
- Use descriptive variable names
- Document all public methods and classes

## 🙏 Recognition

Contributors are recognized in the following ways:

- Listed in the [CONTRIBUTORS.md](CONTRIBUTORS.md) file
- Mentioned in release notes when their contributions are included
- Given credit in documentation for significant contributions

## 📈 Development Roadmap

See our [project board](https://github.com/villageofthousands/vot1/projects/1) for the current development priorities.

## 🏆 Contribution Rewards

Active contributors may be invited to join the core team and given additional repository access based on their contributions.

## 🎨 Design Guidelines

When contributing to the UI:

- Follow the existing color scheme:
  - Primary: `#3c1f3c`
  - Secondary: `#1f3c3c`
  - Accent: `#6c4f9c`
  - Background: `#f9f9fb`
  - Text: `#2d2d2d`
- Use the existing CSS classes where possible
- Maintain responsive design practices
- Consider accessibility guidelines

<div align="center">
  <img src="https://raw.githubusercontent.com/villageofthousands/vot1-assets/main/vot1-color-palette.png" alt="VOT1 Color Palette" width="80%">
</div>

## 📬 Contact

For questions or discussions about contributing:

- Join our [Discord server](https://discord.gg/villagethousands)
- Use GitHub Discussions for feature ideas
- Use GitHub Issues for bugs and tasks

---

<div align="center">
  <p>
    <sub>Thank you for contributing to VOT1! Your efforts help build a better autonomous intelligence system.</sub>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Built_with-%F0%9F%92%9C-6c4f9c?style=for-the-badge" alt="Built with love">
  </p>
</div> 