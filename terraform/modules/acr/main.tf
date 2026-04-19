# ACR name must be globally unique and alphanumeric only (no hyphens).
# This is an Azure Container Registry naming requirement.
resource "azurerm_container_registry" "main" {
  name                = "acr${var.project}${var.environment}${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  # Use managed identity authentication — admin credentials are disabled.
  # AKS pulls images via the AcrPull role assignment in the AKS module.
  admin_enabled = false

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}
