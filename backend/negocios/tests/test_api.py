from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from negocios.models import Negocio, Insumo, Inventario, Categoria, Producto, RecetaProducto, Cliente


def crear_user(username="barista", password="pass1234"):
    return User.objects.create_user(username=username, password=password)


def crear_negocio(user):
    return Negocio.objects.create(
        propietario=user,
        nombre="Buen Apetito",
        direccion="Av. Siempre Viva 123",
        comuna="Santiago",
        telefono="56912345678",
        tipo_negocio="CAFETERIA",
        margen=60,
    )


class AuthTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = crear_user()

    def test_login_ok(self):
        r = self.client.post('/api/auth/login/', {'username': 'barista', 'password': 'pass1234'})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn('access', r.data)

    def test_login_credenciales_invalidas(self):
        r = self.client.post('/api/auth/login/', {'username': 'barista', 'password': 'wrong'})
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_endpoint_protegido_sin_token(self):
        r = self.client.get('/api/negocios/')
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)


class NegocioAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = crear_user()
        self.client.force_authenticate(user=self.user)

    def test_crear_negocio(self):
        r = self.client.post('/api/negocios/', {
            'nombre': 'Mi Café', 'direccion': 'Calle 1',
            'comuna': 'Providencia', 'telefono': '912345678',
            'tipo_negocio': 'CAFETERIA', 'margen': '55.00'
        })
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['nombre'], 'Mi Café')

    def test_listar_solo_mis_negocios(self):
        crear_negocio(self.user)
        otro_user = crear_user("otro")
        crear_negocio(otro_user)
        r = self.client.get('/api/negocios/')
        self.assertEqual(len(r.data), 1)


class ProductoAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = crear_user()
        self.client.force_authenticate(user=self.user)
        self.negocio = crear_negocio(self.user)
        self.categoria = Categoria.objects.create(negocio=self.negocio, nombre="Bebidas")
        self.insumo = Insumo.objects.create(
            negocio=self.negocio, nombre="Café molido",
            unidad_medida="GR", costo_unitario=8
        )
        Inventario.objects.create(insumo=self.insumo, stock_actual=500)

    def test_crear_producto_con_receta(self):
        r = self.client.post(f'/api/negocios/{self.negocio.id}/productos/', {
            'nombre': 'Espresso',
            'tipo': 'P',
            'precio_venta': '1800',
            'activo': True,
            'categoria': self.categoria.id,
            'recetas': [{'insumo_id': self.insumo.id, 'cantidad': '8.000'}]
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(r.data['recetas']), 1)

    def test_listar_productos(self):
        Producto.objects.create(
            negocio=self.negocio, categoria=self.categoria,
            tipo='P', nombre='Té', precio_venta=1200
        )
        r = self.client.get(f'/api/negocios/{self.negocio.id}/productos/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_negocio_ajeno_rechazado(self):
        otro_user = crear_user("otro2")
        otro_negocio = crear_negocio(otro_user)
        r = self.client.get(f'/api/negocios/{otro_negocio.id}/productos/')
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)


class VentaAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = crear_user()
        self.client.force_authenticate(user=self.user)
        self.negocio = crear_negocio(self.user)
        self.categoria = Categoria.objects.create(negocio=self.negocio, nombre="Cafés")
        self.insumo = Insumo.objects.create(
            negocio=self.negocio, nombre="Granos", unidad_medida="GR", costo_unitario=10
        )
        Inventario.objects.create(insumo=self.insumo, stock_actual=1000)
        self.producto = Producto.objects.create(
            negocio=self.negocio, categoria=self.categoria,
            tipo='P', nombre='Americano', precio_venta=2000
        )
        RecetaProducto.objects.create(producto=self.producto, insumo=self.insumo, cantidad=15)
        self.cliente = Cliente.objects.create(negocio=self.negocio, nombre="Pedro")

    def test_crear_venta_ok(self):
        r = self.client.post(f'/api/negocios/{self.negocio.id}/ventas/', {
            'cliente_id': self.cliente.id,
            'items': [{'producto_id': self.producto.id, 'cantidad': '2'}]
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(r.data['total']), '4000.00')

    def test_crear_venta_sin_stock(self):
        r = self.client.post(f'/api/negocios/{self.negocio.id}/ventas/', {
            'items': [{'producto_id': self.producto.id, 'cantidad': '500'}]
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_ventas(self):
        self.client.post(f'/api/negocios/{self.negocio.id}/ventas/', {
            'items': [{'producto_id': self.producto.id, 'cantidad': '1'}]
        }, format='json')
        r = self.client.get(f'/api/negocios/{self.negocio.id}/ventas/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)


class InventarioAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = crear_user()
        self.client.force_authenticate(user=self.user)
        self.negocio = crear_negocio(self.user)
        self.insumo = Insumo.objects.create(
            negocio=self.negocio, nombre="Azúcar", unidad_medida="KG", costo_unitario=1
        )
        self.inventario = Inventario.objects.create(
            insumo=self.insumo, stock_actual=50, stock_minimo=10
        )

    def test_listar_inventario(self):
        r = self.client.get(f'/api/negocios/{self.negocio.id}/inventario/')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_filtro_bajo_stock(self):
        Inventario.objects.filter(id=self.inventario.id).update(stock_actual=5)
        r = self.client.get(f'/api/negocios/{self.negocio.id}/inventario/?bajo_stock=true')
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r.data), 1)

    def test_registrar_compra(self):
        r = self.client.post(f'/api/negocios/{self.negocio.id}/movimientos/', {
            'insumo': self.insumo.id,
            'tipo': 'COMPRA',
            'cantidad': '30',
            'referencia': 'Proveedor Central'
        }, format='json')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.stock_actual, 80)
