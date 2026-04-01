resource "azurerm_resource_group" "lab" {
  name     = "rg-opswork-lab"
  location = "Southeast Asia"
}

resource "azurerm_virtual_network" "vnet" {
  name                = "vnet-opswork-prod"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.lab.location
  resource_group_name = azurerm_resource_group.lab.name
}
