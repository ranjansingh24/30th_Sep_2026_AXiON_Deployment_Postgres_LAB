output "pg_server_ids" {
  value = {
    for k, v in azurerm_postgresql_flexible_server.pg-chapra : k => v.id
  }
}

output "pg_fqdn" {
  value = {
    for k, v in azurerm_postgresql_flexible_server.pg-chapra : k => v.fqdn
  }
}
