# make sure everything is free under the free tier
resource "azurerm_cosmosdb_account" "lab" {
  name                = "${local.isolated_sea_platform_prefix}-lab"
  location            = local.location
  resource_group_name = azurerm_resource_group.lab.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  free_tier_enabled = true

  consistency_policy {
    consistency_level = "Session"
  }

  is_virtual_network_filter_enabled = true
  virtual_network_rule {
    id = azurerm_subnet.func_snet.id
  }

  geo_location {
    location          = local.location
    failover_priority = 0
  }

  # limit for the cost to prevent over-provisioning issue
  capacity {
    total_throughput_limit = 1000
  }
}
