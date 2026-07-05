from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import MovimientoInventario, Inventario


@receiver(post_save, sender=MovimientoInventario)
def actualizar_stock(sender, instance, created, **kwargs):

    if not created:
        return

    with transaction.atomic():

        inventario, _ = Inventario.objects.select_for_update().get_or_create(
            insumo=instance.insumo
        )

        inventario.stock_actual += instance.cantidad
        inventario.save()