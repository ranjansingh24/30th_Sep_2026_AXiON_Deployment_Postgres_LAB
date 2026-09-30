resource "azurerm_postgresql_flexible_server" "pg-chapra" {
  for_each               = var.c-pg
  name                   = each.value.name
  resource_group_name    = each.value.group
  location               = each.value.location
  version                = lookup(each.value, "version", "14")
  administrator_login    = lookup(each.value, "admin_user", "psqladmin")
  administrator_password = lookup(each.value, "admin_password", "P@ssw0rd123456!")
  sku_name               = lookup(each.value, "sku_name", "B_Standard_B1ms")
  storage_mb             = lookup(each.value, "storage_mb", 32768)
  zone                   = lookup(each.value, "zone", "1")
  public_network_access_enabled = lookup(each.value, "public_network_access_enabled", true)

  tags = {
    environment = "staging"
    application = "AXiON"
  }
}

resource "azurerm_postgresql_flexible_server_database" "pg-db" {
  for_each  = { for k, v in var.c-pg : k => v if lookup(v, "db_name", null) != null }
  name      = each.value.db_name
  server_id = azurerm_postgresql_flexible_server.pg-chapra[each.key].id
  collation = lookup(each.value, "collation", "en_US.utf8")
  charset   = lookup(each.value, "charset", "UTF8")
}

resource "azurerm_postgresql_flexible_server_firewall_rule" "pg-fw" {
  for_each         = { for k, v in var.c-pg : k => v if lookup(v, "allow_all_ips", true) }
  name             = lookup(each.value, "fw_rule_name", "AllowAllAzureAndPublic")
  server_id        = azurerm_postgresql_flexible_server.pg-chapra[each.key].id
  start_ip_address = lookup(each.value, "start_ip", "0.0.0.0")
  end_ip_address   = lookup(each.value, "end_ip", "255.255.255.255")
}
