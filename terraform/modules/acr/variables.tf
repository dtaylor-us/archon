variable "resource_group_name" {
  type        = string
  description = "Name of the Azure Resource Group where ACR is created."
}

variable "location" {
  type        = string
  description = "Azure region for the Container Registry."
}

variable "project" {
  type        = string
  description = "Short project name used in the registry name."
}

variable "environment" {
  type        = string
  description = "Environment name (dev, prod) used in the registry name."
}

variable "sku" {
  type        = string
  default     = "Basic"
  description = "ACR SKU tier. Basic is sufficient for dev. Standard or Premium for production geo-replication."
}

variable "suffix" {
  type        = string
  default     = ""
  description = "Short random suffix appended to the registry name to ensure global uniqueness."
}
