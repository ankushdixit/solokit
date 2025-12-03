# Solokit

[![PyPI](https://img.shields.io/pypi/v/solokit)](https://pypi.org/project/solokit/)
[![Tests](https://github.com/ankushdixit/solokit/workflows/Tests/badge.svg)](https://github.com/ankushdixit/solokit/actions?query=workflow%3ATests)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)](https://github.com/ankushdixit/solokit)

**Build production software alone with team-level sophistication.**

> Structured Solo Development with AI and Quality Automation for Claude Code

## What is Solokit?

**Solokit is a complete development framework for solo developers building production software with AI assistants like Claude Code.** It combines minimal scaffolding templates with comprehensive documentation, automated quality gates, intelligent session management, and AI-powered knowledge capture into a cohesive workflow that enables you to build alone with the sophistication of a 10-person engineering team.

### The Core Problem

Solo developers using AI assistants face critical challenges:
- **Setup Time Waste** - Spending hours configuring frameworks, linters, tests, CI/CD
- **Context Loss** - AI forgets previous work between sessions
- **Quality Entropy** - Standards slip without enforcement
- **Knowledge Fragmentation** - Learnings and decisions get lost
- **Lack of Process** - No systematic workflow for complex projects

### The Solokit Solution

**🚀 Start Building in <1 Minute**
- 4 minimal scaffolding templates (T3 Stack, FastAPI, Refine, Next.js)
- Comprehensive ARCHITECTURE.md guides with patterns and examples
- PRD-driven development workflow
- 4 quality tiers (Essential → Production-Ready)
- All dependencies version-pinned and compatibility-tested
- CI/CD, Docker, environment templates included

**✨ Perfect Context Continuity**
- Comprehensive AI briefings restore full project state
- Spec-first architecture with complete implementation details
- Previous work context for multi-session features
- Dependency-aware workflow recommendations

**🛡️ Zero-Compromise Quality**
- Automated gates: tests, linting, formatting, security
- Coverage thresholds, mutation testing, E2E tests
- Performance monitoring, error tracking (tier 4)
- Spec validation before and after sessions

**🧠 Knowledge That Grows**
- AI-powered learning categorization (6 categories)
- Automatic extraction from commits and code comments
- Smart deduplication and similarity detection
- Searchable, filterable knowledge base

## Quick Start

### 1. Install Solokit

```bash
# macOS/Linux
pip3 install solokit

# Windows
py -m pip install solokit
```

> **First-time macOS users:** When you run `pip3` for the first time, macOS will prompt you to install Command Line Tools. This is normal and required - the installation takes 5-10 minutes.

### 2. Initialize Your Project

**For new projects:**
```bash
sk init
```

**For existing projects with code:**
```bash
sk adopt
```

Choose from **4 minimal scaffolding stacks** (with `sk init`):
- **SaaS T3 Stack** - Next.js + tRPC + Prisma (full-stack SaaS)
- **ML/AI FastAPI** - FastAPI + Python ML libraries (model serving, data pipelines)
- **Dashboard Refine** - Refine + shadcn/ui (admin panels, internal tools)
- **Full-Stack Next.js** - Next.js + Prisma (general purpose web apps)

Each stack includes comprehensive ARCHITECTURE.md documentation with patterns you'll implement from your PRD.

Select your **quality tier**:
- **Essential** (60-80% coverage) - Prototypes, MVPs
- **Standard** (80% coverage + security) - Production apps
- **Comprehensive** (90% coverage + E2E + mutation) - Mission-critical
- **Production-Ready** (+ monitoring + observability) - Enterprise-grade

Options: CI/CD workflows, Docker support, environment templates

### 3. Start Building

```bash
# Create your first work item
sk work-new

# Start a development session
sk start

# Claude receives a comprehensive briefing with:
# - Complete work item specification
# - Project documentation and context
# - Technology stack and file structure
# - Related learnings from past sessions
# - Dependency information

# Work with Claude...

# End session with automated quality gates
sk end
```

**That's it!** You now have:
- ✅ Production-ready project setup
- ✅ Automated quality enforcement
- ✅ Perfect AI context continuity
- ✅ Growing knowledge base

## 💡 Best Used with Claude Code

Solokit is designed to work seamlessly with [Claude Code](https://claude.com/claude-code), providing:

- **Slash Command Interface**: Use `/start`, `/end`, `/work-new`, and more without memorizing CLI syntax
- **Context Continuity**: Claude maintains full project context across sessions, understanding your work items, dependencies, and progress
- **Interactive Workflow**: Rich prompts and guided workflows make session management effortless
- **Quality Automation**: Automatic quality gate validation and learning capture integrated into your natural workflow

### Quick Start with Claude Code

1. **Initialize your project** (one-time setup):
   ```bash
   sk init
   ```

2. **Open in Claude Code** and use slash commands:
   ```
   /work-new      # Create your first work item
   /start         # Begin a development session with full briefing
   /end           # Complete session with quality gates
   ```

That's it! Claude Code handles the rest, providing context-aware assistance throughout your development session.

## Key Features

### 🎯 Minimal Scaffolding Templates

Initialize projects with battle-tested configurations and comprehensive documentation:

**SaaS T3 Stack** (`saas_t3`)
- Next.js 16.0.1, React 19.2.0, tRPC 11.7.1, Prisma 6.19.0
- End-to-end type safety patterns documented in ARCHITECTURE.md
- Perfect for: SaaS products, B2B apps, complex data models

**ML/AI FastAPI** (`ml_ai_fastapi`)
- FastAPI 0.121.3, Python 3.11+, SQLModel, Pydantic 2.12.4
- Async patterns and service layer architecture documented
- Perfect for: ML model serving, data pipelines, Python microservices

**Dashboard Refine** (`dashboard_refine`)
- Refine 5.0.5, Next.js 16.0.1, shadcn/ui
- Data provider and Refine hook patterns documented
- Perfect for: Admin panels, internal dashboards, data management

**Full-Stack Next.js** (`fullstack_nextjs`)
- Next.js 16.0.1, React 19.2.0, Prisma 6.19.0
- Server Components and Server Actions patterns documented
- Perfect for: Marketing sites, content platforms, e-commerce

**All templates include:**
- Minimal scaffolding (health check endpoint + config only)
- Comprehensive ARCHITECTURE.md with code patterns and examples
- Exact version pinning (all tested for compatibility)
- Framework-specific ESLint/Prettier configurations
- Testing setup with framework utilities
- TypeScript/Python type checking
- Security scanning configured
- Docker Compose for local development
- CI/CD workflows (GitHub Actions)
- Environment variable templates
- **Three-File Documentation Model** (see below)

### 📚 Documentation-First Development

Every project initialized with `sk init` includes comprehensive documentation for building from scratch:

**Three-File Documentation Model:**

| File | Purpose | Audience | Generated |
|------|---------|----------|-----------|
| **README.md** | Quick start guide | Human developers | Yes (project-specific) |
| **ARCHITECTURE.md** | Technical patterns & examples | Human developers + Claude | No (static template) |
| **CLAUDE.md** | AI guidance & Solokit usage | Claude Code | Yes (from template) |

**Development Guides** (in `.session/guides/`):

| Guide | Purpose |
|-------|---------|
| **STACK_GUIDE.md** | Understand your chosen stack's architecture and patterns |
| **PRD_WRITING_GUIDE.md** | Write effective PRDs for AI-driven development |

**CLAUDE.md** is a key differentiator - it provides Claude Code with:
- Stack-specific architecture rules and patterns
- Comprehensive Solokit command usage guide
- Work item management instructions
- Session workflow documentation
- Learning capture best practices
- Anti-patterns and common mistakes to avoid

This means Claude Code automatically understands your project's conventions, quality standards, and how to use Solokit effectively from the first session.

**ARCHITECTURE.md** provides deep technical documentation:
- Architecture decisions with rationale and trade-offs
- Code patterns and examples specific to your stack
- Project structure explanations
- Database workflows
- Troubleshooting guides

### 🛡️ Quality Gates

Automated validation prevents technical debt:

**Available Checkers:**
- **Tests** - Unit, integration, E2E with coverage thresholds
- **Linting** - Code quality (ESLint/Ruff) with auto-fix
- **Formatting** - Code style (Prettier/Ruff) with auto-format
- **Security** - Vulnerability scanning (bandit, safety, npm audit)
- **Type Checking** - Static analysis (TypeScript/mypy)
- **Documentation** - CHANGELOG, README, docstring validation
- **Spec Completeness** - Work item specification validation
- **Performance** - Benchmarks and regression detection

**Quality Tiers:**

| Tier | Use Case | What's Included |
|------|----------|-----------------|
| **Essential** | Prototypes, MVPs | Linting, formatting, type-check, basic tests (60-80% coverage) |
| **Standard** | Production apps | Essential + Pre-commit hooks, security scanning, dependency auditing |
| **Comprehensive** | Mission-critical | Standard + Mutation testing (75%+), E2E tests, integration tests |
| **Production-Ready** | Enterprise | Comprehensive + Sentry, OpenTelemetry, performance monitoring, health checks |

Configure in `.session/config.json`:
```json
{
  "quality_gates": {
    "tests": {"enabled": true, "required": true, "coverage_threshold": 80},
    "linting": {"enabled": true, "required": false, "auto_fix": true},
    "security": {"enabled": true, "required": true, "fail_on": "high"}
  }
}
```

### 📋 Session Management

**Perfect context continuity** across all AI interactions:

> 💡 **Recommended: Use Claude Code for the best experience**

**Start a session** in Claude Code:

```
/start feature_xyz
```

Claude receives:
1. **Complete Work Item Spec** - Full implementation details from `.session/specs/feature_xyz.md`
2. **Project Documentation** - Vision, architecture, PRD
3. **Technology Stack** - Auto-detected frameworks and versions
4. **Project Structure** - Current file tree
5. **Git Context** - Branch status, recent commits
6. **Related Learnings** - Past insights relevant to this work
7. **Dependency Context** - What this depends on and what depends on it
8. **Milestone Progress** - Where this fits in the roadmap
9. **Previous Work Context** - For in-progress items: commits made, files changed, quality results

**Complete session** with automatic quality enforcement:

```
/end
```

The `/end` command asks whether the work item is complete and runs quality gates accordingly:

**Complete mode** (`--complete`):
- ✅ Runs all enabled quality gates (enforced/blocking)
- ✅ Quality gates must pass to end session
- ✅ Marks work item as "completed"

**Incomplete mode** (`--incomplete`):
- ✅ Runs quality gates but doesn't block session end (non-blocking)
- ✅ Useful when running out of context with failing gates
- ✅ Keeps work item as "in_progress" for later resumption

Both modes automatically:
- ✅ Updates stack/tree tracking
- ✅ Extracts learnings from work
- ✅ Commits with standardized message
- ✅ Pushes to remote
- ✅ Generates session summary

<details>
<summary><strong>Alternative: Terminal Usage</strong> (without AI assistance)</summary>

```bash
sk start feature_xyz  # Start session
sk end                # Complete session
```

</details>

### 🎯 Work Item Management

**Dependency-driven, spec-first workflow:**

> 💡 **Recommended: Use Claude Code for interactive work item creation and management**

**Create and manage work items** in Claude Code:

```
/work-new                              # Create work items interactively
/work-list                             # List all work items
/work-list --status not_started        # Filter by status
/work-list --milestone "v1.0"          # Filter by milestone

/work-next                             # Get smart recommendations (dependencies completed)

/work-graph --critical-path            # Show longest dependency chain
/work-graph --bottlenecks              # Identify blockers
/work-graph --format svg               # Export visual graph

/work-update feature_xyz --status in_progress
/work-update feature_xyz --priority high
```

<details>
<summary><strong>Alternative: Terminal Usage</strong> (without AI assistance)</summary>

```bash
sk work-new                        # Create work items interactively
sk work-list                       # List all work items
sk work-list --status not_started
sk work-list --milestone "v1.0"

sk work-next                       # Get recommendations
sk work-graph --critical-path      # Visualize dependencies
sk work-update feature_xyz --status in_progress
```

</details>

**Spec-First Architecture:**

Work item specifications are the single source of truth:

```
.session/
├── specs/
│   ├── feature_xyz.md         # Complete implementation guide
│   └── deployment_abc.md
└── tracking/
    └── work_items.json         # Metadata only (status, deps)
```

**6 work item types** with structured templates:
- **Feature** - New functionality
- **Bug** - Issue fixes with root cause analysis
- **Refactor** - Code improvements
- **Security** - Security enhancements
- **Integration Test** - Test suites
- **Deployment** - Deployment procedures

Each template includes:
- Required sections enforced via validation
- Implementation details, acceptance criteria
- Testing strategy, validation rules
- Type-specific guidelines

### 🧠 Learning System

**AI-powered knowledge capture and curation:**

> 💡 **Recommended: Use Claude Code for AI-assisted learning capture**

**Capture and browse learnings** in Claude Code:

```
/learn                                # Capture learnings during development (AI-assisted)

/learn-show                           # Browse all learnings
/learn-show --category gotchas --tag fastapi

/learn-search "CORS"                  # Search by keyword

/learn-curate                         # Auto-curate (categorize, deduplicate, merge)
```

<details>
<summary><strong>Alternative: Terminal Usage</strong> (without AI assistance)</summary>

```bash
sk learn                       # Capture learnings manually
sk learn-show                  # Browse all learnings
sk learn-search "CORS"         # Search by keyword
sk learn-curate                # Run curation
```

</details>

**6 Learning Categories** (auto-categorized):
- **Architecture** - Design decisions, patterns
- **Gotchas** - Edge cases, pitfalls
- **Best Practices** - Effective approaches
- **Technical Debt** - Areas needing improvement
- **Performance** - Optimization insights
- **Security** - Security discoveries

**3 Extraction Sources:**
1. Session summaries ("Learnings Captured" section)
2. Git commits (`LEARNING:` annotations)
3. Code comments (`# LEARNING:` in changed files)

**Smart Deduplication:**
- Jaccard + containment similarity detection
- Automatic merging of similar learnings
- Configurable similarity threshold (default: 0.7)

### 🔄 Adopting Existing Projects

Already have a project? Use `sk adopt` to add Solokit's session management without modifying your existing code:

```bash
sk adopt
```

**What `sk adopt` does:**
- Auto-detects your project type (Python, Node.js, TypeScript, Fullstack)
- Creates `.session/` directory for tracking
- Installs Claude Code slash commands
- Appends Solokit sections to README.md and CLAUDE.md
- Updates `.gitignore` with Solokit entries
- Installs git hooks for quality enforcement

**What `sk adopt` does NOT do:**
- Modify your existing source code
- Overwrite your documentation content
- Install project templates or starter code
- Change your existing tooling configuration

**When to use `sk adopt` vs `sk init`:**

| Scenario | Command |
|----------|---------|
| Starting a brand new project | `sk init` |
| Adding Solokit to existing codebase | `sk adopt` |
| Project already has package.json/pyproject.toml | `sk adopt` |
| Want production-ready templates | `sk init` |

**Example adoption workflow:**

```bash
# Navigate to your existing project
cd my-existing-project

# Adopt Solokit (interactive prompts)
sk adopt

# Or with arguments
sk adopt --tier=tier-2-standard --coverage=80 --yes

# Start using Solokit
sk work-new
sk start
```

## Commands Reference

> 💡 **Best Experience: Use these commands in Claude Code for AI-assisted development**

### Session Commands (Claude Code)

```
/init                 # Initialize new project with template selection
/adopt                # Add Solokit to existing project
/start [item_id]      # Start session with comprehensive briefing
/end                  # Complete session with quality gates
/status               # Quick session overview
/validate             # Pre-flight check (run gates without ending)
```

### Work Item Commands (Claude Code)

```
/work-new             # Create work item interactively (AI-assisted)
/work-list            # List all work items
/work-show <id>       # Show work item details
/work-update <id>     # Update work item fields
/work-next            # Get next recommended work item
/work-graph           # Visualize dependency graph
/work-delete <id>     # Delete work item (with safety checks)
```

### Learning Commands (Claude Code)

```
/learn                # Capture learning interactively (AI-assisted)
/learn-show           # Browse all learnings
/learn-search <q>     # Search learnings by keyword
/learn-curate         # Run curation (categorize, deduplicate)
```

### Utility Commands (Claude Code & Terminal)

```
sk help               # Show all commands with descriptions
sk help <command>     # Show detailed help for specific command
sk version            # Show version information
sk --version, -V      # Show version (global flag)
sk doctor             # Run system diagnostics
sk config show        # Display current configuration
sk config show --json # Display configuration as JSON
```

<details>
<summary><strong>Alternative: Terminal Commands</strong> (without AI assistance)</summary>

### Session Commands
```bash
sk init               # Initialize new project
sk adopt              # Add Solokit to existing project
sk start [item_id]    # Start session
sk end                # Complete session
sk status             # Session status
sk validate           # Validate readiness
```

### Work Item Commands
```bash
sk work-new           # Create work item
sk work-list          # List work items
sk work-show <id>     # Show work item
sk work-update <id>   # Update work item
sk work-next          # Get recommendation
sk work-graph         # Visualize dependencies
sk work-delete <id>   # Delete work item
```

### Learning Commands
```bash
sk learn              # Capture learning
sk learn-show         # Browse learnings
sk learn-search <q>   # Search learnings
sk learn-curate       # Run curation
```

### Utility Commands
```bash
sk help               # Show all commands
sk help <command>     # Show command help
sk version            # Show version
sk --version, -V      # Show version (flag)
sk doctor             # Run diagnostics
sk config show        # Display config
sk config show --json # Display as JSON
```

</details>

## Typical Workflow

```mermaid
graph TD
    Start{New or Existing Project?}
    Start -->|New| A[sk init]
    Start -->|Existing| A2[sk adopt]
    A --> B[Choose Template & Quality Tier]
    A2 --> B2[Choose Quality Tier]
    B --> C[sk work-new]
    B2 --> C
    C --> D[Write Spec]
    D --> E[sk start]
    E --> F[Develop with Claude]
    F --> G{More Changes?}
    G -->|Yes| F
    G -->|No| H[sk validate]
    H --> I{Gates Pass?}
    I -->|No| J[Fix Issues]
    J --> F
    I -->|Yes| K[sk end]
    K --> L{More Work?}
    L -->|Yes| C
    L -->|No| M[Done!]
```

## Installation

### Prerequisites

**Required:**
- **Python 3.11+** - Core runtime
- **pip/pip3** - Package installer (see OS-specific notes below)
- **Git** - Version control
- **Claude Code** - *Strongly recommended* for slash command integration and optimal workflow experience. While Solokit can be used via CLI alone, Claude Code provides the richest experience with interactive prompts, context continuity, and intelligent assistance.

**OS-Specific Requirements:**

**macOS:**
- Use `pip3` instead of `pip` on fresh installations
- **Command Line Tools** - macOS will prompt you to install these automatically when you first run `pip3` (5-10 minute installation, completely normal)
- **PATH Setup** - You may need to add the install location to your PATH (see Troubleshooting below)

**Windows:**
- Use `py -m pip` instead of `pip` for reliable installation
- Ensure Python is added to PATH during Python installation

**Linux:**
- Use `pip3` for Python 3.x installations
- May need to install `python3-pip` package first: `sudo apt install python3-pip` (Debian/Ubuntu) or `sudo dnf install python3-pip` (Fedora/RHEL)

**Optional Tools** (for quality gates):
- Testing: `pytest` (Python), `jest` (JS/TS)
- Linting: `ruff` (Python), `eslint` (JS/TS)
- Formatting: `prettier` (JS/TS)
- Security: `bandit`, `safety` (Python), `npm audit` (JS)
- Visualization: `graphviz` (dependency graphs)

Quality gates gracefully skip when tools aren't available.

### Option 1: PyPI (Recommended)

```bash
# macOS/Linux
pip3 install solokit

# Windows
py -m pip install solokit
```

**Post-Installation (macOS):**

If you see a warning that `sk` is not on PATH, add it to your shell configuration:

```bash
# For zsh (default on modern macOS)
echo 'export PATH="$HOME/Library/Python/3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export PATH="$HOME/Library/Python/3.11/bin:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

> **Note:** Adjust the Python version (3.11) to match your installed version if different.

### Option 2: From Source

```bash
git clone https://github.com/ankushdixit/solokit.git
cd solokit

# macOS/Linux
pip3 install -e .

# Windows
py -m pip install -e .
```

### Verify Installation

```bash
sk status
```

If `sk` command is not found, see the Troubleshooting section below.

## Troubleshooting

### Common Installation Issues

#### "command not found: sk"

**macOS/Linux:**
The `sk` command is installed in your Python user bin directory, which may not be on your PATH.

**Solution:**
```bash
# Find where sk is installed
pip3 show solokit

# Add to PATH (example for macOS with zsh)
echo 'export PATH="$HOME/Library/Python/3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify
sk status
```

**Windows:**
```powershell
# Add Python Scripts to PATH
# Go to System Properties > Environment Variables
# Add: C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\Scripts
```

#### "command not found: pip" (macOS)

**Problem:** Fresh macOS installations only have `pip3`, not `pip`.

**Solution:** Use `pip3` instead:
```bash
pip3 install solokit
```

#### "xcode-select: note: No developer tools were found"

**This is normal on fresh macOS!** When you run `pip3` for the first time, macOS needs to install Command Line Tools.

**Solution:**
- Click "Install" when prompted
- Wait 5-10 minutes for the installation to complete
- Then retry: `pip3 install solokit`

#### "WARNING: You are using pip version X.X.X"

**This warning is safe to ignore.** Solokit works with older pip versions. If you want to update pip:

```bash
# macOS/Linux
pip3 install --upgrade pip

# Windows
py -m pip install --upgrade pip
```

#### Python Version Issues

**Problem:** Solokit requires Python 3.11 or higher.

**Check your Python version:**
```bash
python3 --version
```

**Solution:** If you have an older version, install Python 3.11+ from [python.org](https://www.python.org/downloads/)

#### Permission Errors on Linux

**Problem:** `Permission denied` when installing packages.

**Solution:** Use `--user` flag to install in your user directory:
```bash
pip3 install --user solokit
```

Or use a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install solokit
```

### Getting Help

If you encounter issues not covered here:

1. **Check existing issues:** [GitHub Issues](https://github.com/ankushdixit/solokit/issues)
2. **Run diagnostics:** `sk doctor` (after installation)
3. **Open a new issue:** Include:
   - Operating system and version
   - Python version (`python3 --version`)
   - Error message (full output)
   - Steps to reproduce

## Configuration

Configure Solokit via `.session/config.json` (created during `sk init`):

```json
{
  "quality_gates": {
    "tests": {
      "enabled": true,
      "required": true,
      "coverage_threshold": 80
    },
    "linting": {
      "enabled": true,
      "required": false,
      "auto_fix": true
    },
    "formatting": {
      "enabled": true,
      "required": false,
      "auto_fix": true
    },
    "security": {
      "enabled": true,
      "required": true,
      "fail_on": "high"
    },
    "documentation": {
      "enabled": true,
      "required": false
    }
  },
  "learning_curation": {
    "auto_curate": true,
    "frequency": 5
  },
  "git": {
    "auto_push": true,
    "auto_merge": false
  }
}
```

**Quality Gate Options:**
- `enabled` - Run this gate
- `required` - Block `sk end` if fails
- `auto_fix` - Automatically fix issues (linting/formatting)
- `coverage_threshold` - Minimum test coverage percentage
- `fail_on` - Security threshold (critical, high, medium, low)

**Learning Curation:**
- `auto_curate` - Automatically run curation
- `frequency` - Run every N sessions

**Git Integration:**
- `auto_push` - Automatically push after `sk end`
- `auto_merge` - Automatically merge branch if work complete

## Documentation

- **[Documentation Index](docs/README.md)** - Complete documentation navigation
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System architecture
- **[Solokit Methodology](docs/architecture/solokit-methodology.md)** - Complete framework specification
- **[AI-Augmented Solo Framework](docs/architecture/ai-augmented-solo-framework.md)** - Philosophical context
- **[Learning System Guide](docs/reference/learning-system.md)** - Knowledge capture details
- **[Configuration Guide](docs/guides/configuration.md)** - Configuration options
- **[Writing Specs](docs/guides/writing-specs.md)** - Spec-first best practices
- **[Troubleshooting](docs/guides/troubleshooting.md)** - Common issues

## Project Structure

```
solokit/
├── .claude/                  # Claude Code integration
│   └── commands/             # 16 slash commands (/sk:init, /sk:start, etc.)
├── src/solokit/              # Python package (standard src/ layout)
│   ├── cli.py                # CLI entry point (sk command)
│   ├── core/                 # Core functionality
│   ├── session/              # Session management
│   ├── work_items/           # Work item CRUD and specs
│   ├── learning/             # Learning capture & curation
│   ├── quality/              # Quality gates
│   ├── visualization/        # Dependency graphs
│   ├── git/                  # Git integration
│   ├── testing/              # Testing utilities
│   ├── deployment/           # Deployment execution
│   ├── project/              # Project initialization
│   └── templates/            # Project templates & work item specs
├── docs/                     # Comprehensive documentation
├── tests/                    # 3,802 tests (100% passing, 97% coverage)
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── README.md                 # This file
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
└── pyproject.toml            # Package configuration (PEP 517/518)
```

## Why Solokit?

### vs. Project Management Tools (Linear, Jira)
- ✅ **AI-native design** - Built for Claude Code, not bolted on
- ✅ **Context continuity** - Perfect AI briefings, not manual updates
- ✅ **Quality enforcement** - Automated gates, not manual reviews
- ✅ **Knowledge capture** - AI-powered, not manual documentation

### vs. AI Coding Tools (Cursor, Copilot)
- ✅ **Complete framework** - Templates + workflow + quality + learning
- ✅ **Production-ready** - Not just code completion
- ✅ **Process rigor** - Systematic workflow, not ad-hoc
- ✅ **Knowledge accumulation** - Learnings persist and grow

### vs. Project Templates (Cookiecutter)
- ✅ **Ongoing workflow** - Not just initial setup
- ✅ **Minimal scaffolding** - Comprehensive docs, not example code
- ✅ **PRD-driven** - Build from your requirements, not template assumptions
- ✅ **Quality enforcement** - Automated validation throughout
- ✅ **Session management** - Perfect context across all work
- ✅ **4 quality tiers** - From MVP to enterprise

### vs. Using Claude Code Standalone
While Claude Code is excellent for code generation and exploration, Solokit adds:
- ✅ **Workflow structure** - Session-driven development with clear start/end boundaries
- ✅ **Quality enforcement** - Automated gates ensure testing, linting, and security standards
- ✅ **Learning capture** - Systematic knowledge accumulation across sessions
- ✅ **Work item management** - Organize and track progress on multiple features/bugs
- ✅ **Minimal scaffolding** - Battle-tested configurations with comprehensive docs
- ✅ **Spec-first architecture** - Clear requirements before implementation

**Solokit is the only tool that combines:**
- Minimal scaffolding templates with comprehensive documentation
- PRD-driven development workflow
- AI-native session management with perfect context
- Automated quality enforcement throughout development
- AI-powered knowledge capture and curation
- Dependency-driven, spec-first workflow

## Development Status

**Current Version:** v0.2.0 (Production-Ready)

**Test Coverage:** 3,802 tests passing (100%), 97% code coverage

### Completed Features

| Feature | Status |
|---------|--------|
| Core Session Management | ✅ Complete |
| Work Item System | ✅ Complete |
| Dependency Visualization | ✅ Complete |
| Learning Management | ✅ Complete |
| Quality Gates | ✅ Complete |
| Spec-First Architecture | ✅ Complete |
| Minimal Scaffolding Templates (4 stacks) | ✅ Complete |
| Quality Tiers (4 levels) | ✅ Complete |
| Claude Code Integration | ✅ Complete |

See [CHANGELOG.md](./CHANGELOG.md) for detailed release history.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

```bash
# Clone and install
git clone https://github.com/ankushdixit/solokit.git
cd solokit
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run quality checks
ruff check src/solokit/ tests/
ruff format src/solokit/ tests/
mypy src/solokit
```

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Credits

Built for solo developers building production software with AI assistance.

Inspired by professional software development practices adapted for AI-augmented solo development.

---

**Solo doesn't mean shortcuts. Build with team-level sophistication.**

🌐 [getsolokit.com](https://getsolokit.com) | 📦 [PyPI](https://pypi.org/project/solokit/) | 🐙 [GitHub](https://github.com/ankushdixit/solokit)
