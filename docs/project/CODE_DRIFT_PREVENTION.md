# Code Drift Prevention: Comprehensive Strategy

**Status:** RESEARCH & DESIGN
**Priority:** High
**Last Updated:** 2025-12-27

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Current State Analysis](#current-state-analysis)
3. [Proposed Solution: Two-Layer Architecture](#proposed-solution-two-layer-architecture)
4. [Layer 1: Deterministic Enforcement](#layer-1-deterministic-enforcement)
   - [Convention Manifest System](#1-convention-manifest-system)
   - [Architecture Tests](#2-architecture-tests)
   - [Custom Lint Rules](#3-custom-lint-rules)
   - [Import/Dependency Rules](#4-importdependency-rules)
   - [Code Pattern Templates](#5-code-pattern-templates)
   - [Convention Drift Detection](#6-convention-drift-detection)
5. [Layer 2: AI-Enhanced Enforcement](#layer-2-ai-enhanced-enforcement)
6. [Integration with Solokit](#integration-with-solokit)
7. [Implementation Roadmap](#implementation-roadmap)
8. [References](#references)

---

## Problem Statement

### The Challenge

When working on large projects with 20-30+ work items (stories), **code drift** occurs:

- Early stories establish patterns and conventions
- Over time, these patterns are forgotten or misremembered
- New code introduces variations and inconsistencies
- The codebase becomes a patchwork of different approaches
- Technical debt accumulates silently

### Why This Happens

1. **Context Loss Between Sessions**: Each new session starts with limited context about original decisions
2. **Advisory vs. Enforced Conventions**: Learnings and CLAUDE.md provide guidance but don't enforce
3. **Semantic Drift**: Small variations compound over time
4. **No Baseline Comparison**: No way to compare current code against established patterns
5. **Manual Capture**: Conventions only documented when explicitly captured

### Impact

| Symptom | Example |
|---------|---------|
| Inconsistent API responses | Some endpoints return `{data, error}`, others return `{result, message}` |
| Mixed error handling | Some files use try/catch, others use Result types |
| Variable naming drift | `userId`, `user_id`, `userID` used interchangeably |
| Architecture violations | Controllers directly accessing repositories |
| Design token violations | Hardcoded colors instead of theme variables |

---

## Current State Analysis

### Existing Solokit Mechanisms

Solokit already provides **8 layers of consistency mechanisms**:

| Layer | Mechanism | Enforcement Level |
|-------|-----------|-------------------|
| Spec-First | `.session/specs/*.md` | **Strong** - Validated before sessions |
| Context Restoration | Session briefings | **Medium** - Advisory context |
| Learning System | 215+ captured learnings | **Weak** - Keyword-based retrieval |
| Quality Gates | Tests, linting, security | **Strong** - Blocks on failure |
| Work Tracking | `work_items.json` | **Strong** - Complete audit trail |
| CLAUDE.md | Stack-specific guidance | **Weak** - Advisory only |
| Config as Code | `.session/config.json` | **Strong** - Version-controlled |
| Git Integration | Auto-branching | **Strong** - Enforced workflow |

### Gaps Identified

1. **Quality gates check syntax, not semantics** - Linting catches style violations but not "we always do X this way"
2. **Learnings are advisory** - AI sees them but can choose different approaches
3. **No convention drift detection** - No comparison between early vs. recent code
4. **No architecture enforcement** - Layer violations not caught
5. **No project-specific rules** - Only generic lint rules apply

---

## Proposed Solution: Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CODE DRIFT PREVENTION ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 1: DETERMINISTIC                            │   │
│  │                    (Always Enforced, No AI)                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • Convention Manifest → Machine-readable rules                     │   │
│  │  • Architecture Tests → Layer/dependency validation                  │   │
│  │  • Custom Lint Rules → Project-specific ESLint/Ruff                 │   │
│  │  • Import Rules → dependency-cruiser, import-linter                 │   │
│  │  • Pattern Templates → Code generators                              │   │
│  │  • Drift Detection → Baseline comparison                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    LAYER 2: AI-ENHANCED                              │   │
│  │                    (Semantic Understanding)                          │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  • #29: Frontend Quality & Design System Compliance                  │   │
│  │  • #30: Documentation-Driven Development (Architecture Validation)  │   │
│  │  • #31: AI-Enhanced Learning System (Semantic Relevance)            │   │
│  │  • #39: Automated Code Review                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Principle**: Deterministic enforcement provides the foundation; AI enhancement adds semantic understanding on top.

---

## Layer 1: Deterministic Enforcement

### 1. Convention Manifest System

**Purpose**: Machine-readable conventions that quality gates can check automatically.

#### Design

```yaml
# .session/conventions.yaml
version: "1.0"
project: "my-project"

# API conventions
api:
  response_format:
    required_fields: ["success", "data", "error"]
    success_type: "boolean"
    pattern: |
      {
        success: boolean,
        data: T | null,
        error: { code: string, message: string } | null
      }

  error_codes:
    prefix: "ERR_"
    format: "ERR_{DOMAIN}_{SPECIFIC}"
    examples: ["ERR_AUTH_INVALID_TOKEN", "ERR_USER_NOT_FOUND"]

  http_status:
    success_create: 201
    success_update: 200
    success_delete: 204
    client_error: 400
    unauthorized: 401
    not_found: 404
    server_error: 500

# Naming conventions
naming:
  files:
    components: "PascalCase"    # Button.tsx, UserProfile.tsx
    hooks: "camelCase"          # useAuth.ts, useUser.ts
    utils: "camelCase"          # formatDate.ts, parseUrl.ts
    types: "PascalCase"         # User.types.ts, ApiResponse.types.ts
    tests: "{name}.test.ts"     # Button.test.tsx

  code:
    variables: "camelCase"
    constants: "SCREAMING_SNAKE_CASE"
    classes: "PascalCase"
    interfaces: "PascalCase"    # No "I" prefix
    types: "PascalCase"
    enums: "PascalCase"
    enum_values: "SCREAMING_SNAKE_CASE"

# Architecture layers
architecture:
  layers:
    - name: "presentation"
      paths: ["src/components/**", "src/pages/**"]
      can_import: ["domain", "infrastructure"]
      cannot_import: ["data"]

    - name: "domain"
      paths: ["src/domain/**", "src/hooks/**"]
      can_import: ["infrastructure"]
      cannot_import: ["presentation", "data"]

    - name: "data"
      paths: ["src/repositories/**", "src/api/**"]
      can_import: ["infrastructure"]
      cannot_import: ["presentation", "domain"]

    - name: "infrastructure"
      paths: ["src/lib/**", "src/utils/**"]
      can_import: []
      cannot_import: ["presentation", "domain", "data"]

# Code patterns
patterns:
  error_handling:
    strategy: "result-type"  # or "try-catch", "either"
    examples:
      - file: "src/domain/user/createUser.ts"
        lines: [15, 45]

  validation:
    library: "zod"
    location: "src/schemas/**"
    naming: "{Entity}Schema.ts"

  logging:
    library: "pino"
    levels: ["debug", "info", "warn", "error"]
    structured: true
    required_fields: ["timestamp", "level", "message", "context"]

# Design tokens (for frontend)
design_tokens:
  colors:
    source: "src/styles/tokens.ts"
    forbidden_patterns:
      - "#[0-9a-fA-F]{3,6}"  # No hardcoded hex
      - "rgb\\([^)]+\\)"     # No hardcoded rgb
      - "rgba\\([^)]+\\)"    # No hardcoded rgba
    allowed_exceptions:
      - "transparent"
      - "inherit"
      - "currentColor"

  spacing:
    scale: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96]
    unit: "px"
    forbidden_patterns:
      - "\\d+px"  # Catch any pixel value not in scale

  typography:
    source: "src/styles/typography.ts"
    sizes: [12, 14, 16, 18, 20, 24, 30, 36, 48, 60]

# Test conventions
testing:
  coverage:
    minimum: 80
    critical_paths: 95
  naming:
    describe_format: "{ComponentName}"
    it_format: "should {expected behavior} when {condition}"
  structure:
    arrange_act_assert: true
    one_assertion_per_test: false
```

#### Validation Implementation

```python
# src/solokit/quality/convention_validator.py
from pathlib import Path
from typing import Dict, List, Any
import yaml
import re

class ConventionValidator:
    """Validate code against project conventions"""

    def __init__(self, manifest_path: Path = None):
        self.manifest_path = manifest_path or Path(".session/conventions.yaml")
        self.manifest = self._load_manifest()
        self.violations = []

    def _load_manifest(self) -> Dict[str, Any]:
        """Load convention manifest"""
        if not self.manifest_path.exists():
            return {}
        with open(self.manifest_path) as f:
            return yaml.safe_load(f)

    def validate_all(self) -> Dict[str, Any]:
        """Run all convention validations"""
        results = {
            "passed": True,
            "violations": [],
            "checks": {}
        }

        # Naming conventions
        naming_result = self.validate_naming()
        results["checks"]["naming"] = naming_result
        if not naming_result["passed"]:
            results["passed"] = False
            results["violations"].extend(naming_result["violations"])

        # API conventions
        api_result = self.validate_api_patterns()
        results["checks"]["api"] = api_result
        if not api_result["passed"]:
            results["passed"] = False
            results["violations"].extend(api_result["violations"])

        # Design tokens
        tokens_result = self.validate_design_tokens()
        results["checks"]["design_tokens"] = tokens_result
        if not tokens_result["passed"]:
            results["passed"] = False
            results["violations"].extend(tokens_result["violations"])

        return results

    def validate_naming(self) -> Dict[str, Any]:
        """Validate file and code naming conventions"""
        violations = []
        naming = self.manifest.get("naming", {})

        # Validate file naming
        for category, pattern in naming.get("files", {}).items():
            files = self._get_files_for_category(category)
            for file in files:
                if not self._matches_case_pattern(file.stem, pattern):
                    violations.append({
                        "type": "naming",
                        "file": str(file),
                        "expected": pattern,
                        "actual": file.stem,
                        "message": f"File '{file.name}' should use {pattern} naming"
                    })

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

    def validate_api_patterns(self) -> Dict[str, Any]:
        """Validate API response patterns"""
        violations = []
        api = self.manifest.get("api", {})
        response_format = api.get("response_format", {})

        if not response_format:
            return {"passed": True, "violations": []}

        required_fields = response_format.get("required_fields", [])

        # Scan API files for response patterns
        api_files = list(Path("src").rglob("**/api/**/*.ts")) + \
                   list(Path("src").rglob("**/routes/**/*.ts"))

        for file in api_files:
            content = file.read_text()
            # Check for response objects missing required fields
            # This is simplified - production would use AST parsing
            if "return {" in content or "return{" in content:
                for field in required_fields:
                    if field not in content:
                        violations.append({
                            "type": "api_response",
                            "file": str(file),
                            "message": f"API response may be missing required field: {field}"
                        })

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

    def validate_design_tokens(self) -> Dict[str, Any]:
        """Validate design token usage"""
        violations = []
        tokens = self.manifest.get("design_tokens", {})

        if not tokens:
            return {"passed": True, "violations": []}

        # Check colors
        color_patterns = tokens.get("colors", {}).get("forbidden_patterns", [])
        allowed_exceptions = tokens.get("colors", {}).get("allowed_exceptions", [])

        frontend_files = list(Path("src").rglob("*.tsx")) + \
                        list(Path("src").rglob("*.css")) + \
                        list(Path("src").rglob("*.scss"))

        for file in frontend_files:
            content = file.read_text()
            for pattern in color_patterns:
                for match in re.finditer(pattern, content):
                    matched_value = match.group(0)
                    if matched_value not in allowed_exceptions:
                        line_num = content[:match.start()].count('\n') + 1
                        violations.append({
                            "type": "design_token",
                            "file": str(file),
                            "line": line_num,
                            "value": matched_value,
                            "message": f"Hardcoded color value. Use design token instead."
                        })

        return {
            "passed": len(violations) == 0,
            "violations": violations
        }

    def _get_files_for_category(self, category: str) -> List[Path]:
        """Get files for a naming category"""
        category_paths = {
            "components": ["src/components/**/*.tsx", "src/components/**/*.jsx"],
            "hooks": ["src/hooks/**/*.ts"],
            "utils": ["src/utils/**/*.ts", "src/lib/**/*.ts"],
            "types": ["src/types/**/*.ts", "src/**/*.types.ts"],
            "tests": ["**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts"]
        }

        patterns = category_paths.get(category, [])
        files = []
        for pattern in patterns:
            files.extend(Path(".").glob(pattern))
        return files

    def _matches_case_pattern(self, name: str, pattern: str) -> bool:
        """Check if name matches case pattern"""
        if pattern == "PascalCase":
            return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))
        elif pattern == "camelCase":
            return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name))
        elif pattern == "kebab-case":
            return bool(re.match(r'^[a-z][a-z0-9-]*$', name))
        elif pattern == "snake_case":
            return bool(re.match(r'^[a-z][a-z0-9_]*$', name))
        elif pattern == "SCREAMING_SNAKE_CASE":
            return bool(re.match(r'^[A-Z][A-Z0-9_]*$', name))
        return True
```

#### CLI Integration

```bash
# Validate conventions
sk validate --conventions

# Generate convention manifest from existing code
sk conventions --init

# Show convention compliance report
sk conventions --report

# Auto-fix where possible
sk conventions --fix
```

---

### 2. Architecture Tests

**Purpose**: Enforce architectural boundaries as executable tests that run with the test suite.

#### TypeScript: Using ts-arch

```typescript
// tests/architecture/architecture.test.ts
import { filesOfProject } from "ts-arch";

describe("Architecture Rules", () => {
  // Rule 1: Presentation layer cannot import from data layer
  it("presentation should not import from data layer", async () => {
    const rule = filesOfProject()
      .inFolder("src/components")
      .shouldNot()
      .dependOnFiles()
      .inFolder("src/repositories");

    await expect(rule).toPassAsync();
  });

  // Rule 2: Domain layer is independent
  it("domain should not import from presentation", async () => {
    const rule = filesOfProject()
      .inFolder("src/domain")
      .shouldNot()
      .dependOnFiles()
      .inFolder("src/components");

    await expect(rule).toPassAsync();
  });

  // Rule 3: No circular dependencies
  it("should have no circular dependencies", async () => {
    const rule = filesOfProject()
      .inFolder("src")
      .shouldNot()
      .haveCyclicDependencies();

    await expect(rule).toPassAsync();
  });

  // Rule 4: Services should be named correctly
  it("services should have Service suffix", async () => {
    const rule = filesOfProject()
      .inFolder("src/services")
      .should()
      .matchPattern(".*Service\\.ts$");

    await expect(rule).toPassAsync();
  });

  // Rule 5: Hooks must start with 'use'
  it("hooks should start with 'use'", async () => {
    const rule = filesOfProject()
      .inFolder("src/hooks")
      .should()
      .matchPattern("use[A-Z].*\\.ts$");

    await expect(rule).toPassAsync();
  });

  // Rule 6: API routes should not import React
  it("API routes should not use React", async () => {
    const rule = filesOfProject()
      .inFolder("src/app/api")
      .shouldNot()
      .dependOnFiles()
      .matchingPattern(".*react.*");

    await expect(rule).toPassAsync();
  });
});
```

#### Python: Using import-linter

```ini
# setup.cfg or pyproject.toml
[importlinter]
root_package = src
include_external_packages = True

[importlinter:contract:layers]
name = Layered Architecture
type = layers
layers =
    presentation
    application
    domain
    infrastructure

containers =
    src

[importlinter:contract:domain-independence]
name = Domain Independence
type = independence
modules =
    src.domain.user
    src.domain.order
    src.domain.product

[importlinter:contract:no-orm-in-domain]
name = No ORM in Domain Layer
type = forbidden
source_modules =
    src.domain
forbidden_modules =
    sqlalchemy
    prisma
    peewee
```

```python
# tests/architecture/test_architecture.py
import pytest
from importlinter import api

class TestArchitecture:
    """Architecture constraint tests"""

    def test_layer_dependencies(self):
        """Verify layer dependencies are respected"""
        result = api.read_graph("src")

        # Presentation can import from application and domain
        # Application can import from domain
        # Domain cannot import from any other layer
        # Infrastructure can be imported by all

        contract = api.get_contract("layers")
        assert contract.check_contract(result).kept

    def test_domain_independence(self):
        """Verify domain modules are independent"""
        contract = api.get_contract("domain-independence")
        result = api.read_graph("src")
        assert contract.check_contract(result).kept

    def test_no_orm_in_domain(self):
        """Verify domain layer has no ORM dependencies"""
        contract = api.get_contract("no-orm-in-domain")
        result = api.read_graph("src")
        assert contract.check_contract(result).kept
```

#### Alternative: pytest-arch

```python
# tests/architecture/test_layers.py
from pytest_arch import archrule

def test_controllers_use_services():
    """Controllers should only use services, not repositories directly"""
    archrule(
        "Controllers should depend on services"
    ).match(
        "src/controllers/*"
    ).should_import(
        "src/services/*"
    ).should_not_import(
        "src/repositories/*"
    ).check()

def test_services_use_repositories():
    """Services should use repositories for data access"""
    archrule(
        "Services should depend on repositories"
    ).match(
        "src/services/*"
    ).may_import(
        "src/repositories/*"
    ).should_not_import(
        "src/controllers/*"
    ).check()
```

---

### 3. Custom Lint Rules

**Purpose**: Encode project-specific conventions as lint rules that fail CI.

#### ESLint: Project-Specific Rules

```javascript
// eslint-local-rules/index.js
module.exports = {
  "api-response-format": {
    meta: {
      type: "problem",
      docs: {
        description: "Enforce API response format convention"
      },
      schema: []
    },
    create(context) {
      return {
        ReturnStatement(node) {
          if (!isInApiRoute(context)) return;

          if (node.argument?.type === "ObjectExpression") {
            const props = node.argument.properties.map(p => p.key?.name);
            const required = ["success", "data", "error"];

            for (const field of required) {
              if (!props.includes(field)) {
                context.report({
                  node,
                  message: `API response missing required field: ${field}. ` +
                           `Expected format: { success, data, error }`
                });
              }
            }
          }
        }
      };
    }
  },

  "no-hardcoded-colors": {
    meta: {
      type: "problem",
      docs: {
        description: "Prevent hardcoded color values in styles"
      }
    },
    create(context) {
      const hexPattern = /#[0-9a-fA-F]{3,6}\b/;
      const rgbPattern = /rgba?\([^)]+\)/;

      return {
        Literal(node) {
          if (typeof node.value !== "string") return;

          if (hexPattern.test(node.value) || rgbPattern.test(node.value)) {
            context.report({
              node,
              message: "Use design token instead of hardcoded color: " +
                       "e.g., colors.primary instead of '${node.value}'"
            });
          }
        }
      };
    }
  },

  "use-result-type-for-errors": {
    meta: {
      type: "suggestion",
      docs: {
        description: "Prefer Result type over try/catch for domain logic"
      }
    },
    create(context) {
      return {
        TryStatement(node) {
          if (isInDomainLayer(context)) {
            context.report({
              node,
              message: "Use Result<T, E> type instead of try/catch in domain layer. " +
                       "Import from '@/lib/result'"
            });
          }
        }
      };
    }
  },

  "consistent-error-codes": {
    meta: {
      type: "problem",
      docs: {
        description: "Enforce error code naming convention"
      }
    },
    create(context) {
      const pattern = /^ERR_[A-Z]+_[A-Z_]+$/;

      return {
        Property(node) {
          if (node.key?.name === "code" &&
              node.value?.type === "Literal" &&
              typeof node.value.value === "string") {

            if (!pattern.test(node.value.value)) {
              context.report({
                node,
                message: `Error code should follow pattern ERR_{DOMAIN}_{SPECIFIC}. ` +
                         `Got: ${node.value.value}`
              });
            }
          }
        }
      };
    }
  }
};

function isInApiRoute(context) {
  return context.getFilename().includes("/api/") ||
         context.getFilename().includes("/routes/");
}

function isInDomainLayer(context) {
  return context.getFilename().includes("/domain/") ||
         context.getFilename().includes("/services/");
}
```

#### ESLint Configuration

```javascript
// eslint.config.js
import localRules from "./eslint-local-rules/index.js";
import boundaries from "eslint-plugin-boundaries";

export default [
  {
    plugins: {
      "local": { rules: localRules },
      "boundaries": boundaries
    },
    rules: {
      // Project-specific rules
      "local/api-response-format": "error",
      "local/no-hardcoded-colors": "error",
      "local/use-result-type-for-errors": "warn",
      "local/consistent-error-codes": "error",

      // Architecture boundaries
      "boundaries/element-types": [
        "error",
        {
          default: "disallow",
          rules: [
            {
              from: "components",
              allow: ["hooks", "utils", "types", "services"]
            },
            {
              from: "services",
              allow: ["repositories", "utils", "types"]
            },
            {
              from: "repositories",
              allow: ["utils", "types"]
            }
          ]
        }
      ]
    }
  }
];
```

#### Ruff Configuration (Python)

While Ruff doesn't support custom rules, it offers extensive configuration:

```toml
# pyproject.toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate (commented-out code)
    "PL",     # Pylint
    "RUF",    # Ruff-specific rules
    "ANN",    # flake8-annotations
    "S",      # flake8-bandit (security)
    "N",      # pep8-naming
]

ignore = [
    "ANN101",  # Missing type annotation for self
    "ANN102",  # Missing type annotation for cls
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN"]  # Allow assert and skip type hints in tests
"**/__init__.py" = ["F401"]  # Allow unused imports in __init__.py

[tool.ruff.lint.isort]
known-first-party = ["src", "app"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[tool.ruff.lint.pep8-naming]
classmethod-decorators = ["classmethod", "validator", "root_validator"]

[tool.ruff.lint.pylint]
max-args = 5
max-branches = 12
max-returns = 6
max-statements = 50
```

---

### 4. Import/Dependency Rules

**Purpose**: Enforce module boundaries and prevent architectural violations at the import level.

#### dependency-cruiser (JavaScript/TypeScript)

```javascript
// .dependency-cruiser.js
module.exports = {
  forbidden: [
    // Rule 1: No circular dependencies
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: {
        circular: true
      }
    },

    // Rule 2: Components cannot import from API routes
    {
      name: "no-components-to-api",
      severity: "error",
      comment: "Components should use hooks/services, not direct API calls",
      from: {
        path: "^src/components"
      },
      to: {
        path: "^src/app/api"
      }
    },

    // Rule 3: API routes cannot import React
    {
      name: "no-react-in-api",
      severity: "error",
      comment: "API routes are server-side only",
      from: {
        path: "^src/app/api"
      },
      to: {
        path: "react"
      }
    },

    // Rule 4: Domain layer is framework-agnostic
    {
      name: "domain-framework-agnostic",
      severity: "error",
      comment: "Domain layer should not depend on frameworks",
      from: {
        path: "^src/domain"
      },
      to: {
        path: "(react|next|express|fastify)"
      }
    },

    // Rule 5: No orphan files
    {
      name: "no-orphans",
      severity: "warn",
      from: {
        orphan: true,
        pathNot: [
          "\\.d\\.ts$",
          "\\.test\\.tsx?$",
          "\\.spec\\.tsx?$",
          "^src/app/.*page\\.tsx$",
          "^src/app/.*layout\\.tsx$"
        ]
      },
      to: {}
    },

    // Rule 6: Repositories only in data layer
    {
      name: "repositories-isolation",
      severity: "error",
      from: {
        pathNot: "^src/(repositories|data)"
      },
      to: {
        path: "^src/repositories"
      }
    }
  ],

  allowed: [
    // Shared utilities can be imported anywhere
    {
      from: {},
      to: {
        path: "^src/(utils|lib|types)"
      }
    }
  ],

  options: {
    doNotFollow: {
      path: "node_modules"
    },
    tsPreCompilationDeps: true,
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default"]
    }
  }
};
```

#### npm scripts integration

```json
{
  "scripts": {
    "lint:deps": "depcruise src --config .dependency-cruiser.js",
    "lint:deps:graph": "depcruise src --include-only '^src' --output-type dot | dot -T svg > dependency-graph.svg",
    "lint": "eslint . && npm run lint:deps",
    "precommit": "npm run lint && npm test"
  }
}
```

---

### 5. Code Pattern Templates

**Purpose**: Generate code that automatically follows conventions.

#### Template System Design

```yaml
# .session/templates/index.yaml
templates:
  api-route:
    description: "Create a new API route with standard response format"
    output: "src/app/api/{name}/route.ts"
    prompts:
      - name: "name"
        message: "Route name (e.g., users, products)"
      - name: "methods"
        message: "HTTP methods"
        type: "multiselect"
        choices: ["GET", "POST", "PUT", "DELETE", "PATCH"]

  component:
    description: "Create a React component following conventions"
    output: "src/components/{Name}/{Name}.tsx"
    additional_files:
      - "src/components/{Name}/{Name}.test.tsx"
      - "src/components/{Name}/index.ts"

  service:
    description: "Create a service class"
    output: "src/services/{Name}Service.ts"
    additional_files:
      - "src/services/{Name}Service.test.ts"

  hook:
    description: "Create a custom React hook"
    output: "src/hooks/use{Name}.ts"
    additional_files:
      - "src/hooks/use{Name}.test.ts"
```

#### API Route Template

```typescript
// .session/templates/api-route/route.ts.template
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { ApiResponse, createSuccessResponse, createErrorResponse } from "@/lib/api";
import { {{Name}}Service } from "@/services/{{Name}}Service";

// Request validation schemas
const Get{{Name}}Schema = z.object({
  id: z.string().uuid().optional(),
});

const Create{{Name}}Schema = z.object({
  // Define your schema here
});

const service = new {{Name}}Service();

{{#if hasGet}}
export async function GET(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const { searchParams } = new URL(request.url);
    const params = Get{{Name}}Schema.parse(Object.fromEntries(searchParams));

    const result = await service.get(params);

    if (result.isErr()) {
      return NextResponse.json(
        createErrorResponse(result.error.code, result.error.message),
        { status: 400 }
      );
    }

    return NextResponse.json(createSuccessResponse(result.value));
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        createErrorResponse("ERR_VALIDATION_FAILED", error.message),
        { status: 400 }
      );
    }

    return NextResponse.json(
      createErrorResponse("ERR_INTERNAL_SERVER", "An unexpected error occurred"),
      { status: 500 }
    );
  }
}
{{/if}}

{{#if hasPost}}
export async function POST(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const body = await request.json();
    const data = Create{{Name}}Schema.parse(body);

    const result = await service.create(data);

    if (result.isErr()) {
      return NextResponse.json(
        createErrorResponse(result.error.code, result.error.message),
        { status: 400 }
      );
    }

    return NextResponse.json(
      createSuccessResponse(result.value),
      { status: 201 }
    );
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        createErrorResponse("ERR_VALIDATION_FAILED", error.message),
        { status: 400 }
      );
    }

    return NextResponse.json(
      createErrorResponse("ERR_INTERNAL_SERVER", "An unexpected error occurred"),
      { status: 500 }
    );
  }
}
{{/if}}
```

#### CLI Commands

```bash
# Generate new code from templates
sk generate api-route --name users --methods GET,POST
sk generate component --name UserProfile
sk generate service --name Authentication
sk generate hook --name Auth

# List available templates
sk generate --list

# Create custom template
sk generate:template --name my-pattern
```

---

### 6. Convention Drift Detection

**Purpose**: Detect when recent code deviates from established patterns.

#### Design

```python
# src/solokit/quality/drift_detector.py
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter
import re
from datetime import datetime, timedelta

class ConventionDriftDetector:
    """Detect convention drift between early and recent code"""

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(".")
        self.baseline_sessions = 5  # First N sessions establish baseline

    def analyze_drift(self) -> Dict[str, Any]:
        """Analyze convention drift across the codebase"""
        # Get files by age (using git history)
        early_files = self._get_files_from_sessions(0, self.baseline_sessions)
        recent_files = self._get_files_from_sessions(-5, None)  # Last 5 sessions

        results = {
            "analyzed_at": datetime.now().isoformat(),
            "baseline_sessions": self.baseline_sessions,
            "patterns": {}
        }

        # Analyze different pattern categories
        patterns = [
            ("error_handling", self._analyze_error_handling),
            ("api_responses", self._analyze_api_responses),
            ("naming", self._analyze_naming),
            ("imports", self._analyze_imports),
            ("typing", self._analyze_typing),
        ]

        for pattern_name, analyzer in patterns:
            early_patterns = analyzer(early_files)
            recent_patterns = analyzer(recent_files)

            consistency = self._calculate_consistency(early_patterns, recent_patterns)

            results["patterns"][pattern_name] = {
                "baseline": early_patterns,
                "current": recent_patterns,
                "consistency_score": consistency,
                "status": "consistent" if consistency > 0.8 else
                         "drifting" if consistency > 0.5 else "diverged",
                "recommendations": self._get_recommendations(
                    pattern_name, early_patterns, recent_patterns
                )
            }

        # Overall drift score
        scores = [p["consistency_score"] for p in results["patterns"].values()]
        results["overall_consistency"] = sum(scores) / len(scores) if scores else 1.0
        results["overall_status"] = (
            "healthy" if results["overall_consistency"] > 0.8 else
            "needs_attention" if results["overall_consistency"] > 0.6 else
            "critical"
        )

        return results

    def _analyze_error_handling(self, files: List[Path]) -> Dict[str, float]:
        """Analyze error handling patterns"""
        patterns = Counter()

        for file in files:
            content = file.read_text()

            # Count different error handling patterns
            patterns["try_catch"] += len(re.findall(r'\btry\s*{', content))
            patterns["result_type"] += len(re.findall(r'Result<|\.isOk\(|\.isErr\(', content))
            patterns["throw"] += len(re.findall(r'\bthrow\s+new', content))
            patterns["error_callback"] += len(re.findall(r'\.catch\(|onError', content))

        total = sum(patterns.values())
        if total == 0:
            return {}

        return {k: v / total for k, v in patterns.items()}

    def _analyze_api_responses(self, files: List[Path]) -> Dict[str, float]:
        """Analyze API response format patterns"""
        patterns = Counter()
        api_files = [f for f in files if '/api/' in str(f) or '/routes/' in str(f)]

        for file in api_files:
            content = file.read_text()

            # Check for different response formats
            if re.search(r'success.*:.*true|false', content):
                patterns["success_field"] += 1
            if re.search(r'data.*:', content):
                patterns["data_field"] += 1
            if re.search(r'error.*:', content):
                patterns["error_field"] += 1
            if re.search(r'message.*:', content):
                patterns["message_field"] += 1
            if re.search(r'result.*:', content):
                patterns["result_field"] += 1

        total = sum(patterns.values())
        if total == 0:
            return {}

        return {k: v / total for k, v in patterns.items()}

    def _analyze_naming(self, files: List[Path]) -> Dict[str, float]:
        """Analyze naming convention patterns"""
        patterns = Counter()

        for file in files:
            name = file.stem

            if re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
                patterns["PascalCase"] += 1
            elif re.match(r'^[a-z][a-zA-Z0-9]*$', name):
                patterns["camelCase"] += 1
            elif re.match(r'^[a-z][a-z0-9-]*$', name):
                patterns["kebab-case"] += 1
            elif re.match(r'^[a-z][a-z0-9_]*$', name):
                patterns["snake_case"] += 1

        total = sum(patterns.values())
        if total == 0:
            return {}

        return {k: v / total for k, v in patterns.items()}

    def _analyze_imports(self, files: List[Path]) -> Dict[str, float]:
        """Analyze import organization patterns"""
        patterns = Counter()

        for file in files:
            content = file.read_text()
            imports = re.findall(r'^import\s+.*$', content, re.MULTILINE)

            if not imports:
                continue

            # Check import ordering
            has_groups = self._has_import_groups(imports)
            patterns["grouped_imports"] += 1 if has_groups else 0
            patterns["ungrouped_imports"] += 0 if has_groups else 1

            # Check for type-only imports
            type_imports = len(re.findall(r'import\s+type\s+', content))
            patterns["type_imports"] += 1 if type_imports > 0 else 0

        total = sum(patterns.values())
        if total == 0:
            return {}

        return {k: v / total for k, v in patterns.items()}

    def _analyze_typing(self, files: List[Path]) -> Dict[str, float]:
        """Analyze type annotation patterns"""
        patterns = Counter()
        ts_files = [f for f in files if f.suffix in ['.ts', '.tsx']]

        for file in ts_files:
            content = file.read_text()

            # Check for explicit return types
            functions = re.findall(r'function\s+\w+\([^)]*\)\s*:', content)
            arrow_typed = re.findall(r'=>\s*:', content)

            patterns["explicit_return_types"] += len(functions) + len(arrow_typed)

            # Check for 'any' usage
            patterns["any_usage"] += len(re.findall(r':\s*any\b', content))

            # Check for interface vs type
            patterns["interfaces"] += len(re.findall(r'\binterface\s+', content))
            patterns["type_aliases"] += len(re.findall(r'\btype\s+\w+\s*=', content))

        total = sum(patterns.values())
        if total == 0:
            return {}

        return {k: v / total for k, v in patterns.items()}

    def _calculate_consistency(
        self,
        baseline: Dict[str, float],
        current: Dict[str, float]
    ) -> float:
        """Calculate consistency score between baseline and current patterns"""
        if not baseline or not current:
            return 1.0

        all_keys = set(baseline.keys()) | set(current.keys())
        if not all_keys:
            return 1.0

        differences = []
        for key in all_keys:
            base_val = baseline.get(key, 0)
            curr_val = current.get(key, 0)
            differences.append(abs(base_val - curr_val))

        avg_diff = sum(differences) / len(differences)
        return max(0, 1 - avg_diff)

    def _get_files_from_sessions(
        self,
        start_session: int,
        end_session: int
    ) -> List[Path]:
        """Get files modified in specific session range"""
        # This would use git history to find files
        # Simplified implementation - in production, parse git log
        all_files = list(self.project_root.rglob("src/**/*.ts"))
        all_files.extend(self.project_root.rglob("src/**/*.tsx"))
        all_files.extend(self.project_root.rglob("src/**/*.py"))

        # For now, return all files (production would filter by git history)
        return all_files[:50] if start_session == 0 else all_files[-50:]

    def _has_import_groups(self, imports: List[str]) -> bool:
        """Check if imports are organized into groups"""
        # Simplified check - look for blank line patterns in original file
        return True  # Placeholder

    def _get_recommendations(
        self,
        pattern_name: str,
        baseline: Dict[str, float],
        current: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations for fixing drift"""
        recommendations = []

        for key in baseline:
            if key in current:
                diff = baseline[key] - current[key]
                if diff > 0.2:  # Pattern decreased significantly
                    recommendations.append(
                        f"Consider using more '{key}' pattern (baseline: {baseline[key]:.0%}, current: {current[key]:.0%})"
                    )
                elif diff < -0.2:  # Pattern increased significantly
                    recommendations.append(
                        f"'{key}' usage increased from baseline (baseline: {baseline[key]:.0%}, current: {current[key]:.0%})"
                    )

        return recommendations
```

#### CLI Integration

```bash
# Run drift detection
sk drift --analyze

# Generate drift report
sk drift --report

# Compare specific sessions
sk drift --compare session-005..session-020

# Set baseline
sk drift --set-baseline --sessions 1-5
```

#### Sample Output

```
Convention Drift Report
=======================

Overall Status: NEEDS ATTENTION (67% consistent)

Pattern Analysis:
-----------------

Error Handling (45% consistent) ⚠️ DRIFTING
  Baseline: try_catch: 80%, result_type: 20%
  Current:  try_catch: 40%, result_type: 60%

  Recommendations:
  - Pattern changed significantly. Consider standardizing on Result type
    (which has become more common) or documenting both as acceptable.

API Responses (92% consistent) ✓ CONSISTENT
  Baseline: {success, data, error} format
  Current:  {success, data, error} format

Naming (88% consistent) ✓ CONSISTENT
  Baseline: PascalCase for components, camelCase for utilities
  Current:  Matches baseline

Imports (71% consistent) ⚠️ DRIFTING
  Baseline: grouped_imports: 90%
  Current:  grouped_imports: 65%

  Recommendations:
  - Import organization has degraded. Run 'sk lint --fix' to reorganize.

Typing (55% consistent) ⚠️ DRIFTING
  Baseline: explicit_return_types: 85%, any_usage: 5%
  Current:  explicit_return_types: 60%, any_usage: 25%

  Recommendations:
  - Type coverage has decreased. Consider adding eslint rule for explicit returns.
  - 'any' usage has increased 5x. Review recent files for type safety.
```

---

## Layer 2: AI-Enhanced Enforcement

The AI-enhanced layer provides semantic understanding that complements deterministic rules. These are documented in detail in [ENHANCEMENTS.md](./ENHANCEMENTS.md).

### Enhancement #29: Frontend Quality & Design System Compliance

**Lines 3474-4155 in ENHANCEMENTS.md**

Provides automated design system enforcement:
- Design token validation (detect hardcoded colors, spacing, fonts)
- Component library enforcement (detect raw HTML vs. components)
- Framework best practices (React hooks, Next.js optimizations)
- Accessibility validation (semantic HTML, ARIA, WCAG)
- Bundle size monitoring
- CSS quality standards

**Key Integration Points:**
- Runs as part of quality gates at `sk end`
- Configuration in `.session/config.json` under `quality_gates.frontend`
- Complements deterministic Layer 1 rules

### Enhancement #30: Documentation-Driven Development

**Lines 4156-4440 in ENHANCEMENTS.md**

Provides architecture alignment:
- Parse Vision, PRD, Architecture documents
- Generate work items from documentation
- Architecture Decision Records (ADR) management
- Document-to-code traceability
- **Architecture validation** - validate work items against architectural constraints
- API-first documentation (OpenAPI generation, SDK generation)

**Key Integration Points:**
- Work items validated against architecture constraints
- ADRs linked to work items and code
- Traceability matrix between requirements and implementation

### Enhancement #31: AI-Enhanced Learning System

**Lines 4441-4947 in ENHANCEMENTS.md**

Provides semantic convention understanding:
- **Semantic similarity detection** - find similar learnings without keyword matches
- **Semantic relevance scoring** - find relevant conventions for current work
- Intelligent categorization with confidence scores
- Learning relationships and knowledge graph
- Learning summarization

**Key Integration Points:**
- Session briefings include semantically relevant learnings
- Conventions captured as learnings are found based on meaning, not keywords
- Related conventions surfaced even with different terminology

### Enhancement #39: Automated Code Review

**Lines 6237-6313 in ENHANCEMENTS.md**

Provides AI-powered consistency checking:
- Analyze code changes for convention violations
- Detect anti-patterns and code smells
- Suggest improvements based on established patterns
- Security vulnerability detection
- Best practice recommendations

**Key Integration Points:**
- Runs during `sk end` before quality gates
- Can reference convention manifest for project-specific rules
- Learns from approved code patterns

---

## Integration with Solokit

### Quality Gate Enhancement

```python
# src/solokit/quality/gates.py (enhanced)
class QualityGateRunner:
    """Enhanced quality gates with convention enforcement"""

    def run_all_gates(self, config: Dict[str, Any]) -> Dict[str, Any]:
        results = {"passed": True, "gates": {}}

        # Tier 1: Essential (existing)
        results["gates"]["tests"] = self.run_tests()
        results["gates"]["linting"] = self.run_linting()
        results["gates"]["formatting"] = self.run_formatting()

        # Tier 2: Convention Enforcement (NEW)
        if config.get("convention_enforcement", {}).get("enabled"):
            results["gates"]["conventions"] = self.run_convention_validation()
            results["gates"]["architecture"] = self.run_architecture_tests()
            results["gates"]["dependencies"] = self.run_dependency_rules()

        # Tier 3: AI-Enhanced (NEW with #29, #31, #39)
        if config.get("ai_enhanced", {}).get("enabled"):
            results["gates"]["design_system"] = self.run_design_system_check()
            results["gates"]["code_review"] = self.run_ai_code_review()

        # Tier 4: Drift Detection (NEW)
        if config.get("drift_detection", {}).get("enabled"):
            drift_result = self.run_drift_detection()
            results["gates"]["drift"] = drift_result
            # Drift is warning-only, doesn't block
            if drift_result["status"] == "critical":
                results["warnings"] = results.get("warnings", [])
                results["warnings"].append("Critical convention drift detected")

        # Security (existing)
        results["gates"]["security"] = self.run_security_scan()

        # Calculate overall pass/fail
        for gate_name, gate_result in results["gates"].items():
            if gate_result.get("required", True) and not gate_result.get("passed", True):
                results["passed"] = False

        return results
```

### Configuration Schema

```json
// .session/config.json (enhanced)
{
  "quality_gates": {
    "tests": { "enabled": true, "coverage_threshold": 80 },
    "linting": { "enabled": true, "auto_fix": true },
    "formatting": { "enabled": true, "auto_fix": true },
    "security": { "enabled": true, "fail_on": "high" },

    "convention_enforcement": {
      "enabled": true,
      "manifest_path": ".session/conventions.yaml",
      "fail_on_violation": true,
      "checks": {
        "naming": true,
        "api_patterns": true,
        "design_tokens": true,
        "architecture": true
      }
    },

    "architecture_tests": {
      "enabled": true,
      "tool": "ts-arch",  // or "import-linter" for Python
      "config_path": "tests/architecture/"
    },

    "dependency_rules": {
      "enabled": true,
      "tool": "dependency-cruiser",
      "config_path": ".dependency-cruiser.js"
    },

    "drift_detection": {
      "enabled": true,
      "baseline_sessions": 5,
      "warn_threshold": 0.7,
      "critical_threshold": 0.5,
      "check_frequency": "every_session"  // or "every_n_sessions: 3"
    },

    "ai_enhanced": {
      "enabled": true,
      "design_system": true,
      "code_review": true,
      "semantic_learning": true
    }
  }
}
```

### Session Briefing Enhancement

```python
# src/solokit/session/briefing/convention_loader.py
class ConventionLoader:
    """Load relevant conventions for session briefing"""

    def get_conventions_for_work_item(
        self,
        work_item_id: str
    ) -> Dict[str, Any]:
        """Get conventions relevant to the current work item"""

        # Load convention manifest
        manifest = self._load_manifest()

        # Get work item details
        work_item = self._get_work_item(work_item_id)

        # Filter to relevant conventions
        relevant = {}

        # API work → API conventions
        if "api" in work_item["title"].lower() or work_item["type"] == "feature":
            relevant["api"] = manifest.get("api", {})

        # Frontend work → Design tokens
        if any(tag in work_item.get("tags", []) for tag in ["frontend", "ui", "component"]):
            relevant["design_tokens"] = manifest.get("design_tokens", {})

        # All work → Naming and architecture
        relevant["naming"] = manifest.get("naming", {})
        relevant["architecture"] = manifest.get("architecture", {})

        return relevant

    def format_for_briefing(self, conventions: Dict[str, Any]) -> str:
        """Format conventions for session briefing markdown"""
        sections = []

        if conventions.get("api"):
            sections.append(self._format_api_conventions(conventions["api"]))

        if conventions.get("design_tokens"):
            sections.append(self._format_design_conventions(conventions["design_tokens"]))

        if conventions.get("architecture"):
            sections.append(self._format_architecture_conventions(conventions["architecture"]))

        return "\n\n".join(sections)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Priority: Critical**

1. **Convention Manifest System**
   - Define YAML schema
   - Implement ConventionValidator
   - Add `sk conventions` CLI commands
   - Integrate with quality gates

2. **Architecture Tests Setup**
   - Add ts-arch to TypeScript templates
   - Add import-linter to Python templates
   - Create example architecture test suites
   - Document patterns

### Phase 2: Lint Rules & Dependencies (Weeks 3-4)

**Priority: High**

3. **Custom Lint Rules**
   - Create eslint-local-rules structure
   - Implement core project rules (API format, error codes)
   - Integrate with eslint.config.js template
   - Add Ruff configuration for Python

4. **Dependency Rules**
   - Add dependency-cruiser to JS/TS templates
   - Create default architecture rules
   - Integrate with `sk validate`

### Phase 3: Templates & Generation (Weeks 5-6)

**Priority: Medium**

5. **Code Pattern Templates**
   - Design template system
   - Create core templates (API route, component, service, hook)
   - Implement `sk generate` command
   - Allow custom templates

### Phase 4: Drift Detection (Weeks 7-8)

**Priority: Medium**

6. **Convention Drift Detection**
   - Implement DriftDetector
   - Add git history analysis
   - Create drift reports
   - Integrate with quality gates (as warnings)

### Phase 5: AI Integration (Ongoing)

**Priority: High (parallel track)**

7. **Enhancement #31: AI Learning System**
   - Semantic similarity for learnings
   - Semantic relevance in briefings

8. **Enhancement #29: Frontend Quality**
   - Design token validation
   - Component library enforcement

9. **Enhancement #39: Automated Code Review**
   - AI-powered convention checking

---

## References

### Tools & Libraries

- **ESLint Custom Rules**: [eslint.org/docs/extend/custom-rules](https://eslint.org/docs/latest/extend/custom-rules)
- **eslint-plugin-boundaries**: [github.com/javierbrea/eslint-plugin-boundaries](https://github.com/javierbrea/eslint-plugin-boundaries)
- **eslint-plugin-local-rules**: [medium.com/@ignatovich.dm/creating-and-using-custom-local-eslint-rules](https://medium.com/@ignatovich.dm/creating-and-using-custom-local-eslint-rules-with-eslint-plugin-local-rules-428d510db78f)
- **dependency-cruiser**: [github.com/sverweij/dependency-cruiser](https://github.com/sverweij/dependency-cruiser)
- **ts-arch**: [github.com/ts-arch/ts-arch](https://github.com/ts-arch/ts-arch)
- **import-linter**: [import-linter.readthedocs.io](https://import-linter.readthedocs.io/en/stable/)
- **pytest-arch**: [github.com/nwilbert/pytest-arch](https://github.com/nwilbert/pytest-arch)
- **ArchUnit**: [archunit.org](https://www.archunit.org/)
- **Ruff**: [docs.astral.sh/ruff](https://docs.astral.sh/ruff/)

### Related Solokit Enhancements

- **#29**: Frontend Quality & Design System Compliance (lines 3474-4155)
- **#30**: Documentation-Driven Development (lines 4156-4440)
- **#31**: AI-Enhanced Learning System (lines 4441-4947)
- **#39**: Automated Code Review (lines 6237-6313)

### Articles & Guides

- [6 Ways to Improve Python Architecture with import-linter](https://www.piglei.com/articles/en-6-ways-to-improve-the-arch-of-you-py-project/)
- [ArchUnit in Practice: Keep Your Architecture Clean](https://www.codecentric.de/en/knowledge-hub/blog/archunit-in-practice-keep-your-architecture-clean)
- [Dependency Cruiser: Restrict Imports in JavaScript](https://spin.atomicobject.com/dependency-cruiser-imports/)
- [How ESLint Can Enforce Your Design System Best Practices](https://backlight.dev/blog/best-practices-w-eslint-part-1)

---

*This document will be updated as implementation progresses.*
