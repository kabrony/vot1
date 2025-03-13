# Contributing to VOT1

Thank you for your interest in contributing to VOT1! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our code of conduct: be respectful, constructive, and collaborative.

## How to Contribute

There are several ways you can contribute to VOT1:

1. **Report bugs or suggest features**: Open an issue on GitHub
2. **Improve documentation**: Submit PRs for documentation improvements
3. **Submit code changes**: Implement new features or fix bugs
4. **Share your experience**: Write about how you're using VOT1

## Development Process

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork locally
3. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys (see `.env.example`)

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests to ensure your changes don't break existing functionality:
   ```bash
   pytest
   ```
4. Commit your changes with a descriptive commit message
5. Push your changes to your fork

### Submitting a Pull Request

1. Submit a pull request from your fork to the main repository
2. In your PR description, explain:
   - What the PR does
   - Why the change is necessary
   - How you tested the changes
   - Any other relevant information

### Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, a maintainer will merge your PR

## Coding Standards

### Python Code

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where appropriate
- Add docstrings for all functions, classes, and modules
- Write unit tests for new functionality

### JavaScript Code

- Follow [Standard JS](https://standardjs.com/) style
- Use ES6+ features where appropriate
- Comment complex code

### HTML/CSS

- Use semantic HTML
- Follow BEM methodology for CSS class names

## Documentation

When adding or changing features, please update the relevant documentation:

- Update comments and docstrings
- Update README.md if necessary
- Update any relevant documentation in the `docs` directory

## Self-Improvement Workflow

If you're working on the self-improvement workflow:

1. Test your changes with small, isolated examples first
2. Add appropriate safety checks
3. Document your reasoning in comments
4. Consider the implications of autonomous modifications

## License

By contributing to VOT1, you agree that your contributions will be licensed under the project's MIT License.

## Questions?

If you have any questions or need help, feel free to:

- Open an issue with your question
- Contact the maintainers directly

Thank you for contributing to VOT1! 