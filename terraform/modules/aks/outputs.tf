output "cluster_name" {
  description = "Name of the AKS cluster."
  value       = azurerm_kubernetes_cluster.main.name
}

output "kubelet_identity_object_id" {
  description = "Object ID of the AKS kubelet managed identity. Used for Key Vault and ACR role assignments."
  value       = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

output "kubelet_identity_client_id" {
  description = "Client ID of the AKS kubelet managed identity. Used by the Key Vault CSI driver to authenticate."
  value       = azurerm_kubernetes_cluster.main.kubelet_identity[0].client_id
}

output "kube_config" {
  description = "Raw kubeconfig for the AKS cluster. Sensitive — contains credentials."
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}
