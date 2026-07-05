from django.db import transaction
from django.core.exceptions import ValidationError
from negocios.models import Pedido, ItemPedido, SecuenciaPedido


@transaction.atomic
def crear_pedido(negocio, cliente, items, notas=''):
    if not items:
        raise ValidationError("El pedido no tiene productos.")

    numero = _generar_numero_pedido(negocio)
    pedido = Pedido.objects.create(
        negocio=negocio, cliente=cliente, numero=numero, total=0, notas=notas,
    )

    total = 0
    for item in items:
        producto = item['producto']
        cantidad = item['cantidad']
        if cantidad <= 0:
            raise ValidationError(f"Cantidad inválida para {producto.nombre}.")

        for receta in producto.recetas.select_related('insumo__inventario').all():
            inventario = getattr(receta.insumo, 'inventario', None)
            if not inventario:
                raise ValidationError(f"No hay inventario registrado para '{receta.insumo.nombre}'.")
            if inventario.stock_disponible < receta.cantidad * cantidad:
                raise ValidationError(
                    f"Sin stock suficiente de '{receta.insumo.nombre}' para preparar '{producto.nombre}'."
                )

        detalle = ItemPedido.objects.create(
            pedido=pedido, producto=producto, cantidad=cantidad,
            precio_unitario=producto.precio_venta,
        )
        total += detalle.subtotal

    pedido.total = total
    pedido.save()
    return pedido


def _generar_numero_pedido(negocio):
    secuencia, _ = SecuenciaPedido.objects.select_for_update().get_or_create(negocio=negocio)
    secuencia.ultimo_numero += 1
    secuencia.save()
    return f"P-{secuencia.ultimo_numero:04d}"