variable "resource_group_name" {
  type        = string
  description = "Name of the Azure Resource Group where AKS is created."
}

variable "location" {
  type        = string
  description = "Azure region for the AKS cluster."
}

variable "project" {
  type        = string
  description = "Short project name used in resource names."
}

variable "environment" {
  type        = string
  description = "Environment name (dev, prod) used in resource names."
}

variable "node_count" {
  type        = number
  description = "Initial node count for the system node pool."
}

variable "node_vm_size" {
  type        = string
  description = "VM size for the AKS system node pool."
}

variable "min_node_count" {
  type        = number
  description = "Minimum node count for AKS auto-scaling."
}

variable "max_node_count" {
  type        = number
  description = "Maximum node count for AKS auto-scaling."
}

variable "acr_id" {
  type        = string
  description = "Full resource ID of the Azure Container Registry. Used to assign AcrPull role to the kubelet identity."
}

variable "subscription_id" {
  description = "Azure subscription ID. Required to construct the AKS node resource group scope for the Network Contributor role assignment that allows the cluster to manage the ingress load balancer and public IP."
  type        = string
}
