#!/usr/bin/env bash
# scripts/post-terraform.sh
#
# Runs after `terraform apply` to install Kubernetes components that
# Terraform cannot manage directly:
#   - nginx ingress controller
#   - cert-manager
#   - Azure Key Vault CSI driver
#   - ai-architect application namespace
#
# Idempotent — uses `helm upgrade --install` throughout.
# Safe to re-run if any step was interrupted.

set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; }
header()  { echo -e "\n${BOLD}${BLUE}══ $* ══${RESET}"; }

# Determine the repo root (the directory containing this script's parent).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ─── Step 1: Source .deployment-config if present ─────────────────────────────
header "Step 1 — Loading configuration"

if [[ -f "${REPO_ROOT}/.deployment-config" ]]; then
  # shellcheck source=/dev/null
  source "${REPO_ROOT}/.deployment-config"
  success "Loaded .deployment-config"
else
  warn ".deployment-config not found — assuming environment variables are set."
fi

# ─── Step 2: Configure kubectl ────────────────────────────────────────────────
header "Step 2 — Configuring kubectl"

info "Fetching AKS credentials from Terraform output..."
pushd "${REPO_ROOT}/terraform" > /dev/null
  GET_CREDENTIALS_CMD="$(terraform output -raw get_credentials_command 2>/dev/null || true)"
popd > /dev/null

if [[ -z "${GET_CREDENTIALS_CMD}" ]]; then
  error "Could not read get_credentials_command from Terraform output."
  error "Ensure 'terraform apply' has completed successfully before running this script."
  exit 1
fi

info "Running: ${GET_CREDENTIALS_CMD}"
eval "${GET_CREDENTIALS_CMD}"
success "kubectl configured for AKS cluster."

# ─── Step 3: Install nginx ingress controller ─────────────────────────────────
header "Step 3 — Installing nginx ingress controller"

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx 2>/dev/null || true
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set "controller.service.annotations.service\.beta\.kubernetes\.io/azure-load-balancer-health-probe-request-path=/healthz" \
  --wait \
  --timeout 5m

success "nginx ingress controller installed."

# ─── Step 4: Install cert-manager ─────────────────────────────────────────────
header "Step 4 — Installing cert-manager"

helm repo add jetstack https://charts.jetstack.io 2>/dev/null || true
helm repo update

helm upgrade --install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true \
  --wait \
  --timeout 5m

success "cert-manager installed."

# ─── Step 5: Install Azure Key Vault CSI driver ───────────────────────────────
header "Step 5 — Installing Azure Key Vault CSI driver"

# The AKS cluster was provisioned with the key_vault_secrets_provider add-on,
# which installs the CSI driver natively. A separate Helm install would conflict.
if kubectl get csidriver secrets-store.csi.k8s.io &>/dev/null; then
  success "Azure Key Vault CSI driver already present (AKS add-on)."
else
  helm repo add csi-secrets-store-provider-azure \
    https://azure.github.io/secrets-store-csi-driver-provider-azure/charts 2>/dev/null || true
  helm repo update
  helm upgrade --install csi-secrets-store-provider-azure \
    csi-secrets-store-provider-azure/csi-secrets-store-provider-azure \
    --namespace kube-system \
    --wait \
    --timeout 5m
  success "Azure Key Vault CSI driver installed via Helm."
fi

# ─── Step 6: Create application namespace ────────────────────────────────────
header "Step 6 — Creating application namespace"

# --dry-run=client + apply is idempotent because it will not error if the
# namespace already exists — it simply re-applies the unchanged object.
kubectl create namespace ai-architect --dry-run=client -o yaml \
  | kubectl apply -f -

success "Namespace 'ai-architect' ready."

# ─── Step 7: Wait for ingress external IP ─────────────────────────────────────
header "Step 7 — Waiting for ingress external IP"

# Maximum wait time: 3 minutes (18 polls × 10 seconds each)
MAX_POLLS=18
POLL_INTERVAL=10
EXTERNAL_IP=""

info "Waiting for the Azure Load Balancer to assign an external IP..."
info "(This can take 1–3 minutes)"

for ((i = 1; i <= MAX_POLLS; i++)); do
  EXTERNAL_IP="$(kubectl get service ingress-nginx-controller \
    --namespace ingress-nginx \
    --template '{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}' 2>/dev/null || true)"

  if [[ -n "$EXTERNAL_IP" ]]; then
    break
  fi

  printf "."
  sleep "$POLL_INTERVAL"
done
echo ""  # newline after progress dots

if [[ -z "$EXTERNAL_IP" ]]; then
  warn "Timed out waiting for external IP after $((MAX_POLLS * POLL_INTERVAL)) seconds."
  warn "The Load Balancer may still be provisioning. Check again with:"
  warn "  kubectl get service ingress-nginx-controller -n ingress-nginx"
else
  success "External IP assigned: ${EXTERNAL_IP}"
fi

# ─── Step 8: Print final summary ──────────────────────────────────────────────
header "Step 8 — Summary"

echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}${BOLD}║           Post-Terraform setup completed!                    ║${RESET}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${BOLD}Installed:${RESET}"
echo "  ✓ nginx Ingress Controller  (namespace: ingress-nginx)"
echo "  ✓ cert-manager              (namespace: cert-manager)"
echo "  ✓ Azure Key Vault CSI       (namespace: kube-system)"
echo "  ✓ Application namespace:    ai-architect"
echo ""

if [[ -n "$EXTERNAL_IP" ]]; then
  echo -e "${BOLD}Your application entry point:${RESET}"
  echo ""
  echo "  External IP:   ${EXTERNAL_IP}"
  echo ""
  echo "  If you have a domain, create an A record:"
  echo "    Host: aiarchitect  (or @)  →  IP: ${EXTERNAL_IP}"
  echo ""
  echo "  If you do not have a domain, use nip.io right now:"
  echo "    http://aiarchitect.${EXTERNAL_IP}.nip.io"
  echo ""
  echo "  nip.io resolves *.1.2.3.4.nip.io to 1.2.3.4 — no DNS setup needed."
fi

echo -e "${BOLD}Next step:${RESET}"
echo "  Add the GitHub Secrets listed by the bootstrap script, then push to main:"
echo "    git add ."
echo "    git commit -m \"Add deployment configuration\""
echo "    git push origin main"
echo ""
echo "  The CI/CD pipeline will build and deploy your application automatically."
echo ""
