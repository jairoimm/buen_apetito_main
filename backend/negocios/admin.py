from django.contrib import admin

from .models import (
    Categoria, Negocio, Insumo, Producto, RecetaProducto, Inventario,
    MovimientoInventario, Venta, DetalleVenta, Cliente, UsuarioNegocio,
    Pedido, ItemPedido, Pago, SecuenciaPedido, SecuenciaVenta,
)

admin.site.register(Categoria)
admin.site.register(Negocio)
admin.site.register(Insumo)
admin.site.register(Producto)
admin.site.register(RecetaProducto)
admin.site.register(Inventario)
admin.site.register(MovimientoInventario)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Cliente)
admin.site.register(UsuarioNegocio)
admin.site.register(Pedido)
admin.site.register(ItemPedido)
admin.site.register(Pago)
admin.site.register(SecuenciaPedido)
admin.site.register(SecuenciaVenta)