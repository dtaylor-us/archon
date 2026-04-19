terraform {
  required_version = ">= 1.7.0"

  # Backend values are populated at init time by scripts/azure-bootstrap.sh.
  # Run: terraform init \
  #   -backend-config="resource_group_name=rg-<project>-tfstate" \
  #   -backend-config="storage_account_name=st<project>tfstate" \
  #   -backend-config="container_name=tfstate" \
  #   -backend-config="key=aiarchitect.tfstate"
  #
  # Or source .deployment-config and use the init command printed by
  # scripts/azure-bootstrap.sh.
  backend "azurerm" {
    resource_group_name  = ""
    storage_account_name = ""
    container_name       = ""
    key                  = ""
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.110"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.53"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      # Do not destroy the Key Vault permanently during terraform destroy.
      # The vault enters soft-delete for 7 days, allowing recovery if needed.
      purge_soft_delete_on_destroy = false

      # Automatically recover a soft-deleted Key Vault that shares the same
      # name if re-deploying to the same environment.
      recover_soft_deleted_key_vaults = true
    }
  }
}
