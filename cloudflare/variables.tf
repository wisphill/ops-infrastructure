variable "cloudflare_account_id" {
  description = "Cloudflare account ID that will own the Pages project."
  type        = string
  default     = "13ef71f58915b43c6b681df0bf9f9dc9"
}

# zone_id of the foolosophy.dev
variable "cloudflare_foolosophy_zone_id" {
  description = "Cloudflare zone ID for foolosophy.dev, used to manage the portal DNS record."
  type        = string
  default     = "9806b23872717769ec4751edf0877de4"
}
