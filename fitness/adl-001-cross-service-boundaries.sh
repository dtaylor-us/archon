#!/usr/bin/env bash
# ADL-001: System and Service Boundaries (Soft enforcement)
#
# Verifies no source file in any of the three services imports from another
# service's root namespace or module path. Exits with code 1 if a
# cross-service import is found.
#
# Services:
#   API Gateway     — ai-architect-api/src  (Java: com.aiarchitect.api)
#   Agent           — ai-architect-agent/app (Python: app)
#   UI              — ai-architect-ui/src    (TypeScript: ui/src)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

VIOLATIONS=0

echo "=== ADL-001: Checking cross-service import boundaries ==="

# 1. API Gateway must not import from Agent or UI
echo "-- Checking API Gateway for cross-service imports..."
if grep -rn --include='*.java' \
    -e 'import app\.' \
    -e 'from app ' \
    -e "from ['\"].*ai-architect-agent" \
    -e "from ['\"].*ai-architect-ui" \
    "$REPO_ROOT/ai-architect-api/src" 2>/dev/null; then
  echo "VIOLATION: API Gateway imports from Agent or UI service"
  VIOLATIONS=$((VIOLATIONS + 1))
fi

# 2. Agent must not import from API Gateway or UI
echo "-- Checking Agent for cross-service imports..."
if grep -rn --include='*.py' \
    -e 'import com\.aiarchitect' \
    -e 'from com\.aiarchitect' \
    -e 'from ai_architect_api' \
    -e 'import ai_architect_api' \
    -e 'from ai_architect_ui' \
    -e 'import ai_architect_ui' \
    "$REPO_ROOT/ai-architect-agent/app" 2>/dev/null; then
  echo "VIOLATION: Agent imports from API Gateway or UI service"
  VIOLATIONS=$((VIOLATIONS + 1))
fi

# 3. UI must not import from API Gateway or Agent
echo "-- Checking UI for cross-service imports..."
if grep -rn --include='*.ts' --include='*.tsx' \
    -e 'from.*ai-architect-api' \
    -e 'from.*ai-architect-agent' \
    -e 'import.*com\.aiarchitect' \
    -e "from ['\"]app\." \
    "$REPO_ROOT/ai-architect-ui/src" 2>/dev/null; then
  echo "VIOLATION: UI imports from API Gateway or Agent service"
  VIOLATIONS=$((VIOLATIONS + 1))
fi

if [ "$VIOLATIONS" -gt 0 ]; then
  echo "FAILED: $VIOLATIONS cross-service import violation(s) found"
  exit 1
else
  echo "PASSED: No cross-service imports detected"
  exit 0
fi
