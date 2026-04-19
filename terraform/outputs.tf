output "resource_group_name" {
  description = "Name of the Azure Resource Group containing all application resources."
  value       = azurerm_resource_group.main.name
}

output "acr_login_server" {
  description = "ACR login server URL for Docker push and Helm chart image references. Format: <name>.azurecr.io"
  value       = module.acr.login_server
}

output "acr_name" {
  description = "Short name of the Azure Container Registry (without .azurecr.io suffix)."
  value       = module.acr.name
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster. Use with az aks get-credentials."
  value       = module.aks.cluster_name
}

output "key_vault_name" {
  description = "Name of the Azure Key Vault storing all application secrets."
  value       = module.keyvault.name
}

output "key_vault_uri" {
  description = "URI of the Azure Key Vault. Format: https://<name>.vault.azure.net/"
  value       = module.keyvault.uri
}

output "key_vault_tenant_id" {
  description = "Azure AD tenant ID where the Key Vault is registered. Required by the AKS CSI driver."
  value       = data.azurerm_client_config.current.tenant_id
}

output "aks_kubelet_client_id" {
  description = "Managed identity client ID for the AKS kubelet. Required by the Key Vault CSI driver to authenticate to Key Vault."
  value       = module.aks.kubelet_identity_client_id
}

output "db_fqdn" {
  description = "Fully qualified domain name of the PostgreSQL Flexible Server."
  value       = module.database.fqdn
}

output "get_credentials_command" {
  description = "Run this command to configure kubectl for the AKS cluster after apply."
  value = join(" ", [
    "az aks get-credentials",
    "--resource-group", azurerm_resource_group.main.name,
    "--name", module.aks.cluster_name
  ])
}

output "github_secrets_summary" {
  description = "Copy-paste this block into GitHub Secrets. Each pair shows the exact secret name and value."
  value       = <<-EOT
    Secret: AZURE_RESOURCE_GROUP
    Value:  ${azurerm_resource_group.main.name}

    Secret: ACR_LOGIN_SERVER
    Value:  ${module.acr.login_server}

    Secret: ACR_NAME
    Value:  ${module.acr.name}

    Secret: AKS_CLUSTER_NAME
    Value:  ${module.aks.cluster_name}

    Secret: KEY_VAULT_NAME
    Value:  ${module.keyvault.name}

    Secret: KEY_VAULT_TENANT_ID
    Value:  ${data.azurerm_client_config.current.tenant_id}

    Secret: AKS_KUBELET_CLIENT_ID
    Value:  ${module.aks.kubelet_identity_client_id}
  EOT
}
