from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import MovimientoInventario, Inventario


@receiver(post_save, sender=MovimientoInventario)
def actualizar_stock(sender, instance, created, **kwargs):
    if not created:
        return

    Tipo = MovimientoInventario.TipoMovimiento

    with transaction.atomic():
        inventario = Inventario.objects.select_for_update().get(insumo=instance.insumo)

        if instance.tipo == Tipo.RESERVA:
            # cantidad se guarda positiva: aparta stock para un pedido pendiente de pago
            inventario.stock_reservado += instance.cantidad

        elif instance.tipo == Tipo.LIBERACION:
            # cantidad se guarda positiva: libera lo reservado (pedido pagado o cancelado)
            inventario.stock_reservado -= instance.cantidad

        else:
            # COMPRA, VENTA, MERMA, AJUSTE: el signo ya viene correcto desde quien
            # crea el movimiento (igual que ya hace venta_service.py con VENTA en negativo)
            inventario.stock_actual += instance.cantidad

        inventario.save()