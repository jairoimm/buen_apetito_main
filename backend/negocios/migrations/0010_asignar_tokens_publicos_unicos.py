import uuid
from django.db import migrations


def asignar_tokens_unicos(apps, schema_editor):
    Pedido = apps.get_model('negocios', 'Pedido')
    for pedido in Pedido.objects.all():
        pedido.token_publico = uuid.uuid4()
        pedido.save(update_fields=['token_publico'])


def revertir(apps, schema_editor):
    # No hace falta revertir datos; el campo se elimina solo al revertir 0009.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('negocios', '0009_pedido_token_publico'),
    ]

    operations = [
        migrations.RunPython(asignar_tokens_unicos, revertir),
    ]