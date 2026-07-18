from django.db import transaction
from django.core.exceptions import ValidationError
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys

from negocios.models import Pago, Pedido
from negocios.services.pedido_service import confirmar_venta_pedido, liberar_reserva_pedido


def _tx():
    return Transaction.build_for_integration(
        IntegrationCommerceCodes.WEBPAY_PLUS,
        IntegrationApiKeys.WEBPAY,
    )


def iniciar_pago_webpay(pedido):
    if pedido.estado != Pedido.Estado.PENDIENTE_PAGO:
        raise ValidationError("Este pedido ya no está pendiente de pago.")

    return_url = 'http://127.0.0.1:8000/api/pagos/webpay/retorno/'

    respuesta = _tx().create(
        buy_order=pedido.numero,
        session_id=str(pedido.id),
        amount=int(pedido.total),
        return_url=return_url,
    )

    pago, _ = Pago.objects.update_or_create(
        pedido=pedido,
        defaults={
            'pasarela': Pago.Pasarela.WEBPAY,
            'estado': Pago.Estado.PENDIENTE,
            'monto': pedido.total,
            'token_pasarela': respuesta['token'],
        }
    )
    return {'url': respuesta['url'], 'token': respuesta['token']}


@transaction.atomic
def confirmar_pago_webpay(token):
    pago = Pago.objects.select_related('pedido').select_for_update().get(token_pasarela=token)

    # Idempotencia: si Transbank o el navegador reintentan el retorno,
    # no se vuelve a procesar un pago ya resuelto.
    if pago.estado in (Pago.Estado.APROBADO, Pago.Estado.RECHAZADO, Pago.Estado.ANULADO):
        return pago

    respuesta = _tx().commit(token)
    pago.respuesta_cruda = respuesta

    if respuesta.get('status') == 'AUTHORIZED':
        pago.estado = Pago.Estado.APROBADO
        pedido = pago.pedido

        venta = confirmar_venta_pedido(pedido)

        pedido.venta = venta
        pedido.estado = Pedido.Estado.PAGADO
        pedido.save()
    else:
        pago.estado = Pago.Estado.RECHAZADO
        pedido = pago.pedido
        liberar_reserva_pedido(pedido)
        pedido.estado = Pedido.Estado.CANCELADO
        pedido.save()

    pago.save()
    return pago