# Creating Solokit Templates

This guide explains how to create new project templates for Solokit's template-based initialization system.

## Overview

Solokit uses a tier-based template system that allows projects to be initialized with different quality levels:

- **Tier 1 (Essential)**: Core testing and linting
- **Tier 2 (Standard)**: + Security scanning and formatting
- **Tier 3 (Comprehensive)**: + E2E tests and performance monitoring
- **Tier 4 (Production)**: + Production monitoring and deployment tools

## Template Structure

Each template has the following directory structure:

```
templates/
└── your_template_name/
    ├── base/                           # Base files (always installed)
    │   ├── src/                        # Source code
    │   ├── package.json.template       # Config with placeholders
    │   └── README.md                   # Project documentation
    ├── tier-1-essential/               # Tier 1 additions
    │   ├── tests/                      # Test files
    │   └── package.json.tier1.template # Tier 1 packages
    ├── tier-2-standard/                # Tier 2 additions
    │   └── package.json.tier2.template # Tier 2 packages
    ├── tier-3-comprehensive/           # Tier 3 additions
    │   ├── e2e/                        # E2E tests
    │   └── package.json.tier3.template # Tier 3 packages
    ├── tier-4-production/              # Tier 4 additions
    │   └── package.json.tier4.template # Tier 4 packages
    ├── ci-cd/                          # CI/CD files (optional)
    │   └── .github/
    ├── docker/                         # Docker files (optional)
    │   ├── Dockerfile
    │   └── docker-compose.yml
    └── env-templates/                  # Environment templates (optional)
        ├── .env.local.example
        └── .env.production.example
```

## Template Files

### Base Template

The base template contains essential files that are always installed:

**Required files:**
- `package.json.template` (or `pyproject.toml.template` for Python)
- Source code structure
- Basic configuration files

**Naming convention:**
- Files ending in `.template` will have placeholders replaced
- Other files are copied as-is

### Tier Templates

Each tier adds incremental functionality:

**Tier template files must be named with tier suffix:**
- `package.json.tier1.template`
- `package.json.tier2.template`
- `package.json.tier3.template`
- `package.json.tier4.template`

The tier suffix (`.tier1`, `.tier2`, etc.) is automatically stripped during installation, so all tier templates merge into the final `package.json` or `pyproject.toml`.

**Important**: Each higher tier completely replaces the previous tier's configuration. Tier 4 should contain ALL packages from tiers 1-3 plus tier 4 additions.

## Placeholders

Templates support the following placeholders:

- `{project_name}` - Project directory name
- `{project_description}` - Description from template metadata
- `{template_id}` - Template identifier
- `{template_name}` - Human-readable template name

Example:
```json
{
  "name": "{project_name}",
  "description": "{project_description}",
  "version": "0.1.0"
}
```

## Version Management

All package versions should be defined in `stack-versions.yaml`:

```yaml
stacks:
  your_template:
    name: "Your Template Name"
    description: "Template description"
    package_manager: "npm"  # or "pip"

    base_framework:
      next: "16.0.7"
      react: "19.2.1"

    tier1_essential:
      jest: "30.0.3"
      eslint: "9.39.1"

    tier2_standard:
      prettier: "3.6.2"
      husky: "9.1.7"

    tier3_comprehensive:
      playwright: "1.56.1"
      lighthouse: "12.2.1"

    tier4_production:
      "@sentry/nextjs": "10.23.0"
      "@vercel/analytics": "1.5.0"

    installation:
      commands:
        base: "npm install next@16.0.7 react@19.2.1 react-dom@19.2.1"
        tier1: "npm install --save-dev jest@30.0.3 eslint@9.39.1"
        tier2: "npm install --save-dev prettier@3.6.2 husky@9.1.7"
        tier3: "npm install --save-dev playwright@1.56.1 @lhci/cli@0.15.1"
        tier4_dev: "npm install --save-dev @sentry/cli@2.39.2"
        tier4_prod: "npm install @sentry/nextjs@10.23.0 @vercel/analytics@1.5.0"
```

## Template Registry

Register your template in `template-registry.json`:

```json
{
  "templates": {
    "your_template": {
      "id": "your_template",
      "display_name": "Your Template Name",
      "description": "Brief description of what this template provides",
      "category": "web|backend|ml_ai|dashboard",
      "package_manager": "npm",
      "language": "typescript",
      "framework": "Next.js",
      "supported_tiers": [
        "tier-1-essential",
        "tier-2-standard",
        "tier-3-comprehensive",
        "tier-4-production"
      ],
      "additional_options": [
        "ci_cd",
        "docker",
        "env_templates"
      ],
      "tech_stack": {
        "frontend": ["Next.js 16", "React 19", "Tailwind CSS 4"],
        "backend": ["API Routes"],
        "testing": ["Jest", "Playwright"],
        "deployment": ["Vercel", "Docker"]
      }
    }
  }
}
```

## Tier Guidelines

### Tier 1 (Essential) - Development Basics
**Purpose**: Enable basic development workflow

**Should include:**
- Unit testing framework
- Linter (ESLint/Ruff)
- Type checker (TypeScript/Pyright)
- Basic test examples
- Hot reload/dev server

**Time estimate**: 5-15 minutes installation

### Tier 2 (Standard) - Team Collaboration
**Purpose**: Support team development

**Should include:**
- Code formatter (Prettier/Black)
- Security scanning (npm audit/bandit)
- Git hooks (Husky + lint-staged)
- Commit linting
- License checking

**Time estimate**: +3-5 minutes

### Tier 3 (Comprehensive) - Quality Assurance
**Purpose**: Comprehensive testing and quality

**Should include:**
- E2E testing (Playwright/Locust)
- Performance monitoring (Lighthouse)
- Code quality tools (SonarQube/Radon)
- Mutation testing
- Load testing capabilities

**Time estimate**: +5-10 minutes

### Tier 4 (Production) - Production Ready
**Purpose**: Production deployment and monitoring

**Should include:**
- Error tracking (Sentry)
- Analytics
- Performance monitoring (OpenTelemetry/Prometheus)
- Health checks
- Production deployment configs
- CDN/Edge optimization

**Time estimate**: +3-5 minutes

## Example: Creating a New Template

Let's create a simple Express.js template:

### 1. Create directory structure

```bash
mkdir -p src/solokit/templates/express_api/{base,tier-1-essential,tier-2-standard}
```

### 2. Create base template

**base/package.json.template:**
```json
{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "{project_description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js"
  },
  "dependencies": {
    "express": "4.21.2",
    "dotenv": "16.4.5"
  },
  "devDependencies": {
    "nodemon": "3.1.9"
  }
}
```

**base/src/index.js:**
```javascript
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Hello World' });
});

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
```

### 3. Add tier 1 testing

**tier-1-essential/package.json.tier1.template:**
```json
{
  "name": "{project_name}",
  "version": "0.1.0",
  "description": "{project_description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:coverage": "jest --coverage"
  },
  "dependencies": {
    "express": "4.21.2",
    "dotenv": "16.4.5"
  },
  "devDependencies": {
    "nodemon": "3.1.9",
    "jest": "30.0.3",
    "supertest": "7.0.0",
    "eslint": "9.18.0"
  }
}
```

**tier-1-essential/tests/api.test.js:**
```javascript
const request = require('supertest');
const app = require('../src/index');

describe('GET /', () => {
  it('should return hello world', async () => {
    const res = await request(app).get('/');
    expect(res.statusCode).toBe(200);
    expect(res.body.message).toBe('Hello World');
  });
});
```

### 4. Update stack-versions.yaml

```yaml
stacks:
  express_api:
    name: "Express.js API"
    description: "RESTful API with Express.js"
    package_manager: "npm"

    base_framework:
      express: "4.21.2"
      dotenv: "16.4.5"
      nodemon: "3.1.9"

    tier1_essential:
      jest: "30.0.3"
      supertest: "7.0.0"
      eslint: "9.18.0"

    installation:
      commands:
        base: "npm install express@4.21.2 dotenv@16.4.5 && npm install --save-dev nodemon@3.1.9"
        tier1: "npm install --save-dev jest@30.0.3 supertest@7.0.0 eslint@9.18.0"
```

### 5. Register in template-registry.json

```json
{
  "templates": {
    "express_api": {
      "id": "express_api",
      "display_name": "Express.js API",
      "description": "RESTful API with Express.js and TypeScript",
      "category": "backend",
      "package_manager": "npm",
      "language": "javascript",
      "framework": "Express.js",
      "supported_tiers": ["tier-1-essential", "tier-2-standard"],
      "tech_stack": {
        "backend": ["Express.js 4", "Node.js"],
        "testing": ["Jest", "Supertest"],
        "tools": ["ESLint", "Nodemon"]
      }
    }
  }
}
```

## Testing Your Template

1. **Initialize a test project:**
```bash
cd /tmp
mkdir test-express-api
cd test-express-api
sk init --template=express_api --tier=tier-1-essential
```

2. **Verify installation:**
```bash
npm test
npm run dev
```

3. **Check all tiers:**
```bash
# Test each tier
sk init --template=express_api --tier=tier-1-essential
sk init --template=express_api --tier=tier-2-standard
sk init --template=express_api --tier=tier-3-comprehensive
sk init --template=express_api --tier=tier-4-production
```

## Best Practices

### File Organization
- Keep base template minimal - only essentials
- Group related features in same tier
- Use clear, descriptive directory names
- Include README in base template

### Dependency Management
- Pin exact versions in stack-versions.yaml
- Test all dependencies work together
- Document any version conflicts in known_issues
- Use official packages when possible

### Testing
- Include example tests in tier 1
- Test templates build successfully
- Verify all tiers install correctly
- Check optional features work

### Documentation
- Clear README in base template
- Comment complex configurations
- Document required environment variables
- Include getting started examples

### Maintenance
- Keep stack-versions.yaml updated
- Test with latest package versions regularly
- Document breaking changes
- Update examples when APIs change

## Common Issues

### Issue: Tier files not merging

**Symptom**: Multiple `package.json.tier1`, `package.json.tier2` files exist

**Solution**: Ensure files follow naming convention `package.json.tier[1-4].template`. The `.tier[1-4]` suffix is automatically stripped during installation.

### Issue: Placeholders not replaced

**Symptom**: Literal `{project_name}` appears in files

**Solution**: Ensure files end with `.template` extension. Only `.template` files have placeholders replaced.

### Issue: Dependencies not installing

**Symptom**: Installation fails with missing packages

**Solution**: Verify installation commands in stack-versions.yaml match template package.json. Test each tier command individually.

### Issue: Conflicting versions

**Symptom**: Package version warnings or errors

**Solution**: Check version compatibility in stack-versions.yaml. Document conflicts in `known_issues` section.

## Reference

- [Stack Versions Schema](stack-versions-schema.md)
- [Template Registry Schema](template-registry-schema.md)
- [Template Installer](../../src/solokit/init/template_installer.py)
- [Dependency Installer](../../src/solokit/init/dependency_installer.py)
