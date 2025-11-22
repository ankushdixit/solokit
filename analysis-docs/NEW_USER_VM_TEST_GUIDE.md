# New User VM Testing Guide

This guide simulates a new user experience with Solokit on a fresh VM to identify installation and setup issues.

## Overview

**Goal:** Test the complete new user journey:
1. Install Solokit from scratch
2. Initialize tier-4 projects with all options
3. Run CI checks and identify failures
4. Document issues for fixing

**Test Projects:**
1. `fullstack_nextjs` - tier-4, all options
2. `saas_t3` - tier-4, all options
3. `dashboard_refine` - tier-4, all options
4. `ml_ai_fastapi` - tier-4, all options (Python stack)

---

## Step 1: Create GCP VM

```bash
# Create a fresh Ubuntu VM (same as new user would use)
gcloud compute instances create solokit-new-user-test \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd

# Wait for VM to be ready
sleep 30

# SSH into the VM
gcloud compute ssh solokit-new-user-test --zone=us-central1-a
```

---

## Step 2: Install Prerequisites (As New User Would)

Once SSH'd into the VM, run these commands:

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Node.js 20 LTS (from NodeSource - recommended for new users)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify Node.js
node --version  # Should be v20.x
npm --version   # Should be 10.x

# Install Python 3.11+ (for ml_ai_fastapi stack)
sudo apt-get install -y python3.11 python3.11-venv python3-pip

# Create symlinks
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 100
sudo ln -sf /usr/bin/python3.11 /usr/bin/python

# Verify Python
python3 --version  # Should be 3.11.x

# Install git
sudo apt-get install -y git

# Configure git (required for sk init)
git config --global user.email "newuser@example.com"
git config --global user.name "New User"
```

---

## Step 3: Install Solokit

### Option A: Clone from GitHub (Recommended for testing released code)

**On the VM**, run:

```bash
# Clone solokit from GitHub
cd ~
git clone https://github.com/ankushdixit/solokit.git solokit-source

# Create a Python virtual environment for solokit
python3 -m venv ~/solokit-env
source ~/solokit-env/bin/activate

# Install solokit from source
cd ~/solokit-source
pip install -e .

# Verify installation
sk --version
sk --help
```

### Option B: Upload from Local Machine (For testing uncommitted changes)

Use this option when you have local changes that haven't been pushed to GitHub yet.

**From your LOCAL machine** (not the VM), run:

```bash
# First, clean up macOS resource fork files
cd ~/Projects/solokit
find . -name '._*' -delete 2>/dev/null

# Create tarball of your local solokit (includes uncommitted changes)
# Use COPYFILE_DISABLE to prevent macOS from adding resource forks
COPYFILE_DISABLE=1 tar -czf /tmp/solokit-local.tar.gz \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='*.pyc' \
  --exclude='.DS_Store' \
  --exclude='._*' \
  --exclude='test_results' \
  .

# Upload to VM
gcloud compute scp /tmp/solokit-local.tar.gz solokit-new-user-test:~/ --zone=us-central1-a

# Cleanup local tarball
rm /tmp/solokit-local.tar.gz
```

**Then on the VM**, run:

```bash
# Extract solokit
mkdir -p ~/solokit-source
tar -xzf ~/solokit-local.tar.gz -C ~/solokit-source
rm ~/solokit-local.tar.gz

# Create a Python virtual environment for solokit
python3 -m venv ~/solokit-env
source ~/solokit-env/bin/activate

# Install solokit from local source
cd ~/solokit-source
pip install -e .

# Verify installation
sk --version
sk --help
```

---

## Step 4: Test Project 1 - fullstack_nextjs

```bash
# Create test directory
mkdir -p ~/test-projects
cd ~/test-projects

# Create project directory
mkdir test-fullstack-nextjs
cd test-fullstack-nextjs

# Initialize with tier-4 and all options
echo "=========================================="
echo "TEST 1: fullstack_nextjs tier-4 all options"
echo "=========================================="

sk init \
  --template fullstack_nextjs \
  --tier tier-4-production \
  --options ci_cd,docker,env_templates,a11y \
  --coverage 80

# Check what was installed
echo ""
echo "--- Checking installed files ---"
ls -la
ls -la .github/workflows/ 2>/dev/null || echo "No workflows directory"
cat package.json | grep -A 50 '"scripts"' | head -60

# Check if Playwright browsers were installed
echo ""
echo "--- Checking Playwright browsers ---"
ls -la ~/.cache/ms-playwright/ 2>/dev/null || echo "No Playwright browsers found in cache"
npx playwright --version 2>/dev/null || echo "Playwright not available"

# Try to run CI checks manually
echo ""
echo "--- Running CI checks ---"

echo "1. Lint check..."
npm run lint 2>&1 | tail -20

echo ""
echo "2. Type check..."
npm run type-check 2>&1 | tail -20

echo ""
echo "3. Format check..."
npm run format:check 2>&1 | tail -20

echo ""
echo "4. Unit tests..."
npm run test 2>&1 | tail -20

echo ""
echo "5. Build..."
npm run build 2>&1 | tail -20

echo ""
echo "6. E2E tests (requires Playwright browsers)..."
npm run test:e2e 2>&1 | tail -30

echo ""
echo "7. A11y tests (requires Playwright browsers)..."
npm run test:a11y 2>&1 | tail -30

echo ""
echo "8. Lighthouse CI..."
npm run lighthouse 2>&1 | tail -30

# Record results
echo ""
echo "=========================================="
echo "TEST 1 COMPLETE - Check output above for failures"
echo "=========================================="
```

---

## Step 5: Test Project 2 - saas_t3

```bash
cd ~/test-projects
mkdir test-saas-t3
cd test-saas-t3

echo "=========================================="
echo "TEST 2: saas_t3 tier-4 all options"
echo "=========================================="

sk init \
  --template saas_t3 \
  --tier tier-4-production \
  --options ci_cd,docker,env_templates,a11y \
  --coverage 80

# Run same checks
echo ""
echo "--- Running CI checks ---"

npm run lint 2>&1 | tail -20
npm run type-check 2>&1 | tail -20
npm run format:check 2>&1 | tail -20
npm run test 2>&1 | tail -20
npm run build 2>&1 | tail -20
npm run test:e2e 2>&1 | tail -30
npm run test:a11y 2>&1 | tail -30
npm run lighthouse 2>&1 | tail -30

echo "=========================================="
echo "TEST 2 COMPLETE"
echo "=========================================="
```

---

## Step 6: Test Project 3 - dashboard_refine

```bash
cd ~/test-projects
mkdir test-dashboard-refine
cd test-dashboard-refine

echo "=========================================="
echo "TEST 3: dashboard_refine tier-4 all options"
echo "=========================================="

sk init \
  --template dashboard_refine \
  --tier tier-4-production \
  --options ci_cd,docker,env_templates,a11y \
  --coverage 80

# Run same checks
echo ""
echo "--- Running CI checks ---"

npm run lint 2>&1 | tail -20
npm run type-check 2>&1 | tail -20
npm run format:check 2>&1 | tail -20
npm run test 2>&1 | tail -20
npm run build 2>&1 | tail -20
npm run test:e2e 2>&1 | tail -30
npm run test:a11y 2>&1 | tail -30
npm run lighthouse 2>&1 | tail -30

echo "=========================================="
echo "TEST 3 COMPLETE"
echo "=========================================="
```

---

## Step 7: Test Project 4 - ml_ai_fastapi (Python)

```bash
cd ~/test-projects
mkdir test-ml-ai-fastapi
cd test-ml-ai-fastapi

echo "=========================================="
echo "TEST 4: ml_ai_fastapi tier-4 all options"
echo "=========================================="

sk init \
  --template ml_ai_fastapi \
  --tier tier-4-production \
  --options ci_cd,docker,env_templates \
  --coverage 80

# Check Python environment
echo ""
echo "--- Checking Python environment ---"
ls -la venv/ 2>/dev/null || echo "No venv directory"
source venv/bin/activate 2>/dev/null || echo "Cannot activate venv"

# Run Python CI checks
echo ""
echo "--- Running CI checks ---"

echo "1. Ruff lint..."
venv/bin/ruff check src/ tests/ 2>&1 | tail -20

echo ""
echo "2. Pyright type check..."
venv/bin/pyright 2>&1 | tail -20

echo ""
echo "3. Pytest..."
venv/bin/pytest -v 2>&1 | tail -30

echo ""
echo "4. Bandit security..."
venv/bin/bandit -r src/ 2>&1 | tail -20

echo "=========================================="
echo "TEST 4 COMPLETE"
echo "=========================================="
```

---

## Step 8: Full Workflow Test (Optional)

Test the complete solokit workflow on one project:

```bash
cd ~/test-projects/test-fullstack-nextjs

# Create a work item
sk work-new --type feature --title "Test Feature" --priority high

# Get the work item ID
WORK_ID=$(cat .session/tracking/work_items.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d['work_items'].keys())[-1])")
echo "Work item ID: $WORK_ID"

# Start session
sk start $WORK_ID

# Create sample code
mkdir -p lib
cat > lib/test-feature.ts << 'EOF'
export function add(a: number, b: number): number {
  return a + b;
}
EOF

mkdir -p tests
cat > tests/test-feature.test.ts << 'EOF'
import { add } from '../lib/test-feature';

describe('add', () => {
  it('should add two numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
});
EOF

# Commit changes
git add .
git commit -m "Add test feature"

# Validate session
sk validate

# End session
sk end --incomplete
```

---

## Step 9: Document Issues

Create a file to track all issues found:

```bash
cat > ~/test-projects/ISSUES_FOUND.md << 'EOF'
# Issues Found During New User Testing

## Date: $(date)

## Environment
- OS: Ubuntu 22.04 LTS (GCP VM)
- Node.js: $(node --version)
- Python: $(python3 --version)
- Solokit: $(sk --version 2>/dev/null || echo "unknown")

## Issues by Project

### 1. fullstack_nextjs
- [ ] Issue 1: ...
- [ ] Issue 2: ...

### 2. saas_t3
- [ ] Issue 1: ...
- [ ] Issue 2: ...

### 3. dashboard_refine
- [ ] Issue 1: ...
- [ ] Issue 2: ...

### 4. ml_ai_fastapi
- [ ] Issue 1: ...
- [ ] Issue 2: ...

## Common Issues (All Projects)
- [ ] Playwright browsers not installed automatically
- [ ] ...

## Recommendations
1. ...
2. ...
EOF

# Edit the file with actual issues
nano ~/test-projects/ISSUES_FOUND.md
```

---

## Step 10: Cleanup

```bash
# Exit VM
exit

# Delete VM when done (IMPORTANT - saves cost!)
gcloud compute instances delete solokit-new-user-test --zone=us-central1-a --quiet
```

---

## Quick Reference Commands

### Create VM
```bash
gcloud compute instances create solokit-new-user-test \
  --machine-type=e2-standard-4 \
  --zone=us-central1-a \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB
```

### SSH into VM
```bash
gcloud compute ssh solokit-new-user-test --zone=us-central1-a
```

### Clone solokit from GitHub (on VM)
```bash
cd ~ && git clone https://github.com/ankushdixit/solokit.git solokit-source
python3 -m venv ~/solokit-env && source ~/solokit-env/bin/activate
cd ~/solokit-source && pip install -e .
```

### Upload local solokit (with uncommitted changes)
```bash
# From LOCAL machine - clean macOS files first, then create tarball
cd ~/Projects/solokit
find . -name '._*' -delete 2>/dev/null
COPYFILE_DISABLE=1 tar -czf /tmp/solokit-local.tar.gz \
  --exclude='.git' --exclude='node_modules' --exclude='venv' \
  --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
  --exclude='.DS_Store' --exclude='._*' --exclude='test_results' .
gcloud compute scp /tmp/solokit-local.tar.gz solokit-new-user-test:~/ --zone=us-central1-a
rm /tmp/solokit-local.tar.gz
```

### Delete VM
```bash
gcloud compute instances delete solokit-new-user-test --zone=us-central1-a --quiet
```

### Copy files from VM
```bash
gcloud compute scp solokit-new-user-test:~/test-projects/ISSUES_FOUND.md . --zone=us-central1-a
```

---

## Expected Issues to Look For

1. **Playwright browsers not installed**
   - E2E tests fail with "Executable doesn't exist" error
   - Fix: Run `npx playwright install` or `npx playwright install --with-deps`

2. **Missing system dependencies for Playwright**
   - Browsers installed but fail to launch
   - Fix: Run `sudo npx playwright install-deps`

3. **Lighthouse CI fails**
   - Chrome not available for Lighthouse
   - Fix: Ensure Playwright browsers are installed

4. **Python venv issues**
   - Packages not found in venv
   - Fix: Check venv activation and pip install

5. **Git hooks fail**
   - Husky not properly initialized
   - Fix: Run `npm run prepare`

6. **Build fails**
   - Missing environment variables
   - Fix: Copy `.env.example` to `.env`
