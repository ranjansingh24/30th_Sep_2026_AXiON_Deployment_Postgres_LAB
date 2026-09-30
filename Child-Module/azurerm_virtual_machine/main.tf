resource "azurerm_linux_virtual_machine" "vm-chapra" {
  for_each                        = var.c-vm
  name                            = each.value.name
  resource_group_name             = each.value.group
  location                        = each.value.location
  size                            = lookup(each.value, "size", "Standard_B1s")
  admin_username                  = "adminranjan"
  admin_password                  = "P@ssw0rd123456!"
  disable_password_authentication = false
  network_interface_ids           = each.value.network_interface_ids
  zone                            = lookup(each.value, "zone", null)

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = lookup(each.value, "image_sku", "22_04-lts-gen2")
    version   = "latest"
  }

  tags = {
    environment = "staging"
  }
}