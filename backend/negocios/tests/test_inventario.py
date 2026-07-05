from django.test import TestCase
from negocios.models import Negocio, Insumo, Inventario, MovimientoInventario


def crear_negocio():
    return Negocio.objects.create(
        nombre="Test", direccion="Test", comuna="Test",
        telefono="123", tipo_negocio="CARRO", margen=70
    )


class InventarioModelTest(TestCase):

    def setUp(self):
        self.negocio = crear_negocio()
        self.insumo = Insumo.objects.create(
            negocio=self.negocio, nombre="Azúcar", unidad_medida="KG", costo_unitario=1
        )

    def test_stock_disponible(self):
        inv = Inventario.objects.create(
            insumo=self.insumo, stock_actual=100, stock_reservado=20
        )
        self.assertEqual(inv.stock_disponible, 80)

    def test_bajo_stock_verdadero(self):
        inv = Inventario.objects.create(
            insumo=self.insumo, stock_actual=5, stock_minimo=10
        )
        self.assertTrue(inv.bajo_stock)

    def test_bajo_stock_falso(self):
        inv = Inventario.objects.create(
            insumo=self.insumo, stock_actual=50, stock_minimo=10
        )
        self.assertFalse(inv.bajo_stock)

    def test_stock_disponible_sin_reserva(self):
        inv = Inventario.objects.create(insumo=self.insumo, stock_actual=200)
        self.assertEqual(inv.stock_disponible, 200)


class MovimientoInventarioSignalTest(TestCase):

    def setUp(self):
        self.negocio = crear_negocio()
        self.insumo = Insumo.objects.create(
            negocio=self.negocio, nombre="Harina", unidad_medida="KG", costo_unitario=2
        )
        self.inventario = Inventario.objects.create(
            insumo=self.insumo, stock_actual=0
        )

    def test_compra_aumenta_stock(self):
        MovimientoInventario.objects.create(
            insumo=self.insumo, tipo="COMPRA", cantidad=50
        )
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 50)

    def test_merma_reduce_stock(self):
        self.inventario.stock_actual = 100
        self.inventario.save()
        MovimientoInventario.objects.create(
            insumo=self.insumo, tipo="MERMA", cantidad=-10
        )
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 90)

    def test_multiples_movimientos_acumulan(self):
        MovimientoInventario.objects.create(insumo=self.insumo, tipo="COMPRA", cantidad=100)
        MovimientoInventario.objects.create(insumo=self.insumo, tipo="COMPRA", cantidad=50)
        MovimientoInventario.objects.create(insumo=self.insumo, tipo="MERMA", cantidad=-20)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 130)
