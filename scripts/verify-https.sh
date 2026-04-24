#!/usr/bin/env bash
# scripts/verify-https.sh
#
# Verifies that end-to-end HTTPS is working correctly after deployment.
# Run this script after completing post-terraform.sh and the first helm deploy.
#
# Checks performed:
#   1. Ingress resource is present and has a host configured
#   2. cert-manager Certificate object exists and shows its READY condition
#   3. Detailed certificate status for debugging
#   4. TLS secret created by cert-manager is present
#   5. HTTP to HTTPS redirect returns 301 or 308
#   6. HTTPS endpoint responds with 200 or 304
#
# If the certificate is still being issued, wait 2 minutes and re-run.
# Use scripts/switch-to-prod-tls.sh once the staging cert is verified READY.

set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Archon HTTPS verification ==="
echo ""

# ─── Load configuration ────────────────────────────────────────────────────────
if [[ -f "${REPO_ROOT}/.deployment-config" ]]; then
  # shellcheck source=/dev/null
  source "${REPO_ROOT}/.deployment-config"
fi

# ─── Derive standard names from PROJECT_NAME / ENVIRONMENT if not explicit ────
PROJECT_NAME="${PROJECT_NAME:-}"
ENVIRONMENT="${ENVIRONMENT:-}"

AZURE_RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-rg-${PROJECT_NAME}-${ENVIRONMENT}}"
AKS_CLUSTER_NAME="${AKS_CLUSTER_NAME:-aks-${PROJECT_NAME}-${ENVIRONMENT}}"

# ─── Final guard ──────────────────────────────────────────────────────────────
if [[ -z "${PROJECT_NAME}" ]] || [[ -z "${ENVIRONMENT}" ]]; then
  if [[ -z "${AZURE_RESOURCE_GROUP}" ]] || [[ "${AZURE_RESOURCE_GROUP}" == "rg--" ]]; then
    error "Cannot determine AZURE_RESOURCE_GROUP. Set PROJECT_NAME and ENVIRONMENT or export AZURE_RESOURCE_GROUP directly."
    exit 1
  fi
fi

# Refresh AKS credentials silently — kubeconfig may be stale.
az aks get-credentials \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AKS_CLUSTER_NAME}" \
  --overwrite-existing 2>/dev/null

# ─── Check 1: Ingress status ──────────────────────────────────────────────────
echo "1. Ingress status"
kubectl get ingress -n ai-architect
echo ""

# ─── Check 2: Certificate status ─────────────────────────────────────────────
echo "2. Certificate status"
kubectl get certificate -n ai-architect
echo ""

# ─── Check 3: Certificate detail ─────────────────────────────────────────────
echo "3. Certificate detail"
kubectl describe certificate ai-architect-tls \
  -n ai-architect 2>/dev/null | grep -A5 "Status:" || true
echo ""

# ─── Check 4: TLS secret exists ──────────────────────────────────────────────
echo "4. TLS secret exists"
kubectl get secret ai-architect-tls \
  -n ai-architect 2>/dev/null \
  && success "TLS secret present" \
  || warn "TLS secret not yet created — certificate may still be issuing"
echo ""

# ─── Check 5: HTTP redirect check ────────────────────────────────────────────
echo "5. HTTP redirect check"
INGRESS_IP=$(kubectl get ingress \
  --namespace ai-architect \
  --output jsonpath='{.items[0].status.loadBalancer.ingress[0].ip}' \
  2>/dev/null || echo "")

if [[ -n "$INGRESS_IP" ]]; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 5 "http://$INGRESS_IP" 2>/dev/null || echo "000")
  if [[ "$HTTP_CODE" == "301" || "$HTTP_CODE" == "308" ]]; then
    success "HTTP redirect working (status ${HTTP_CODE})"
  elif [[ "$HTTP_CODE" == "000" ]]; then
    warn "Could not reach ${INGRESS_IP} — check that nginx is running"
  else
    warn "Unexpected HTTP status: ${HTTP_CODE} (expected 301 or 308)"
  fi
else
  warn "Could not determine ingress IP"
fi
echo ""

# ─── Check 6: HTTPS connectivity check ────────────────────────────────────────
echo "6. HTTPS connectivity check"
HOST=$(kubectl get ingress \
  --namespace ai-architect \
  --output jsonpath='{.items[0].spec.rules[0].host}' \
  2>/dev/null || echo "")

if [[ -n "$HOST" && -n "$INGRESS_IP" ]]; then
  # --resolve overrides DNS so the check works even before DNS propagation,
  # using the ingress IP directly while still sending the correct Host header.
  HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 10 "https://$HOST" \
    --resolve "${HOST}:443:${INGRESS_IP}" \
    2>/dev/null || echo "000")
  if [[ "$HTTPS_CODE" == "200" || "$HTTPS_CODE" == "304" ]]; then
    success "HTTPS working — status ${HTTPS_CODE}"
    echo "  Application is accessible at: https://${HOST}"
  elif [[ "$HTTPS_CODE" == "000" ]]; then
    warn "Could not reach https://${HOST}"
    warn "Certificate may still be issuing — wait 1-2 minutes and retry"
  else
    warn "HTTPS returned status ${HTTPS_CODE}"
  fi
elif [[ -z "$HOST" ]]; then
  warn "Could not determine ingress host"
fi

echo ""
echo "=== Verification complete ==="
echo ""
echo "If certificate is still issuing, wait 2 minutes and re-run this script."
echo ""
echo "To switch from staging to production cert (run once staging is READY):"
echo "  ./scripts/switch-to-prod-tls.sh"
