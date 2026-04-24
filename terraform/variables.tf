variable "subscription_id" {
  type        = string
  description = <<-EOT
    Azure subscription ID that hosts all resources.
    How to find: az account show --query id -o tsv
  EOT
}

variable "location" {
  type        = string
  default     = "uksouth"
  description = <<-EOT
    Azure region where all resources are created.
    How to list available regions: az account list-locations -o table
    Default: uksouth (UK South). Change to the region closest to your users.
  EOT
}

variable "environment" {
  type        = string
  default     = "dev"
  description = <<-EOT
    Environment name used as a suffix in all resource names.
    Allowed values: dev, prod.
    Controls resource sizing via .tfvars selection.
  EOT
}

variable "project" {
  type        = string
  default     = "aiarchitect"
  description = <<-EOT
    Short project identifier used in all resource names.
    Requirements: lowercase alphanumeric only, maximum 12 characters.
    Changing this value renames all resources — only set once per environment.
  EOT
}

variable "deployer_object_id" {
  type        = string
  description = <<-EOT
    Azure Object ID of the user or service principal running Terraform.
    Granted Key Vault Administrator role so secrets can be written during apply.
    How to find: az ad signed-in-user show --query id -o tsv
  EOT
}

variable "aks_node_count" {
  type        = number
  default     = 2
  description = "Initial node count for the system node pool. Auto-scaling adjusts this within min/max bounds."
}

variable "aks_node_vm_size" {
  type        = string
  default     = "Standard_D2s_v3"
  description = <<-EOT
    VM size for the AKS system node pool.
    Standard_D2s_v3 = 2 vCPU, 8 GB RAM — sufficient for dev workloads.
    Use Standard_D4s_v3 (4 vCPU, 16 GB) for production.
  EOT
}

variable "aks_min_node_count" {
  type        = number
  default     = 1
  description = "Minimum node count for AKS auto-scaling. Must be >= 1."
}

variable "aks_max_node_count" {
  type        = number
  default     = 5
  description = "Maximum node count for AKS auto-scaling. Limits cost during traffic spikes."
}

variable "db_admin_username" {
  type        = string
  default     = "aiarchitect"
  description = "Administrator login name for the PostgreSQL Flexible Server."
}

variable "db_sku" {
  type        = string
  default     = "B_Standard_B1ms"
  description = <<-EOT
    SKU name for the PostgreSQL Flexible Server.
    B_Standard_B1ms = Burstable tier, 1 vCore, 2 GB RAM — cheapest option, suitable for dev.
    GP_Standard_D2s_v3 = General Purpose, 2 vCores, 8 GB RAM — recommended for production.
  EOT
}

variable "db_storage_mb" {
  type        = number
  default     = 32768
  description = "Allocated storage for PostgreSQL in MB. 32768 = 32 GB. Min 32 GB for Flexible Server."
}

variable "openai_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = <<-EOT
    OpenAI API key. Required when llm_provider = "openai".
    Pass via environment variable to avoid storing in .tfvars:
      export TF_VAR_openai_api_key="sk-your-key-here"
    Terraform reads TF_VAR_-prefixed environment variables automatically.
  EOT
}

variable "azure_openai_endpoint" {
  type        = string
  sensitive   = true
  default     = ""
  description = <<-EOT
    Azure OpenAI service endpoint URL. Required when llm_provider = "azure".
    Format: https://your-resource-name.openai.azure.com/
    Pass via: export TF_VAR_azure_openai_endpoint="https://..."
  EOT
}

variable "azure_openai_api_key" {
  type        = string
  sensitive   = true
  default     = ""
  description = <<-EOT
    Azure OpenAI API key. Required when llm_provider = "azure".
    Pass via: export TF_VAR_azure_openai_api_key="your-key-here"
  EOT
}

variable "llm_provider" {
  type        = string
  default     = "openai"
  description = <<-EOT
    LLM provider to use. Controls which Key Vault secrets are created.
    Allowed values: openai, azure.
    "openai"  — stores openai_api_key in Key Vault.
    "azure"   — stores azure_openai_endpoint and azure_openai_api_key.
  EOT
}

variable "ingress_hostname" {
  description = <<-EOT
    Custom domain for the ingress. If empty, the Azure-assigned FQDN
    (<project>-<environment>.<location>.cloudapp.azure.com) is used automatically.
    If set, create a DNS A record pointing to the ingress_ip output after terraform apply.
  EOT
  type        = string
  default     = ""
}

variable "github_actions_sp_object_id" {
  type        = string
  default     = ""
  description = <<-EOT
    Object ID of the GitHub Actions service principal created by azure-bootstrap.sh.
    When set, grants Key Vault Secrets User role to the SP so CI/CD can read secrets.
    How to find: az ad sp list --display-name sp-<project>-github --query '[0].id' -o tsv
    Leave empty if GitHub Actions does not need direct Key Vault access.
  EOT
}
