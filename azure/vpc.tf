resource "azurerm_resource_group" "lab" {
  name     = "rg-opswork-lab"
  location = local.location
}

resource "azurerm_virtual_network" "vnet" {
  name                = "${local.isolated_sea_platform_prefix}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
}

# 1. subnet for the AZ function only
resource "azurerm_subnet" "func_snet" {
  name                 = "${local.isolated_sea_platform_prefix}-snet"
  resource_group_name  = azurerm_resource_group.lab.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = ["10.0.1.0/24"]

  service_endpoints = ["Microsoft.AzureCosmosDB"]

  # delegate for function to control this subnet
  delegation {
    name = "function-app-delegation"

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}
