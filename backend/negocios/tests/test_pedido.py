from unittest.mock import patch
from django.test import TestCase
from django.core.exceptions import ValidationError

from negocios.models import (
    Negocio, Cliente, Insumo, Inventario,
    Producto, RecetaProducto, Categoria, Pedido, Pago
)
from negocios.services.pedido_service import (
    crear_pedido, confirmar_venta_pedido, liberar_reserva_pedido
)
from negocios.services.pago_service import confirmar_pago_webpay


def crear_negocio():
    return Negocio.objects.create(
        nombre="Cafetería Test", direccion="Calle 1", comuna="Santiago",
        telefono="123456", tipo_negocio="CAFETERIA", margen=70,
    )


def crear_insumo_con_inventario(negocio, nombre="Café", stock=1000):
    insumo = Insumo.objects.create(
        negocio=negocio, nombre=nombre, unidad_medida="GR", costo_unitario=5,
    )
    Inventario.objects.create(insumo=insumo, stock_actual=stock)
    return insumo


def crear_producto(negocio, insumo, nombre="Cappuccino", precio=2500, cantidad_receta=15):
    categoria = Categoria.objects.get_or_create(negocio=negocio, nombre="Bebidas")[0]
    producto = Producto.objects.create(
        negocio=negocio, categoria=categoria, tipo="P",
        nombre=nombre, precio_venta=precio,
    )
    RecetaProducto.objects.create(producto=producto, insumo=insumo, cantidad=cantidad_receta)
    return producto


class CrearPedidoTest(TestCase):
    """El pedido debe RESERVAR stock, sin descontarlo todavía."""

    def setUp(self):
        self.negocio = crear_negocio()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Ana López")
        self.insumo = crear_insumo_con_inventario(self.negocio, stock=1000)
        self.producto = crear_producto(self.negocio, self.insumo, cantidad_receta=50)

    def test_crear_pedido_reserva_stock_sin_descontarlo(self):
        pedido = crear_pedido(
            negocio=self.negocio, cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )
        self.insumo.inventario.refresh_from_db()
        # 2 unidades x 50gr de receta = 100gr reservados
        self.assertEqual(self.insumo.inventario.stock_reservado, 100)
        self.assertEqual(self.insumo.inventario.stock_actual, 1000)  # NO debe bajar aún
        self.assertEqual(pedido.estado, Pedido.Estado.PENDIENTE_PAGO)
        self.assertEqual(pedido.total, 5000)

    def test_numero_pedido_secuencial(self):
        p1 = crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 1}])
        p2 = crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 1}])
        self.assertEqual(p1.numero, "P-0001")
        self.assertEqual(p2.numero, "P-0002")

    def test_pedido_genera_token_publico_unico(self):
        p1 = crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 1}])
        p2 = crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 1}])
        self.assertIsNotNone(p1.token_publico)
        self.assertNotEqual(p1.token_publico, p2.token_publico)

    def test_pedido_sin_stock_falla_y_no_reserva_nada(self):
        with self.assertRaises(ValidationError):
            crear_pedido(
                negocio=self.negocio, cliente=self.cliente,
                items=[{'producto': self.producto, 'cantidad': 100}]  # excede stock
            )
        self.insumo.inventario.refresh_from_db()
        self.assertEqual(self.insumo.inventario.stock_reservado, 0)

    def test_dos_pedidos_no_pueden_reservar_mas_del_disponible(self):
        # stock=1000, receta=50/u -> caben 20 unidades en total
        crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 15}])
        with self.assertRaises(ValidationError):
            crear_pedido(self.negocio, self.cliente, [{'producto': self.producto, 'cantidad': 10}])


class ConfirmarVentaPedidoTest(TestCase):
    """Al aprobarse el pago: se descuenta stock real y se libera la reserva."""

    def setUp(self):
        self.negocio = crear_negocio()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Ana López")
        self.insumo = crear_insumo_con_inventario(self.negocio, stock=1000)
        self.producto = crear_producto(self.negocio, self.insumo, cantidad_receta=50)
        self.pedido = crear_pedido(
            negocio=self.negocio, cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )

    def test_confirmar_venta_descuenta_stock_y_libera_reserva(self):
        confirmar_venta_pedido(self.pedido)
        self.insumo.inventario.refresh_from_db()
        self.assertEqual(self.insumo.inventario.stock_actual, 900)   # 1000 - 100
        self.assertEqual(self.insumo.inventario.stock_reservado, 0)  # reserva liberada

    def test_confirmar_venta_crea_registro_de_venta(self):
        venta = confirmar_venta_pedido(self.pedido)
        self.assertEqual(venta.total, self.pedido.total)
        self.assertEqual(venta.observaciones, f"Pedido {self.pedido.numero}")


class LiberarReservaPedidoTest(TestCase):
    """Si el pago se rechaza/cancela: se libera la reserva sin tocar stock real."""

    def setUp(self):
        self.negocio = crear_negocio()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Ana López")
        self.insumo = crear_insumo_con_inventario(self.negocio, stock=1000)
        self.producto = crear_producto(self.negocio, self.insumo, cantidad_receta=50)
        self.pedido = crear_pedido(
            negocio=self.negocio, cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )

    def test_liberar_reserva_no_descuenta_stock_real(self):
        liberar_reserva_pedido(self.pedido)
        self.insumo.inventario.refresh_from_db()
        self.assertEqual(self.insumo.inventario.stock_actual, 1000)  # intacto
        self.assertEqual(self.insumo.inventario.stock_reservado, 0)  # liberado

    def test_stock_liberado_queda_disponible_para_otro_pedido(self):
        liberar_reserva_pedido(self.pedido)
        # Ahora otro cliente debería poder pedir la misma cantidad sin error
        otro_cliente = Cliente.objects.create(negocio=self.negocio, nombre="Otro cliente")
        nuevo_pedido = crear_pedido(
            negocio=self.negocio, cliente=otro_cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )
        self.assertEqual(nuevo_pedido.estado, Pedido.Estado.PENDIENTE_PAGO)


class ConfirmarPagoWebpayTest(TestCase):
    """Pruebas de integración del servicio de pago, mockeando Transbank
    (no depende de red ni de tarjetas de prueba reales)."""

    def setUp(self):
        self.negocio = crear_negocio()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Ana López")
        self.insumo = crear_insumo_con_inventario(self.negocio, stock=1000)
        self.producto = crear_producto(self.negocio, self.insumo, cantidad_receta=50)
        self.pedido = crear_pedido(
            negocio=self.negocio, cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )
        self.pago = Pago.objects.create(
            pedido=self.pedido, pasarela=Pago.Pasarela.WEBPAY,
            estado=Pago.Estado.PENDIENTE, monto=self.pedido.total,
            token_pasarela="token-de-prueba-123",
        )

    @patch('negocios.services.pago_service._tx')
    def test_pago_aprobado_actualiza_todo_correctamente(self, mock_tx):
        mock_tx.return_value.commit.return_value = {'status': 'AUTHORIZED'}

        confirmar_pago_webpay("token-de-prueba-123")

        self.pago.refresh_from_db()
        self.pedido.refresh_from_db()
        self.insumo.inventario.refresh_from_db()

        self.assertEqual(self.pago.estado, Pago.Estado.APROBADO)
        self.assertEqual(self.pedido.estado, Pedido.Estado.PAGADO)
        self.assertIsNotNone(self.pedido.venta)
        self.assertEqual(self.insumo.inventario.stock_actual, 900)
        self.assertEqual(self.insumo.inventario.stock_reservado, 0)

    @patch('negocios.services.pago_service._tx')
    def test_pago_rechazado_libera_reserva_y_cancela_pedido(self, mock_tx):
        mock_tx.return_value.commit.return_value = {'status': 'FAILED'}

        confirmar_pago_webpay("token-de-prueba-123")

        self.pago.refresh_from_db()
        self.pedido.refresh_from_db()
        self.insumo.inventario.refresh_from_db()

        self.assertEqual(self.pago.estado, Pago.Estado.RECHAZADO)
        self.assertEqual(self.pedido.estado, Pedido.Estado.CANCELADO)
        self.assertEqual(self.insumo.inventario.stock_actual, 1000)  # intacto
        self.assertEqual(self.insumo.inventario.stock_reservado, 0)  # liberado

    @patch('negocios.services.pago_service._tx')
    def test_confirmar_pago_dos_veces_es_idempotente(self, mock_tx):
        """Simula un reintento del navegador o un callback duplicado de Transbank."""
        mock_tx.return_value.commit.return_value = {'status': 'AUTHORIZED'}

        confirmar_pago_webpay("token-de-prueba-123")
        confirmar_pago_webpay("token-de-prueba-123")  # segunda vez, mismo token

        self.insumo.inventario.refresh_from_db()
        # El stock NO debe descontarse dos veces
        self.assertEqual(self.insumo.inventario.stock_actual, 900)
        # Solo debe existir UNA venta asociada al pedido
        self.pedido.refresh_from_db()
        self.assertEqual(mock_tx.return_value.commit.call_count, 1)  # 2da llamada no debió commitear de nuevo