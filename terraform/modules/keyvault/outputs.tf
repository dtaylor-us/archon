output "name" {
  description = "Name of the Azure Key Vault."
  value       = azurerm_key_vault.main.name
}

output "uri" {
  description = "URI of the Azure Key Vault. Format: https://<name>.vault.azure.net/"
  value       = azurerm_key_vault.main.vault_uri
}
