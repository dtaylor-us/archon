variable "resource_group_name" {
  type        = string
  description = "Name of the Resource Group where the Key Vault is created."
}

variable "location" {
  type        = string
  description = "Azure region for the Key Vault."
}

variable "project" {
  type        = string
  description = "Short project name used in the Key Vault name."
}

variable "environment" {
  type        = string
  description = "Environment name (dev, prod) used in the Key Vault name."
}

variable "tenant_id" {
  type        = string
  description = "Azure AD tenant ID. Obtained from data.azurerm_client_config.current.tenant_id in the root module."
}

variable "deployer_object_id" {
  type        = string
  description = "Object ID of the deployer (user or CI runner). Granted Key Vault Administrator to write secrets during apply."
}

variable "aks_kubelet_identity_object_id" {
  type        = string
  description = "Object ID of the AKS kubelet managed identity. Granted Key Vault Secrets User to read secrets at runtime."
}

variable "github_actions_sp_object_id" {
  type        = string
  default     = ""
  description = "Object ID of the GitHub Actions service principal. When set, grants Key Vault Secrets User. Leave empty if not needed."
}

variable "purge_protection" {
  type        = bool
  default     = false
  description = "Enable purge protection on the Key Vault. Set to true for production — prevents permanent deletion for the retention period."
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL administrator password to store in Key Vault."
}

variable "db_connection_string" {
  type        = string
  sensitive   = true
  description = "JDBC connection string for the aiarchitect database to store in Key Vault."
}

variable "jwt_secret" {
  type        = string
  sensitive   = true
  description = "JWT signing secret (64 chars) to store in Key Vault."
}

variable "internal_secret" {
  type        = string
  sensitive   = true
  description = "Internal service-to-service authentication secret (32 chars) to store in Key Vault."
}

variable "openai_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "OpenAI API key. If non-empty, stored in Key Vault as 'openai-api-key'."
}

variable "azure_openai_endpoint" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Azure OpenAI endpoint URL. If non-empty, stored in Key Vault as 'azure-openai-endpoint'."
}

variable "azure_openai_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = "Azure OpenAI API key. If non-empty, stored in Key Vault as 'azure-openai-api-key'."
}
