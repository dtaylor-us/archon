output "acr_id" {
  description = "Full Azure resource ID of the Container Registry. Passed to AKS for AcrPull role assignment."
  value       = azurerm_container_registry.main.id
}

output "login_server" {
  description = "ACR login server hostname. Format: <name>.azurecr.io. Used in image references."
  value       = azurerm_container_registry.main.login_server
}

output "name" {
  description = "Short name of the Container Registry (without .azurecr.io)."
  value       = azurerm_container_registry.main.name
}
