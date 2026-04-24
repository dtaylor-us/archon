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

output "ingress_public_ip_address" {
  value       = azurerm_public_ip.ingress.ip_address
  description = "Static public IP address for the nginx ingress controller. Point a DNS A record here if using a custom domain."
}

output "ingress_public_ip_id" {
  value       = azurerm_public_ip.ingress.id
  description = "Resource ID of the static public IP. Passed to the nginx ingress Helm installation so Azure associates the load balancer with this Terraform-managed IP rather than creating a new dynamic one."
}

output "ingress_fqdn" {
  value       = "${var.project}-${var.environment}.${var.location}.cloudapp.azure.com"
  description = "Azure-assigned stable FQDN for the ingress. Use this as the Let's Encrypt domain when no custom domain is configured."
}
