---
description: Validate current session meets quality standards without ending it
---

# Session Validate

Run the validation script to check quality standards:

```bash
sk validate
```

To automatically fix linting and formatting issues:

```bash
sk validate --fix
```

The validation checks:

- **Tests**: All test suites pass
- **Linting**: Code passes linting rules (auto-fixable with --fix)
- **Formatting**: Code is properly formatted (auto-fixable with --fix)
- **Code Coverage**: Meets minimum coverage threshold
- **Git Status**: Working directory is clean or has expected changes
- **Acceptance Criteria**: Work item requirements are met

Display the validation results to the user with a clear pass/fail status for each check. If linting or formatting fail, suggest using `/validate --fix` to automatically fix the issues. This command allows checking quality during development without ending the session.
