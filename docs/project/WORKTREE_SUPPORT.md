# Git Worktree Support for Parallel Development

## Document Status
- **Type**: Feature Specification
- **Status**: Proposed
- **Created**: 2025-12-28
- **Author**: Claude (with Ankush Dixit)

---

## 1. Executive Summary

This document specifies the implementation of git worktree support in Solokit, enabling developers to work on multiple work items simultaneously in separate worktrees while maintaining a single, shared session state.

### Problem Statement

Currently, Solokit's `/start` command creates a branch and checks it out in the current working directory. This prevents parallel work on multiple work items because:
1. Only one branch can be checked out at a time in a single working directory
2. The `.session/` directory is per-working-directory, so each worktree would have independent (and potentially conflicting) state

### Proposed Solution

1. Add `--worktree` flag to `/start` command to create a git worktree for a work item
2. Move all session state to `.git/solokit/` (shared across all worktrees)
3. Track active sessions per-worktree using worktree path as key
4. Maintain global session numbering across all worktrees

---

## 2. Background

### What Are Git Worktrees?

Git worktrees allow multiple working directories to share a single `.git/` repository. Each worktree can have a different branch checked out, enabling true parallel development.

```bash
# Main worktree
/project/              # Working directory with .git/
  .git/                # Actual git directory

# Added worktree
/project-feature/      # Separate working directory
  .git                 # File pointing to main .git/worktrees/project-feature/
```

Key insight: `git rev-parse --git-common-dir` returns the path to the shared `.git/` directory from any worktree.

### Current Solokit Architecture

**Session state location**: `.session/` directory in the working tree (gitignored)

**Current structure**:
```
.session/
├── config.json                    # Quality gates, git workflow config
├── tracking/
│   ├── work_items.json            # Work item definitions and metadata
│   ├── learnings.json             # Captured learnings
│   ├── status_update.json         # Current active session
│   ├── stack.txt                  # Technology stack snapshot
│   └── tree.txt                   # Directory structure snapshot
├── specs/
│   └── {work_item_id}.md          # Work item specifications
├── briefings/
│   └── session_{NNN}_briefing.md  # Session briefings
└── history/
    └── session_{NNN}_summary.md   # Session summaries
```

**Problem**: Each worktree would have its own `.session/` directory, leading to:
- Duplicated/conflicting work item definitions
- Separate learnings databases
- Potential session number conflicts
- No visibility into what's happening in other worktrees

---

## 3. Proposed Architecture

### 3.1 New Session State Location

Move all session state to `.git/solokit/` which is shared across all worktrees:

```
/project/.git/solokit/               # ALL session state (shared)
├── config.json                      # Quality gates, git workflow, worktree settings
├── tracking/
│   ├── work_items.json              # All work items (single source of truth)
│   ├── learnings.json               # All learnings (shared knowledge)
│   ├── active_sessions.json         # Active sessions keyed by worktree path
│   ├── stack.txt                    # Project stack snapshot
│   ├── tree.txt                     # Directory tree snapshot
│   ├── stack_updates.json           # Historical stack changes
│   └── tree_updates.json            # Historical tree changes
├── specs/
│   ├── feature_auth.md              # Work item specifications
│   └── bug_fix_login.md
├── briefings/
│   ├── session_001_briefing.md      # All briefings (global numbering)
│   ├── session_002_briefing.md
│   └── ...
└── history/
    ├── session_001_summary.md       # All summaries (global numbering)
    ├── session_002_summary.md
    └── ...
```

### 3.2 Active Sessions Tracking

Replace single `status_update.json` with `active_sessions.json` that tracks multiple concurrent sessions:

**Old format** (`status_update.json`):
```json
{
  "current_work_item": "feature_auth",
  "current_session": 5,
  "started_at": "2025-12-28T10:00:00",
  "status": "in_progress"
}
```

**New format** (`active_sessions.json`):
```json
{
  "sessions": {
    "/Users/ankush/Projects/solokit": {
      "work_item_id": "feature_auth",
      "session_num": 5,
      "started_at": "2025-12-28T10:00:00",
      "status": "in_progress"
    },
    "/Users/ankush/Projects/solokit-bug_fix": {
      "work_item_id": "bug_fix",
      "session_num": 6,
      "started_at": "2025-12-28T11:00:00",
      "status": "in_progress"
    }
  },
  "next_session_num": 7
}
```

### 3.3 Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State location | `.git/solokit/` | Automatically shared across worktrees via git internals |
| Session numbering | Global | Avoids conflicts, simplifies cross-referencing |
| Active session tracking | Keyed by worktree path | Enables multiple concurrent sessions |
| Worktree path format | Absolute path | Simple, unambiguous |
| Default worktree location | `../{repo-name}-{work_item_id}` | Sibling directory, predictable |

---

## 4. Command Changes

### 4.1 `/start` Command

#### New Argument: `--worktree`

```bash
# Normal mode (existing behavior, but with shared state)
sk start feature_auth

# Worktree mode (new)
sk start feature_auth --worktree
# Creates worktree at ../solokit-feature_auth

# Worktree mode with explicit path (optional, rare)
sk start feature_auth --worktree-path ~/worktrees/feature
```

#### Worktree Mode Flow

```
sk start feature_auth --worktree
    │
    ├─► Validate work item exists in work_items.json
    │
    ├─► Check no conflicting active session for this work item
    │
    ├─► Determine worktree path (default: ../{repo}-{work_item_id})
    │
    ├─► Create branch if doesn't exist
    │   └─► git branch feature_auth
    │
    ├─► Capture parent branch (for later merging)
    │   └─► git branch --show-current
    │
    ├─► Create worktree
    │   └─► git worktree add <path> feature_auth
    │
    ├─► Update work_items.json with git tracking info
    │   ├─► branch: feature_auth
    │   ├─► parent_branch: main
    │   ├─► status: in_progress
    │   └─► worktree_path: <path>
    │
    ├─► Add entry to active_sessions.json
    │   └─► Key: worktree path, Value: session info
    │
    ├─► Determine session number (global, from active_sessions.json)
    │
    ├─► Generate briefing
    │
    ├─► Save briefing to .git/solokit/briefings/
    │
    ├─► Print briefing
    │
    └─► Print: "To continue working: cd <worktree_path>"
```

#### Normal Mode Changes

Normal mode (`sk start feature_auth` without `--worktree`) continues to work but:
1. Reads/writes from `.git/solokit/` instead of `.session/`
2. Uses `active_sessions.json` keyed by current worktree path
3. Uses global session numbering

### 4.2 `/end` Command

#### Changes Required

1. **Read active session from `active_sessions.json`** using current worktree path as key
2. **Update shared `work_items.json`** with completion status and commits
3. **Remove/update entry in `active_sessions.json`**
4. **Save summary to shared `history/`**

#### Optional Enhancement: `--remove-worktree`

```bash
sk end --complete --remove-worktree
```

After completing the session and merging/creating PR:
1. Switch to parent branch in main worktree
2. Remove the worktree: `git worktree remove <path>`
3. Optionally delete the local branch if merged

### 4.3 `/status` Command

#### Changes Required

1. **Show current worktree's active session** from `active_sessions.json`
2. **Optionally show all active sessions** with `--all` flag

#### New Output Example

```
Current Session Status
━━━━━━━━━━━━━━━━━━━━━━
Worktree: /Users/ankush/Projects/solokit (main)
Work Item: feature_auth (Session #5)
Started: 2025-12-28 10:00:00 (2h 30m ago)
Branch: feature_auth
Status: in_progress

Other Active Sessions
━━━━━━━━━━━━━━━━━━━━━━
• /Users/ankush/Projects/solokit-bug_fix
  Work Item: bug_fix (Session #6)
  Started: 2025-12-28 11:00:00 (1h 30m ago)
```

### 4.4 Work Item Commands

All work item commands need path updates:

| Command | File Access Changes |
|---------|---------------------|
| `/work-list` | Read from `.git/solokit/tracking/work_items.json` |
| `/work-show` | Read from `.git/solokit/tracking/work_items.json`, `.git/solokit/specs/` |
| `/work-new` | Write to `.git/solokit/tracking/work_items.json`, `.git/solokit/specs/` |
| `/work-update` | Write to `.git/solokit/tracking/work_items.json` |
| `/work-delete` | Write to `.git/solokit/tracking/work_items.json`, `.git/solokit/specs/` |
| `/work-next` | Read from `.git/solokit/tracking/work_items.json` |
| `/work-graph` | Read from `.git/solokit/tracking/work_items.json` |

### 4.5 Learning Commands

| Command | File Access Changes |
|---------|---------------------|
| `/learn` | Write to `.git/solokit/tracking/learnings.json` |
| `/learn-show` | Read from `.git/solokit/tracking/learnings.json` |
| `/learn-search` | Read from `.git/solokit/tracking/learnings.json` |
| `/learn-curate` | Read/write `.git/solokit/tracking/learnings.json` |

### 4.6 `/validate` Command

Read config from `.git/solokit/config.json`.

### 4.7 `/init` and `/adopt` Commands

#### New Initialization Flow

1. Create `.git/solokit/` directory structure
2. Create empty tracking files with proper schema
3. Create `.session/` as a pointer/README (for discoverability)
4. Update `.gitignore` to ignore `.session/` (keep existing behavior)

#### Migration for Existing Projects

`/adopt` should detect existing `.session/` and offer migration:

```
Detected existing .session/ directory.
Migrating to shared state in .git/solokit/...
  ✓ Moved tracking/work_items.json
  ✓ Moved tracking/learnings.json
  ✓ Moved specs/
  ✓ Moved config.json
  ✓ Converted status_update.json to active_sessions.json
  ✓ Moved briefings/
  ✓ Moved history/
Migration complete!
```

---

## 5. Implementation Details

### 5.1 SessionPaths Utility Class

**File**: `src/solokit/core/paths.py` (new)

```python
from pathlib import Path
import subprocess

class SessionPaths:
    """Resolves paths to shared session state in .git/solokit/."""

    def __init__(self, working_dir: Path | None = None):
        self.working_dir = Path(working_dir or Path.cwd()).resolve()
        self._git_common_dir: Path | None = None

    @property
    def git_common_dir(self) -> Path:
        """Get the shared .git directory (works from any worktree)."""
        if self._git_common_dir is None:
            result = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                capture_output=True,
                text=True,
                cwd=self.working_dir
            )
            if result.returncode != 0:
                raise NotAGitRepoError(f"Not a git repository: {self.working_dir}")
            self._git_common_dir = Path(result.stdout.strip()).resolve()
        return self._git_common_dir

    @property
    def solokit_root(self) -> Path:
        """Root directory for all Solokit session state."""
        return self.git_common_dir / "solokit"

    @property
    def worktree_path(self) -> Path:
        """Get the current worktree's absolute path (used as session key)."""
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=self.working_dir
        )
        return Path(result.stdout.strip()).resolve()

    # Tracking files
    @property
    def work_items_file(self) -> Path:
        return self.solokit_root / "tracking" / "work_items.json"

    @property
    def learnings_file(self) -> Path:
        return self.solokit_root / "tracking" / "learnings.json"

    @property
    def active_sessions_file(self) -> Path:
        return self.solokit_root / "tracking" / "active_sessions.json"

    @property
    def stack_file(self) -> Path:
        return self.solokit_root / "tracking" / "stack.txt"

    @property
    def tree_file(self) -> Path:
        return self.solokit_root / "tracking" / "tree.txt"

    # Directories
    @property
    def specs_dir(self) -> Path:
        return self.solokit_root / "specs"

    @property
    def briefings_dir(self) -> Path:
        return self.solokit_root / "briefings"

    @property
    def history_dir(self) -> Path:
        return self.solokit_root / "history"

    @property
    def config_file(self) -> Path:
        return self.solokit_root / "config.json"

    def ensure_structure(self) -> None:
        """Create the .git/solokit/ directory structure if it doesn't exist."""
        self.solokit_root.mkdir(exist_ok=True)
        (self.solokit_root / "tracking").mkdir(exist_ok=True)
        self.specs_dir.mkdir(exist_ok=True)
        self.briefings_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
```

### 5.2 Active Sessions Manager

**File**: `src/solokit/session/active_sessions.py` (new)

```python
from pathlib import Path
from datetime import datetime
import json
import fcntl
from contextlib import contextmanager
from dataclasses import dataclass

@dataclass
class ActiveSession:
    work_item_id: str
    session_num: int
    started_at: str
    status: str  # "in_progress", "paused"

class ActiveSessionsManager:
    """Manages active sessions across multiple worktrees."""

    def __init__(self, paths: SessionPaths):
        self.paths = paths
        self.file_path = paths.active_sessions_file

    @contextmanager
    def _locked_access(self, write: bool = False):
        """Context manager for thread-safe file access with locking."""
        mode = 'r+' if write and self.file_path.exists() else 'r'
        if not self.file_path.exists():
            # Initialize empty structure
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(json.dumps({
                "sessions": {},
                "next_session_num": 1
            }, indent=2))
            mode = 'r+'

        with open(self.file_path, mode) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                data = json.load(f)
                yield data
                if write:
                    f.seek(0)
                    f.truncate()
                    json.dump(data, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def get_active_session(self, worktree_path: Path | None = None) -> ActiveSession | None:
        """Get the active session for a worktree (default: current worktree)."""
        worktree_path = worktree_path or self.paths.worktree_path
        worktree_key = str(worktree_path)

        with self._locked_access() as data:
            session_data = data["sessions"].get(worktree_key)
            if session_data:
                return ActiveSession(**session_data)
            return None

    def get_all_active_sessions(self) -> dict[str, ActiveSession]:
        """Get all active sessions across all worktrees."""
        with self._locked_access() as data:
            return {
                path: ActiveSession(**session_data)
                for path, session_data in data["sessions"].items()
            }

    def start_session(
        self,
        work_item_id: str,
        worktree_path: Path | None = None
    ) -> int:
        """Start a new session, returns the session number."""
        worktree_path = worktree_path or self.paths.worktree_path
        worktree_key = str(worktree_path)

        with self._locked_access(write=True) as data:
            # Check if this worktree already has an active session
            if worktree_key in data["sessions"]:
                existing = data["sessions"][worktree_key]
                raise SessionAlreadyActiveError(
                    f"Worktree already has active session for {existing['work_item_id']}"
                )

            # Get and increment session number
            session_num = data["next_session_num"]
            data["next_session_num"] = session_num + 1

            # Add session entry
            data["sessions"][worktree_key] = {
                "work_item_id": work_item_id,
                "session_num": session_num,
                "started_at": datetime.now().isoformat(),
                "status": "in_progress"
            }

            return session_num

    def end_session(self, worktree_path: Path | None = None) -> ActiveSession:
        """End the active session for a worktree, returns the ended session."""
        worktree_path = worktree_path or self.paths.worktree_path
        worktree_key = str(worktree_path)

        with self._locked_access(write=True) as data:
            if worktree_key not in data["sessions"]:
                raise NoActiveSessionError(f"No active session in worktree: {worktree_path}")

            session_data = data["sessions"].pop(worktree_key)
            return ActiveSession(**session_data)

    def is_work_item_active(self, work_item_id: str) -> tuple[bool, str | None]:
        """Check if a work item is being worked on in any worktree."""
        with self._locked_access() as data:
            for worktree_path, session_data in data["sessions"].items():
                if session_data["work_item_id"] == work_item_id:
                    return True, worktree_path
            return False, None
```

### 5.3 Worktree Manager

**File**: `src/solokit/git/worktree.py` (new)

```python
from pathlib import Path
from dataclasses import dataclass

@dataclass
class WorktreeInfo:
    path: Path
    branch: str
    commit: str
    is_main: bool

class WorktreeManager:
    """Manages git worktrees for Solokit."""

    def __init__(self, paths: SessionPaths, runner: CommandRunner):
        self.paths = paths
        self.runner = runner

    def get_default_worktree_path(self, work_item_id: str) -> Path:
        """Get the default path for a new worktree."""
        repo_name = self.paths.worktree_path.name
        parent_dir = self.paths.worktree_path.parent
        return parent_dir / f"{repo_name}-{work_item_id}"

    def list_worktrees(self) -> list[WorktreeInfo]:
        """List all worktrees for this repository."""
        result = self.runner.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=self.paths.working_dir
        )

        worktrees = []
        current = {}

        for line in result.stdout.strip().split('\n'):
            if line.startswith('worktree '):
                current['path'] = Path(line.split(' ', 1)[1])
            elif line.startswith('HEAD '):
                current['commit'] = line.split(' ', 1)[1][:7]
            elif line.startswith('branch '):
                current['branch'] = line.split('/')[-1]
            elif line == '':
                if current:
                    worktrees.append(WorktreeInfo(
                        path=current['path'],
                        branch=current.get('branch', 'detached'),
                        commit=current.get('commit', ''),
                        is_main=len(worktrees) == 0  # First is main
                    ))
                    current = {}

        return worktrees

    def create_worktree(
        self,
        work_item_id: str,
        worktree_path: Path | None = None
    ) -> tuple[Path, str, str]:
        """
        Create a worktree for a work item.

        Returns: (worktree_path, branch_name, parent_branch)
        """
        worktree_path = worktree_path or self.get_default_worktree_path(work_item_id)
        worktree_path = worktree_path.resolve()

        if worktree_path.exists():
            raise WorktreeExistsError(f"Path already exists: {worktree_path}")

        # Capture parent branch before creating worktree
        parent_branch = self._get_current_branch()

        # Check if branch exists
        branch_exists = self._branch_exists(work_item_id)

        if branch_exists:
            # Create worktree with existing branch
            result = self.runner.run([
                "git", "worktree", "add",
                str(worktree_path),
                work_item_id
            ])
        else:
            # Create worktree with new branch
            result = self.runner.run([
                "git", "worktree", "add",
                "-b", work_item_id,
                str(worktree_path)
            ])

        if not result.success:
            raise GitError(f"Failed to create worktree: {result.stderr}")

        return worktree_path, work_item_id, parent_branch

    def remove_worktree(self, worktree_path: Path, force: bool = False) -> None:
        """Remove a worktree."""
        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree_path))

        result = self.runner.run(cmd)
        if not result.success:
            raise GitError(f"Failed to remove worktree: {result.stderr}")

    def _get_current_branch(self) -> str:
        result = self.runner.run(["git", "branch", "--show-current"])
        return result.stdout.strip() or "main"

    def _branch_exists(self, branch_name: str) -> bool:
        result = self.runner.run([
            "git", "show-ref", "--verify",
            f"refs/heads/{branch_name}"
        ])
        return result.success
```

### 5.4 GitWorkflow Updates

**File**: `src/solokit/git/integration.py` (modify)

Add worktree support to existing `GitWorkflow` class:

```python
class GitWorkflow:
    def __init__(self, project_root: Path | None = None):
        self.project_root = Path(project_root or Path.cwd())
        self.paths = SessionPaths(self.project_root)
        self.worktree_manager = WorktreeManager(self.paths, self.runner)
        # ... existing init

    def start_work_item_in_worktree(
        self,
        work_item_id: str,
        worktree_path: Path | None = None
    ) -> dict:
        """
        Create a worktree and start a session for a work item.

        Returns dict with:
        - worktree_path: Path to the new worktree
        - branch: Branch name
        - parent_branch: Parent branch for merging
        - session_num: Assigned session number
        - success: bool
        """
        # Create the worktree
        actual_path, branch, parent_branch = self.worktree_manager.create_worktree(
            work_item_id, worktree_path
        )

        # Update work_items.json with git tracking
        self._update_work_item_git_info(
            work_item_id,
            branch=branch,
            parent_branch=parent_branch,
            worktree_path=actual_path
        )

        return {
            "worktree_path": actual_path,
            "branch": branch,
            "parent_branch": parent_branch,
            "success": True
        }

    def _update_work_item_git_info(
        self,
        work_item_id: str,
        branch: str,
        parent_branch: str,
        worktree_path: Path | None = None
    ):
        """Update work item with git tracking information."""
        # Read work items from shared location
        with open(self.paths.work_items_file) as f:
            data = json.load(f)

        work_item = data["work_items"].get(work_item_id)
        if not work_item:
            raise WorkItemNotFoundError(work_item_id)

        work_item["git"] = {
            "branch": branch,
            "parent_branch": parent_branch,
            "created_at": datetime.now().isoformat(),
            "status": "in_progress",
            "commits": [],
            "worktree_path": str(worktree_path) if worktree_path else None
        }

        # Write back to shared location
        with open(self.paths.work_items_file, 'w') as f:
            json.dump(data, f, indent=2)
```

### 5.5 Briefing Module Updates

**File**: `src/solokit/session/briefing.py` (modify)

Update `main()` to handle `--worktree` flag:

```python
def main(args) -> int:
    work_item_id = args.work_item_id
    worktree_path = getattr(args, 'worktree_path', None)
    use_worktree = getattr(args, 'worktree', False)

    paths = SessionPaths(Path.cwd())

    if use_worktree:
        return _start_in_worktree(work_item_id, worktree_path, paths, args)
    else:
        return _start_normal(work_item_id, paths, args)


def _start_in_worktree(
    work_item_id: str,
    worktree_path: Path | None,
    paths: SessionPaths,
    args
) -> int:
    """Start a session in a new worktree."""
    workflow = GitWorkflow(paths.working_dir)
    sessions = ActiveSessionsManager(paths)

    # 1. Validate work item exists
    work_item = _load_work_item(paths, work_item_id)
    if not work_item:
        raise WorkItemNotFoundError(work_item_id)

    # 2. Check if work item is already being worked on
    is_active, active_worktree = sessions.is_work_item_active(work_item_id)
    if is_active and not args.force:
        raise WorkItemActiveError(
            f"Work item {work_item_id} is already active in: {active_worktree}"
        )

    # 3. Create worktree
    result = workflow.start_work_item_in_worktree(work_item_id, worktree_path)
    print(f"Created worktree at {result['worktree_path']} with branch {result['branch']}")

    # 4. Start session (using the new worktree's path as key)
    new_worktree_paths = SessionPaths(result['worktree_path'])
    session_num = sessions.start_session(work_item_id, result['worktree_path'])

    # 5. Generate briefing
    briefing = generate_briefing(new_worktree_paths, work_item_id, work_item, session_num)

    # 6. Save briefing to shared location
    briefing_file = paths.briefings_dir / f"session_{session_num:03d}_briefing.md"
    briefing_file.write_text(briefing)

    # 7. Print briefing
    print(briefing)

    # 8. Print instructions
    print(f"\nTo continue working:\n  cd {result['worktree_path']}")

    return 0
```

### 5.6 CLI Updates

**File**: `src/solokit/cli.py` (modify)

Add `--worktree` and `--worktree-path` arguments:

```python
def setup_start_parser(subparsers):
    parser = subparsers.add_parser('start', help='Start a development session')
    parser.add_argument('work_item_id', nargs='?', help='Work item ID to start')
    parser.add_argument('--force', action='store_true', help='Force start even if another session is active')

    # New worktree arguments
    parser.add_argument(
        '--worktree',
        action='store_true',
        help='Create a git worktree for this work item'
    )
    parser.add_argument(
        '--worktree-path',
        type=Path,
        help='Custom path for the worktree (default: ../{repo}-{work_item_id})'
    )
```

---

## 6. Migration Strategy

### 6.1 Detection

When any Solokit command runs, check for:
1. `.git/solokit/` exists → New structure, proceed normally
2. `.session/` exists but no `.git/solokit/` → Old structure, offer migration
3. Neither exists → Fresh project, use new structure

### 6.2 Migration Steps

```python
def migrate_session_to_shared(project_root: Path) -> None:
    """Migrate from .session/ to .git/solokit/."""
    old_session = project_root / ".session"
    paths = SessionPaths(project_root)

    # Ensure new structure exists
    paths.ensure_structure()

    # Move tracking files
    old_tracking = old_session / "tracking"
    new_tracking = paths.solokit_root / "tracking"

    for file in ["work_items.json", "learnings.json", "stack.txt", "tree.txt",
                 "stack_updates.json", "tree_updates.json"]:
        old_file = old_tracking / file
        if old_file.exists():
            shutil.move(old_file, new_tracking / file)

    # Convert status_update.json to active_sessions.json
    old_status = old_tracking / "status_update.json"
    if old_status.exists():
        with open(old_status) as f:
            old_data = json.load(f)

        new_data = {
            "sessions": {},
            "next_session_num": _determine_next_session_num(old_session)
        }

        # If there was an active session, preserve it
        if old_data.get("status") == "in_progress":
            new_data["sessions"][str(project_root)] = {
                "work_item_id": old_data["current_work_item"],
                "session_num": old_data["current_session"],
                "started_at": old_data.get("started_at", datetime.now().isoformat()),
                "status": "in_progress"
            }

        with open(paths.active_sessions_file, 'w') as f:
            json.dump(new_data, f, indent=2)

        old_status.unlink()

    # Move specs
    old_specs = old_session / "specs"
    if old_specs.exists():
        for spec_file in old_specs.glob("*.md"):
            shutil.move(spec_file, paths.specs_dir / spec_file.name)
        old_specs.rmdir()

    # Move briefings
    old_briefings = old_session / "briefings"
    if old_briefings.exists():
        for briefing_file in old_briefings.glob("*.md"):
            shutil.move(briefing_file, paths.briefings_dir / briefing_file.name)
        old_briefings.rmdir()

    # Move history
    old_history = old_session / "history"
    if old_history.exists():
        for history_file in old_history.glob("*.md"):
            shutil.move(history_file, paths.history_dir / history_file.name)
        old_history.rmdir()

    # Move config
    old_config = old_session / "config.json"
    if old_config.exists():
        shutil.move(old_config, paths.config_file)

    # Clean up old .session directory
    # Leave a README for discoverability
    shutil.rmtree(old_session, ignore_errors=True)
    old_session.mkdir()
    (old_session / "README.md").write_text(
        "# Solokit Session Data\n\n"
        "Session data has been moved to `.git/solokit/` for worktree support.\n"
        "This directory is kept for backwards compatibility.\n"
    )
```

### 6.3 Backwards Compatibility

For a transition period, commands could check both locations:
1. Try `.git/solokit/` first (new)
2. Fall back to `.session/` (old)
3. Prompt for migration if old structure found

---

## 7. Configuration

### 7.1 New Config Options

Add to `config.json`:

```json
{
  "worktree": {
    "default_path_pattern": "../{repo}-{work_item}",
    "auto_remove_on_complete": false,
    "preserve_on_incomplete": true
  },
  // ... existing config
}
```

### 7.2 Config Schema Updates

Update `config.schema.json` to include worktree configuration.

---

## 8. Edge Cases and Error Handling

### 8.1 Worktree Path Conflicts

**Scenario**: User tries to create worktree at path that already exists.

**Handling**: Raise clear error with suggestion:
```
Error: Path already exists: ../solokit-feature_auth
Suggestion: Use --worktree-path to specify a different location
```

### 8.2 Work Item Already Active

**Scenario**: User tries to start a work item that's already active in another worktree.

**Handling**: Raise error with information about where it's active:
```
Error: Work item 'feature_auth' is already active
  Active in: /Users/ankush/Projects/solokit-feature_auth (Session #5)
  Use --force to start anyway (will end the other session)
```

### 8.3 Worktree Removed Externally

**Scenario**: User removes worktree via `git worktree remove` without using `/end`.

**Handling**:
- `active_sessions.json` still has entry for removed worktree
- Next command should detect orphaned session and clean up
- Add `sk status --cleanup` to manually clean orphaned sessions

### 8.4 Branch Already Exists

**Scenario**: User tries to create worktree but branch already exists (maybe from previous work).

**Handling**: Use existing branch for worktree (already implemented in `create_worktree`).

### 8.5 Concurrent Writes

**Scenario**: Two terminals running Solokit commands simultaneously.

**Handling**: File locking with `fcntl.flock()` ensures atomic read-modify-write operations.

### 8.6 Moved Worktree Directory

**Scenario**: User moves/renames worktree directory.

**Handling**:
- Session key becomes stale
- Commands in renamed worktree will see "no active session"
- User can restart session with `/start`
- Old entry cleaned up by `--cleanup` command

---

## 9. Testing Strategy

### 9.1 Unit Tests

- `SessionPaths` correctly resolves paths from main and worktrees
- `ActiveSessionsManager` handles concurrent access
- `WorktreeManager` creates/removes worktrees correctly
- Migration preserves all data

### 9.2 Integration Tests

- Full `/start --worktree` flow
- `/end` in worktree with PR creation
- Multiple concurrent sessions across worktrees
- Migration from old to new structure

### 9.3 Manual Testing Scenarios

1. Create worktree, work, complete session
2. Create multiple worktrees, work in parallel
3. Remove worktree mid-session, verify cleanup
4. Migrate existing project with active session
5. Cross-worktree learnings (add in one, visible in other)

---

## 10. Documentation Updates

### 10.1 Command Documentation

Update `docs/commands/start.md`:
- Add `--worktree` flag documentation
- Add `--worktree-path` flag documentation
- Add examples of worktree workflow

### 10.2 Architecture Documentation

Update `docs/ARCHITECTURE.md`:
- Document new `.git/solokit/` structure
- Explain shared vs. worktree-specific concepts
- Add diagram of worktree state management

### 10.3 User Guide

Create `docs/guides/PARALLEL_DEVELOPMENT.md`:
- When to use worktrees
- Complete worktree workflow example
- Tips for managing multiple active sessions

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure
1. Implement `SessionPaths` utility
2. Implement `ActiveSessionsManager`
3. Implement `WorktreeManager`
4. Add migration logic

### Phase 2: Command Updates
1. Update `/start` with `--worktree` flag
2. Update `/end` for worktree awareness
3. Update `/status` to show all active sessions
4. Update all other commands to use `SessionPaths`

### Phase 3: Polish
1. Add `--remove-worktree` to `/end`
2. Add `--cleanup` to `/status`
3. Update documentation
4. Add tests

---

## 12. Open Questions

1. **Spec file editing**: With specs in `.git/solokit/specs/`, should we add a helper command to open specs in editor?
   - Proposal: `sk specs feature_auth` opens the spec file

2. **Worktree naming in active_sessions.json**: Use absolute path or something more portable?
   - Current decision: Absolute path (simple, unambiguous)

3. **Session summary location**: Should summaries note which worktree they came from?
   - Proposal: Add `worktree_path` field to session metadata

4. **Stack/tree per worktree**: Should each worktree have its own stack.txt/tree.txt since they may be on different branches?
   - Proposal: Keep single shared version, regenerate on demand

---

## 13. Success Criteria

- [ ] User can run `sk start feature_auth --worktree` and get a functional worktree
- [ ] Multiple worktrees can have active sessions simultaneously
- [ ] All commands work correctly from any worktree
- [ ] Learnings added in one worktree are visible in others
- [ ] Existing projects can be migrated without data loss
- [ ] Session numbers are globally unique and never conflict
- [ ] Worktree removal (via /end or git command) is handled gracefully

---

## 14. References

- [Git Worktrees Documentation](https://git-scm.com/docs/git-worktree)
- `git rev-parse --git-common-dir` - Returns shared .git directory
- `git rev-parse --show-toplevel` - Returns worktree root
- `git worktree list --porcelain` - Machine-readable worktree list
