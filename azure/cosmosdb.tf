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

  geo_location {
    location          = local.location
    failover_priority = 0
  }
}
