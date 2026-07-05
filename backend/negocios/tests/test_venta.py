from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from negocios.models import (
    Negocio, Cliente, Insumo, Inventario,
    Producto, RecetaProducto, Categoria, Venta
)
from negocios.services.venta_service import crear_venta


def crear_negocio(user=None):
    return Negocio.objects.create(
        propietario=user,
        nombre="Cafetería Test",
        direccion="Calle 1",
        comuna="Santiago",
        telefono="123456",
        tipo_negocio="CAFETERIA",
        margen=70,
    )


def crear_insumo_con_inventario(negocio, nombre="Café", stock=1000):
    insumo = Insumo.objects.create(
        negocio=negocio,
        nombre=nombre,
        unidad_medida="GR",
        costo_unitario=5,
    )
    Inventario.objects.create(insumo=insumo, stock_actual=stock)
    return insumo


def crear_producto(negocio, insumo, nombre="Cappuccino", precio=2500, cantidad_receta=15):
    categoria = Categoria.objects.get_or_create(negocio=negocio, nombre="Bebidas")[0]
    producto = Producto.objects.create(
        negocio=negocio,
        categoria=categoria,
        tipo="P",
        nombre=nombre,
        precio_venta=precio,
    )
    RecetaProducto.objects.create(producto=producto, insumo=insumo, cantidad=cantidad_receta)
    return producto


class VentaServiceTest(TestCase):

    def setUp(self):
        self.negocio = crear_negocio()
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Ana López")
        self.insumo = crear_insumo_con_inventario(self.negocio, stock=1000)
        self.producto = crear_producto(self.negocio, self.insumo, cantidad_receta=50)

    def test_crear_venta_ok(self):
        venta = crear_venta(
            negocio=self.negocio,
            cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 2}]
        )
        self.assertEqual(venta.total, 5000)
        self.assertEqual(venta.detalle.count(), 1)
        self.insumo.inventario.refresh_from_db()
        self.assertEqual(self.insumo.inventario.stock_actual, 900)

    def test_numero_venta_secuencial(self):
        v1 = crear_venta(negocio=self.negocio, cliente=None, items=[{'producto': self.producto, 'cantidad': 1}])
        v2 = crear_venta(negocio=self.negocio, cliente=None, items=[{'producto': self.producto, 'cantidad': 1}])
        self.assertEqual(v1.numero, "V-0001")
        self.assertEqual(v2.numero, "V-0002")

    def test_venta_sin_items_falla(self):
        with self.assertRaises(ValidationError):
            crear_venta(negocio=self.negocio, cliente=None, items=[])

    def test_venta_sin_stock_falla(self):
        with self.assertRaises(ValidationError):
            crear_venta(
                negocio=self.negocio,
                cliente=None,
                items=[{'producto': self.producto, 'cantidad': 100}]
            )

    def test_venta_sin_inventario_falla(self):
        insumo_sin_inv = Insumo.objects.create(
            negocio=self.negocio, nombre="Sin inventario", unidad_medida="UN", costo_unitario=1
        )
        cat = Categoria.objects.get_or_create(negocio=self.negocio, nombre="Bebidas")[0]
        prod = Producto.objects.create(
            negocio=self.negocio, categoria=cat, tipo="P",
            nombre="Producto huérfano", precio_venta=1000
        )
        RecetaProducto.objects.create(producto=prod, insumo=insumo_sin_inv, cantidad=1)
        with self.assertRaises(ValidationError):
            crear_venta(negocio=self.negocio, cliente=None, items=[{'producto': prod, 'cantidad': 1}])

    def test_venta_cantidad_invalida(self):
        with self.assertRaises(ValidationError):
            crear_venta(
                negocio=self.negocio, cliente=None,
                items=[{'producto': self.producto, 'cantidad': 0}]
            )

    def test_venta_con_observaciones(self):
        venta = crear_venta(
            negocio=self.negocio,
            cliente=self.cliente,
            items=[{'producto': self.producto, 'cantidad': 1}],
            observaciones="Sin azúcar"
        )
        self.assertEqual(venta.observaciones, "Sin azúcar")

    def test_venta_multiples_productos(self):
        insumo2 = crear_insumo_con_inventario(self.negocio, nombre="Leche", stock=500)
        prod2 = crear_producto(self.negocio, insumo2, nombre="Latte", precio=3000, cantidad_receta=200)
        venta = crear_venta(
            negocio=self.negocio,
            cliente=self.cliente,
            items=[
                {'producto': self.producto, 'cantidad': 2},
                {'producto': prod2, 'cantidad': 1},
            ]
        )
        self.assertEqual(venta.total, 8000)
        self.assertEqual(venta.detalle.count(), 2)
