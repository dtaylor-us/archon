variable "resource_group_name" {
  type        = string
  description = "Name of the Azure Resource Group where PostgreSQL is created."
}

variable "location" {
  type        = string
  description = "Azure region for the PostgreSQL Flexible Server."
}

variable "project" {
  type        = string
  description = "Short project name used in the server name."
}

variable "environment" {
  type        = string
  description = "Environment name (dev, prod) used in the server name."
}

variable "admin_username" {
  type        = string
  description = "Administrator login name for PostgreSQL."
}

variable "sku_name" {
  type        = string
  description = "SKU for the PostgreSQL Flexible Server. B_Standard_B1ms = cheapest dev tier."
}

variable "storage_mb" {
  type        = number
  description = "Allocated storage in MB. Minimum 32768 (32 GB) for Flexible Server."
}

variable "backup_retention_days" {
  type        = number
  default     = 7
  description = "Number of days to retain automated backups. Range 7–35."
}

variable "geo_redundant_backup" {
  type        = bool
  default     = false
  description = "Enable geo-redundant backups. Doubles storage cost but provides cross-region recovery. Recommended for production."
}

variable "suffix" {
  type        = string
  default     = ""
  description = "Short random suffix appended to the server name to ensure global uniqueness."
}
