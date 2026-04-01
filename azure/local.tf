locals {
  create                       = true
  location                     = "Southeast Asia"
  isolated_prefix              = "ywper"
  isolated_sea_platform_prefix = "${local.isolated_prefix}-${terraform.workspace}-sea-platform"
}
