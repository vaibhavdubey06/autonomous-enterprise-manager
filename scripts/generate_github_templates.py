import os

ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", ".github")
ISSUE_DIR = os.path.join(ROOT_DIR, "ISSUE_TEMPLATE")
WF_DIR = os.path.join(ROOT_DIR, "workflows")

os.makedirs(ISSUE_DIR, exist_ok=True)
os.makedirs(WF_DIR, exist_ok=True)

files = {
    "PULL_REQUEST_TEMPLATE.md": """## Description
Please include a summary of the change and which issue is fixed.

Fixes # (issue)

## Checklist:
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published in downstream modules

## Breaking Changes
- [ ] Yes
- [ ] No
""",
    "ISSUE_TEMPLATE/bug_report.md": """---
name: Bug report
about: Create a report to help us improve
title: "[BUG] "
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Desktop (please complete the following information):**
 - OS: [e.g. iOS]
 - Browser [e.g. chrome, safari]
 - Version [e.g. 22]
""",
    "ISSUE_TEMPLATE/feature_request.md": """---
name: Feature request
about: Suggest an idea for this project
title: "[FEATURE] "
labels: enhancement
assignees: ''

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.
""",
    "ISSUE_TEMPLATE/documentation.md": """---
name: Documentation
about: Request or provide documentation updates
title: "[DOCS] "
labels: documentation
assignees: ''

---

**Describe the documentation issue**
A clear and concise description of what is missing, unclear, or incorrect.

**Where should this be documented?**
Link to the specific page or section, or suggest a new page.
""",
    "workflows/ci.yml": """name: CI

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    - name: Install dependencies
      run: uv sync
    - name: Lint with Ruff
      run: uv run ruff check .
    - name: Test with pytest
      run: uv run pytest tests/ -v
"""
}

for path, content in files.items():
    filepath = os.path.join(ROOT_DIR, path)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("GitHub templates generated.")
