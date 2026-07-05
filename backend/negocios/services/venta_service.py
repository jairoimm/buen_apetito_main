from django.db import transaction
from django.core.exceptions import ValidationError
from negocios.models import Venta, DetalleVenta, MovimientoInventario, SecuenciaVenta


@transaction.atomic
def crear_venta(negocio, cliente, items, observaciones=''):
    if not items:
        raise ValidationError("La venta no tiene productos.")

    numero = _generar_numero_venta(negocio)

    venta = Venta.objects.create(
        negocio=negocio,
        cliente=cliente,
        numero=numero,
        total=0,
        observaciones=observaciones,
    )

    total = 0

    for item in items:
        producto = item['producto']
        cantidad = item['cantidad']

        if cantidad <= 0:
            raise ValidationError(f"Cantidad inválida para {producto.nombre}.")

        detalle = DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=producto.precio_venta,
        )
        total += detalle.subtotal

        for receta in producto.recetas.select_related('insumo').all():
            inventario = getattr(receta.insumo, 'inventario', None)
            if not inventario:
                raise ValidationError(
                    f"No hay inventario registrado para '{receta.insumo.nombre}'."
                )
            cantidad_necesaria = receta.cantidad * cantidad
            if inventario.stock_disponible < cantidad_necesaria:
                raise ValidationError(
                    f"Stock insuficiente de '{receta.insumo.nombre}'. "
                    f"Disponible: {inventario.stock_disponible}, "
                    f"requerido: {cantidad_necesaria}."
                )
            MovimientoInventario.objects.create(
                insumo=receta.insumo,
                tipo=MovimientoInventario.TipoMovimiento.VENTA,
                cantidad=-(receta.cantidad * cantidad),
                referencia=f"Venta {venta.numero}",
            )

    venta.total = total
    venta.save()
    return venta


def _generar_numero_venta(negocio):
    secuencia, _ = SecuenciaVenta.objects.select_for_update().get_or_create(
        negocio=negocio
    )
    secuencia.ultimo_numero += 1
    secuencia.save()
    return f"V-{secuencia.ultimo_numero:04d}"
