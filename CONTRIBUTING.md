# Contributing to Solokit (Session-Driven Development)

Thank you for your interest in contributing to Solokit! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project follows standard open-source community guidelines:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept differing viewpoints
- Show empathy towards other contributors

## Getting Started

Before you begin:

1. **Familiarize yourself with Solokit** - Read the [README](README.md) and [documentation](docs/README.md)
2. **Check existing issues** - Look for open issues or create a new one
3. **Understand the architecture** - Review the [Solokit Framework](docs/architecture/solokit-methodology.md)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Claude Code (for testing slash commands)
- pytest for running tests

### Clone and Setup

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/solokit.git
cd solokit

# Install development dependencies
pip install pytest pytest-cov

# Run tests to verify setup
pytest tests/
```

### Project Structure

```
solokit/
├── .claude/commands/        # Slash command definitions (15 commands)
├── src/solokit/                 # Python package (standard src/ layout)
│   ├── cli.py               # CLI entry point
│   ├── core/                # Core functionality
│   ├── session/             # Session management
│   ├── work_items/          # Work item management
│   ├── learning/            # Learning system
│   ├── quality/             # Quality gates
│   ├── visualization/       # Dependency graphs
│   ├── git/                 # Git integration
│   ├── testing/             # Testing utilities
│   ├── deployment/          # Deployment executor
│   ├── project/             # Project initialization
│   └── templates/           # Work item spec templates
├── docs/                   # Documentation
│   ├── architecture/       # System architecture and design
│   ├── guides/             # User guides and how-tos
│   ├── reference/          # Reference documentation
│   ├── project/            # Project planning
│   └── development/        # Development notes
├── tests/                  # Test suites (3,225 tests)
├── Makefile                # Developer convenience targets
└── pyproject.toml          # Package configuration (PEP 517/518)
```

## How to Contribute

### Step 1: Fork and Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/solokit.git
cd solokit

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/your-bugfix-name
```

### Step 2: Make Your Changes

- Write clear, maintainable code
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed

### Step 3: Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific phase tests
pytest tests/phase_1/
pytest tests/phase_5/

# Run with coverage
pytest tests/ --cov=scripts --cov-report=html
```

### Step 4: Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add: Brief description of your changes"
```

**Commit Message Guidelines:**
- Use imperative mood ("Add feature" not "Added feature")
- Start with a verb (Add, Fix, Update, Refactor, etc.)
- Keep first line under 72 characters
- Add detailed description if needed

### Step 5: Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request on GitHub
```

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

### Example:

```python
def calculate_dependency_depth(work_item_id: str, work_items: dict) -> int:
    """
    Calculate the maximum dependency depth for a work item.

    Args:
        work_item_id: The ID of the work item to analyze
        work_items: Dictionary of all work items

    Returns:
        The maximum dependency depth (0 if no dependencies)
    """
    # Implementation here
    pass
```

### Import Patterns

**IMPORTANT:** Solokit uses a hybrid packaging approach (v0.5.7). Follow these import patterns:

**For scripts importing other scripts:**
```python
from scripts.file_ops import load_json, save_json
from scripts.work_item_manager import WorkItemManager
from scripts.quality_gates import QualityGates
```

**For tests importing scripts:**
```python
from scripts.work_item_manager import WorkItemManager
from scripts.session_manager import SessionManager
```

**DO NOT use relative imports:**
```python
# ❌ WRONG - Don't do this
from .file_ops import load_json
from solokit.work_items.manager import WorkItemManager
from solokit.quality.gates import QualityGates
from solokit.session.briefing import generate_briefing
```

**Import Guidelines:**
- Use standard Python imports from the `solokit` package
- No `sys.path` manipulation needed (v0.1.3+)
- Package organized by domain for clarity
- Full PEP 517/518 compliance

See [README.md Architecture Notes](README.md#architecture-notes) for package organization details.

### Command Design

For new slash commands:

- Keep prompts clear and concise
- Provide helpful error messages
- Follow existing command patterns
- Document expected inputs and outputs

## Testing Requirements

### Test Coverage

- **All new features must include tests**
- Maintain or improve existing test coverage
- Tests should be clear and well-documented
- Follow existing test patterns

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/phase_5/test_quality_gates.py

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=scripts
```

### Writing Tests

```python
def test_work_item_creation():
    """Test that work items are created correctly."""
    # Arrange
    manager = WorkItemManager()

    # Act
    work_item = manager.create_item(
        title="Test Feature",
        item_type="feature"
    )

    # Assert
    assert work_item["title"] == "Test Feature"
    assert work_item["type"] == "feature"
```

## Submitting Changes

### Pull Request Guidelines

1. **Title**: Clear and descriptive (e.g., "Add dependency graph filtering")
2. **Description**: Explain what and why, not just how
3. **Link Issues**: Reference related issues (e.g., "Fixes #123")
4. **Tests**: Ensure all tests pass
5. **Documentation**: Update relevant docs

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Related Issues
Fixes #(issue number)

## Additional Notes
Any additional context or notes
```

## Reporting Bugs

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - OS and version
   - Python version
   - Claude Code version
   - Solokit version/commit

### Bug Report Template

```markdown
**Description:**
Brief description of the bug

**Steps to Reproduce:**
1. Run command X
2. Observe behavior Y
3. Expected Z but got W

**Environment:**
- OS: macOS 14.0
- Python: 3.11.5
- Claude Code: 1.2.3
- Solokit: commit abc123

**Additional Context:**
Any other relevant information
```

## Suggesting Enhancements

We welcome enhancement suggestions! When suggesting:

1. **Check existing issues** - Avoid duplicates
2. **Describe the problem** - What problem does this solve?
3. **Propose a solution** - How would you implement it?
4. **Consider alternatives** - What other approaches exist?
5. **Explain benefits** - How does this improve Solokit?

### Enhancement Template

```markdown
**Problem:**
Description of the problem or limitation

**Proposed Solution:**
Detailed description of proposed enhancement

**Alternatives Considered:**
Other approaches you've considered

**Benefits:**
How this improves Solokit

**Implementation Notes:**
Technical considerations or challenges
```

## Development Workflow

### Typical Contribution Flow

1. Find or create an issue to work on
2. Fork and clone the repository
3. Create a feature branch
4. Make your changes
5. Write tests
6. Run test suite
7. Update documentation
8. Commit changes
9. Push to your fork
10. Open Pull Request

### Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged
- Your contribution will be credited

## Questions?

If you have questions:

- Check existing [issues](https://github.com/ankushdixit/solokit/issues)
- Review [documentation](docs/README.md)
- Open a new issue for discussion

## License

By contributing to Solokit, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

Thank you for contributing to Solokit! Your efforts help make AI-augmented development better for everyone.
