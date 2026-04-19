#!/usr/bin/env bash
# ADL-015: Agent Orchestration Service — Prompt Template Isolation (Soft enforcement)
#
# Scans all Python files under app/tools/ for string literals longer than
# 200 characters and flags them as inline prompt templates that should be
# moved to Jinja2 files in app/prompts/. Exits with code 1 if any match
# is found.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$REPO_ROOT/ai-architect-agent/app/tools"
MAX_LEN=200

echo "=== ADL-015: Checking for inline prompt strings (>${MAX_LEN} chars) in app/tools/ ==="

VIOLATIONS=0

# Search for long string literals in Python files under tools/
# Match triple-quoted strings and single-line strings exceeding MAX_LEN chars
while IFS= read -r -d '' pyfile; do
  # Use Python to parse and detect long string literals (excluding docstrings)
  python3 -c "
import ast, sys

with open('$pyfile') as f:
    source = f.read()

try:
    tree = ast.parse(source)
except SyntaxError:
    sys.exit(0)

# Collect line numbers of docstrings so we can skip them.
# A docstring is an ast.Expr whose value is an ast.Constant(str)
# that appears as the first statement of a module, class, or function body.
docstring_lines = set()
for node in ast.walk(tree):
    body = None
    if isinstance(node, ast.Module):
        body = node.body
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        docstring_lines.add(body[0].value.lineno)

violations = []
for node in ast.walk(tree):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if len(node.value) > $MAX_LEN and node.lineno not in docstring_lines:
            violations.append((node.lineno, len(node.value)))

if violations:
    for lineno, length in violations:
        print(f'  {sys.argv[1]}:{lineno} — string literal of {length} chars (max {$MAX_LEN})')
    sys.exit(1)
" "$pyfile" && true || VIOLATIONS=$((VIOLATIONS + 1))
done < <(find "$TOOLS_DIR" -name '*.py' -not -name '__*' -print0)

if [ "$VIOLATIONS" -gt 0 ]; then
  echo "FAILED: $VIOLATIONS file(s) contain inline prompt strings exceeding $MAX_LEN characters"
  echo "Move long strings to Jinja2 templates in app/prompts/"
  exit 1
else
  echo "PASSED: No inline prompt strings exceeding $MAX_LEN characters found"
  exit 0
fi
