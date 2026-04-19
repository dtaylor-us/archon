resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.project}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"

  # 30 days retains enough for operational debugging without excessive cost.
  retention_in_days = 30

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-${var.project}-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  dns_prefix          = "${var.project}-${var.environment}"

  # SystemAssigned identity — Azure manages credentials automatically.
  # No service principal rotation required.
  identity {
    type = "SystemAssigned"
  }

  default_node_pool {
    name = "system"

    vm_size             = var.node_vm_size
    enable_auto_scaling = true
    min_count           = var.min_node_count
    max_count           = var.max_node_count
    node_count          = var.node_count

    # Ephemeral OS disks use the VM's local cache/temp storage.
    # Faster boot, lower cost, and no OS disk charges.
    os_disk_type = "Ephemeral"
  }

  # Azure CNI provides pod-level network policies and direct VNet integration.
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
  }

  # Built-in Key Vault secrets provider — mounts secrets as volumes.
  # Enabled here so the CSI driver is available when the post-terraform
  # script installs the provider chart.
  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }

  # Automatic channel upgrade keeps the cluster on stable patch releases
  # without requiring manual intervention.
  automatic_channel_upgrade = "stable"

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Dedicated node pool for Python agent pods.
# Larger VM size accommodates LangGraph state and LLM response buffering.
# The taint prevents non-agent pods from scheduling here and wasting capacity.
resource "azurerm_kubernetes_cluster_node_pool" "agent" {
  name                  = "agentpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = "Standard_D4s_v3"
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = 6

  # Only pods that tolerate this taint will be scheduled on this pool.
  # The Helm chart sets the matching toleration on agent deployments.
  node_taints = ["workload=agent:NoSchedule"]

  node_labels = {
    workload = "agent"
  }

  tags = {
    project     = var.project
    environment = var.environment
    managed_by  = "terraform"
  }
}

# Allow AKS kubelet to pull images from ACR without storing credentials.
# Role is scoped to the specific ACR resource to follow least-privilege.
resource "azurerm_role_assignment" "aks_acr_pull" {
  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# Required for Container Insights to publish metrics to Azure Monitor.
resource "azurerm_role_assignment" "monitoring" {
  scope                = azurerm_kubernetes_cluster.main.id
  role_definition_name = "Monitoring Metrics Publisher"
  principal_id         = azurerm_kubernetes_cluster.main.identity[0].principal_id
}
