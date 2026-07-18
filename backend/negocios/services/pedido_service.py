from django.db import transaction
from django.core.exceptions import ValidationError
from negocios.models import Pedido, ItemPedido, SecuenciaPedido, MovimientoInventario, Inventario
from negocios.services.venta_service import crear_venta


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

        for receta in producto.recetas.select_related('insumo').all():
            cantidad_necesaria = receta.cantidad * cantidad

            try:
                inventario = Inventario.objects.select_for_update().get(insumo=receta.insumo)
            except Inventario.DoesNotExist:
                raise ValidationError(f"No hay inventario registrado para '{receta.insumo.nombre}'.")

            if inventario.stock_disponible < cantidad_necesaria:
                raise ValidationError(
                    f"Sin stock suficiente de '{receta.insumo.nombre}' para preparar '{producto.nombre}'."
                )

            MovimientoInventario.objects.create(
                insumo=receta.insumo,
                tipo=MovimientoInventario.TipoMovimiento.RESERVA,
                cantidad=cantidad_necesaria,
                referencia=numero,
            )

        detalle = ItemPedido.objects.create(
            pedido=pedido, producto=producto, cantidad=cantidad,
            precio_unitario=producto.precio_venta,
        )
        total += detalle.subtotal

    pedido.total = total
    pedido.save()
    return pedido


def confirmar_venta_pedido(pedido):
    """Llamar cuando el pago se confirma: crea el registro de Venta (para
    reportes), concreta el descuento real de stock, y libera la reserva
    que quedó pendiente desde crear_pedido()."""
    items = [{'producto': i.producto, 'cantidad': i.cantidad} for i in pedido.items.all()]

    venta = crear_venta(
        negocio=pedido.negocio,
        cliente=pedido.cliente,
        items=items,
        observaciones=f"Pedido {pedido.numero}",
        gestionar_inventario=False,  # el stock ya fue reservado en crear_pedido()
    )

    for item in pedido.items.select_related('producto').all():
        for receta in item.producto.recetas.select_related('insumo').all():
            cantidad_necesaria = receta.cantidad * item.cantidad

            MovimientoInventario.objects.create(
                insumo=receta.insumo,
                tipo=MovimientoInventario.TipoMovimiento.VENTA,
                cantidad=-cantidad_necesaria,
                referencia=f"Pedido {pedido.numero}",
            )
            MovimientoInventario.objects.create(
                insumo=receta.insumo,
                tipo=MovimientoInventario.TipoMovimiento.LIBERACION,
                cantidad=cantidad_necesaria,
                referencia=f"Pedido {pedido.numero}",
            )

    return venta


def liberar_reserva_pedido(pedido):
    """Llamar cuando un pedido se cancela o el pago es rechazado/expira."""
    for item in pedido.items.select_related('producto').all():
        for receta in item.producto.recetas.select_related('insumo').all():
            MovimientoInventario.objects.create(
                insumo=receta.insumo,
                tipo=MovimientoInventario.TipoMovimiento.LIBERACION,
                cantidad=receta.cantidad * item.cantidad,
                referencia=f"Pedido {pedido.numero}",
            )


def _generar_numero_pedido(negocio):
    secuencia, _ = SecuenciaPedido.objects.select_for_update().get_or_create(negocio=negocio)
    secuencia.ultimo_numero += 1
    secuencia.save()
    return f"P-{secuencia.ultimo_numero:04d}"