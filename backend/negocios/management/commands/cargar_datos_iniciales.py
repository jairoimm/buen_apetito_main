"""
Comando para cargar los datos iniciales de Buen Apetito.
Uso: python manage.py cargar_datos_iniciales

Carga:
  - Insumos con stock inicial e inventario
  - Categorías del menú
  - Productos con recetas (qué insumos usa cada uno)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from negocios.models import (
    Negocio, Insumo, Inventario, Categoria,
    Producto, RecetaProducto, SecuenciaVenta
)


class Command(BaseCommand):
    help = 'Carga los datos iniciales de la cafetería Buen Apetito'

    def handle(self, *args, **kwargs):
        self.stdout.write('\nCargando datos iniciales de Buen Apetito...\n')
        try:
            with transaction.atomic():
                negocio = self._get_negocio()
                insumos = self._crear_insumos(negocio)
                categorias = self._crear_categorias(negocio)
                self._crear_productos(negocio, categorias, insumos)
                SecuenciaVenta.objects.get_or_create(negocio=negocio)
            self.stdout.write(self.style.SUCCESS('\n✅  Datos cargados exitosamente!\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌  Error: {e}\n'))
            raise

    def _get_negocio(self):
        negocio = Negocio.objects.first()
        if not negocio:
            raise Exception(
                'No existe ningún negocio. '
                'Créalo primero desde http://localhost:8000/admin'
            )
        self.stdout.write(f'  → Negocio: {negocio.nombre}')
        return negocio

    def _crear_insumos(self, negocio):
        """
        Insumos organizados por proveedor/tipo.
        stock_inicial = cantidad que tienes hoy en bodega.
        stock_minimo  = cuando llega a este nivel, el sistema te avisa.
        """
        datos = [
            # ── Panadería / Masas ──────────────────────────────────────
            dict(nombre='sopaipilla',           unidad='UN', costo=80,  stock=5,  minimo=3),
            dict(nombre='empanadas coctel',           unidad='UN', costo=300,  stock=5,   minimo=2),
            dict(nombre='masa de empanadas',              unidad='UN', costo=100,  stock=2,   minimo=1),
            dict(nombre='masa pizza individual',   unidad='UN', costo=400, stock=5,   minimo=2),
            dict(nombre='Masa pizza mediana',      unidad='UN', costo=500, stock=2,   minimo=1),
            dict(nombre='masa pizza xl',         unidad='UN', costo=850, stock=1,   minimo=0.5),
            dict(nombre='pan completo',           unidad='UN', costo=250,  stock=60,  minimo=20),
            dict(nombre='pan completo xl',     unidad='UN', costo=450,  stock=10,  minimo=3),
            dict(nombre='pan churrasco',     unidad='UN', costo=250,  stock=10,  minimo=3),
            dict(nombre='calzones rotos',     unidad='UN', costo=350,  stock=10,  minimo=3),

            # ── Churros ───────────────────────────────────────────────
            dict(nombre='churro tradicional',  unidad='UN', costo=575, stock=0.5, minimo=0.2),
            dict(nombre='Churro relleno', unidad='UN', costo=300, stock=2, minimo=0.5),
            dict(nombre='churro jumbo',           unidad='UN', costo=282, stock=2,   minimo=0.5),
            dict(nombre='Azúcar flor',      unidad='KG', costo=1600,  stock=1,   minimo=0.5),
            dict(nombre='manjar nestle 1',       unidad='KG', costo=5000,  stock=1,   minimo=0.5),
            dict(nombre='leche condensada',      unidad='LT', costo=2000,  stock=1,   minimo=0.5),
            dict(nombre='cobertura de chocolate',      unidad='KG', costo=7000,  stock=1,   minimo=0.5),
            dict(nombre='leche entera',      unidad='LT', costo=2000,  stock=1,   minimo=0.5),

            # ── insumos empaque──────────────────────────────────────────────────
            dict(nombre='Cajas de carton',      unidad='CM', costo=650, stock=3,  minimo=1),
            dict(nombre='bolsas plástico pequeñas',    unidad='CM', costo=600, stock=2,  minimo=1),
            dict(nombre='bolsas plástico grandes', unidad='CM', costo=950,   stock=5,  minimo=2),
            dict(nombre='bolsas papel pequeñas',    unidad='CM', costo=250,  stock=2,  minimo=1),
            dict(nombre='bolsas papel grandes',   unidad='CM', costo=500,  stock=2,  minimo=1),
            dict(nombre='Pack servilletas',   unidad='KG', costo=1500,  stock=1,  minimo=0.3),
            dict(nombre='papel mantequilla',      unidad='CM', costo=1450,  stock=1,   minimo=0.5),
            dict(nombre='Vasos desechables',unidad='UN', costo=1200,   stock=200, minimo=50),
            dict(nombre='Vasos te/Cafe',unidad='UN', costo=1500,   stock=200, minimo=50),
            dict(nombre='Bolsas kraft',     unidad='UN', costo=500,   stock=200, minimo=50),
            dict(nombre='alusa plast',     unidad='MT', costo=3000,   stock=10, minimo=50),
    

            # ── Empanadas ─────────────────────────────────────────────
            dict(nombre='Carne posta rosada',     unidad='KG', costo=11690, stock=3,   minimo=1),
            dict(nombre='Cebolla',          unidad='KG', costo=600,  stock=3,   minimo=1),
            dict(nombre='Aceitunas',        unidad='KG', costo=4000, stock=0.5, minimo=0.2),
            dict(nombre='Pimentón',         unidad='KG', costo=1450, stock=1,   minimo=0.5),
            dict(nombre='Queso mantecoso',  unidad='KG', costo=9800, stock=2,   minimo=0.5),
            dict(nombre='choclo molido',  unidad='KG', costo=6000, stock=2,   minimo=0.5),
            dict(nombre='pechuga deshuesada',  unidad='KG', costo=31640, stock=2,   minimo=0.5),
            dict(nombre='huevos 30',  unidad='UN', costo=8990, stock=2,   minimo=0.5),
            dict(nombre='oregano',         unidad='GR', costo=1500, stock=2,   minimo=0.3),

            # ── Sándwiches / Desayunos ────────────────────────────────
            dict(nombre='Jamón',            unidad='GR', costo=5000, stock=2,   minimo=0.5),
            dict(nombre='Tomate',           unidad='KG', costo=1500,  stock=2,   minimo=1),
            dict(nombre='Palta',            unidad='KG', costo=5200, stock=2,   minimo=1),
            dict(nombre='mostoza',          unidad='GR', costo=3500,  stock=1,   minimo=0.5),
            dict(nombre='mayonesa',         unidad='GR', costo=10290, stock=1,   minimo=0.3),
            dict(nombre='ketchup',         unidad='GR', costo=3000, stock=1,   minimo=0.3),
            dict(nombre='aji',             unidad='KG', costo=2960, stock=1,   minimo=0.3),
            dict(nombre='cilantro',         unidad='KG', costo=1500, stock=1,   minimo=0.3),
            dict(nombre='ajo',         unidad='KG', costo=2500, stock=1,   minimo=0.3),
            dict(nombre='sal',         unidad='KG', costo=800, stock=1,   minimo=0.3),
            dict(nombre='aceite 5',         unidad='LT', costo=8990, stock=1,   minimo=0.3),
            dict(nombre='limones',         unidad='KG', costo=2300, stock=1,   minimo=0.3),
            dict(nombre='mantequilla',         unidad='GR', costo=5500, stock=1,   minimo=0.3),
            dict(nombre='queso laminado',         unidad='GR', costo=6000, stock=1,   minimo=0.3),


            # ── Bebidas frías ─────────────────────────────────────────
            dict(nombre='kem piña lata',          unidad='LT', costo=615,  stock=5,   minimo=2),
            dict(nombre='Limón soda lata',            unidad='LT', costo=615,  stock=2,   minimo=1),
            dict(nombre='cocacola lata',         unidad='LT', costo=750, stock=2,   minimo=1),
            dict(nombre='sprite lata',          unidad='LT', costo=715,  stock=2,   minimo=1),
            dict(nombre='Agua mineral pequeña',     unidad='LT', costo=790,  stock=24,  minimo=6),
            dict(nombre='Agua mineral grande',     unidad='LT', costo=1060,  stock=12,  minimo=4),
            dict(nombre='pepsi lata',     unidad='LT', costo=615,  stock=24,  minimo=6),
            dict(nombre='fanta lata',     unidad='LT', costo=540,  stock=24,  minimo=6),
            dict(nombre='Nectar Jumex piña',     unidad='LT', costo=800,  stock=24,  minimo=6),
            dict(nombre='Nectar Jumex mango',     unidad='LT', costo=800,  stock=24,  minimo=6),

            # ── Bebidas calientes ─────────────────────────────────────
            dict(nombre='Café',             unidad='GR', costo=5000, stock=10,  minimo=2),
            dict(nombre='Té',               unidad='UN', costo=6000,  stock=10,  minimo=2),
            dict(nombre='milo',   unidad='UN', costo=9790, stock=10,  minimo=2),
            ]

        insumos = {}
        creados = 0
        for d in datos:
            insumo, nuevo = Insumo.objects.get_or_create(
                negocio=negocio,
                nombre=d['nombre'],
                defaults={
                    'unidad_medida': d['unidad'],
                    'costo_unitario': d['costo'],
                }
            )
            Inventario.objects.get_or_create(
                insumo=insumo,
                defaults={
                    'stock_actual': d['stock'],
                    'stock_minimo': d['minimo'],
                }
            )
            insumos[d['nombre']] = insumo
            if nuevo:
                creados += 1

        self.stdout.write(f'  → {creados} insumos creados ({len(insumos)} total)')
        return insumos

    def _crear_categorias(self, negocio):
        nombres = [
            'Churros',
            'Bebidas calientes',
            'Bebidas frías',
            'Empanadas',
            'Sándwiches',
            'Sopaipillas',
            'Desayunos',
            'Pasteles',
        ]
        cats = {}
        for nombre in nombres:
            cat, _ = Categoria.objects.get_or_create(negocio=negocio, nombre=nombre)
            cats[nombre] = cat
        self.stdout.write(f'  → {len(cats)} categorías creadas')
        return cats

    def _crear_productos(self, negocio, cats, ins):
        """
        Cada producto tiene:
          - precio_venta en CLP
          - receta: lista de (nombre_insumo, cantidad)
        Las cantidades están en la misma unidad del insumo (KG, LT, UN, GR→KG).
        """
        productos = [

            # ── CHURROS ──────────────────────────────────────────────
            dict(
                nombre='Churro Tradicional (6 uds)',
                cat='Churros', precio=4500,
                receta=[
                    ('Aceite vegetal', 0.050), 
                    ('Azúcar flor', 0.015),
                    ('Canela en polvo', 0.003), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='Churro Tradicional (12 uds)',
                cat='Churros', precio=8500,
                receta=[
                    ('Aceite vegetal', 0.100), 
                    ('Azúcar flor', 0.030),
                    ('Canela en polvo', 0.006), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='Churro Tradicional (20 uds)',
                cat='Churros', precio=14500,
                receta=[
                    ('Aceite vegetal', 0.150), 
                    ('Azúcar flor', 0.045),
                    ('Canela en polvo', 0.009), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='Churro Relleno (6 uds)',
                cat='Churros', precio=6500,
                receta=[
                    ('Aceite vegetal', 0.050), 
                    ('Azúcar flor', 0.015),
                    ('Canela en polvo', 0.003), 
                    ('Manjar', 0.040), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='Churro relleno (12 uds)',
                cat='Churros', precio=12500,
                receta=[
                    ('Aceite vegetal', 0.100), 
                    ('Azúcar flor', 0.030),
                    ('Canela en polvo', 0.006), 
                    ('Manjar', 0.080), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='Churro Relleno (20 uds)',
                cat='Churros', precio=21000,
                receta=[
                    ('Aceite vegetal', 0.150), 
                    ('Azúcar flor', 0.045),
                    ('Canela en polvo', 0.009), 
                    ('Manjar', 0.150), 
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),

            dict(
                nombre='churro Jumbo (1 uds)',
                cat='Churros', precio=1700,
                receta=[
                    ('Aceite vegetal', 0.010),
                    ('Azúcar flor', 0.005), 
                    ('Canela en polvo', 0.003),
                    ('servileta', 0.005),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0),
                ]
            ),
            dict(
                nombre='churro Jumbo (3 uds)',
                cat='Churros', precio=4800,
                receta=[
                    ('Aceite vegetal', 0.020),
                    ('Azúcar flor', 0.005), 
                    ('Canela en polvo', 0.004),
                    ('leche condensada ->', 0),
                    ('chocolate cobertura ->', 0), 
                    ('servileta', 0.005),
                ]
            ),
            dict(
                nombre='leche condensada (1 uds)',
                cat='Churros', precio=500,
                receta=[]
            ),
            dict(
                nombre='cobertura chocolate (1 uds)',
                cat='Churros', precio=500,
                receta=[]
            ),

            # ── SOPAIPILLAS ───────────────────────────────────────────
            dict(
                nombre='Sopaipillas (1 uds)',
                cat='Sopaipillas', precio=350,
                receta=[
                    ('Aceite vegetal', 0.040),
                    ('Bolsas kraft', 1), 
                    ('servileta', 0.005),
                ]
            ),
            dict(
                nombre='Sopaipillas (3 uds)',
                cat='Sopaipillas', precio=1000,
                receta=[
                    ('Aceite vegetal', 0.040),
                    ('Bolsas kraft', 1), 
                    ('servileta', 0.005),
                ]
            ),

            # ── EMPANADAS ─────────────────────────────────────────────
            dict(
                nombre='Empanada de cóctel (1 uds)',
                cat='Empanadas', precio=500,
                receta=[
                    ('Aceite vegetal', 0.040),
                    ('Bolsas kraft', 1), 
                    ('servileta', 0.005),
                ]
            ),
            dict(
                nombre='Empanada de coctel (3 uds)',
                cat='Empanadas', precio=1000,
                receta=[
                    ('Aceite vegetal', 0.040),
                    ('Bolsas kraft', 1), 
                    ('servileta', 0.005),
                ]
            ),
            dict(
                nombre='empanadas de carne (1 uds)',
                cat='Empanadas', precio=2000,
                receta=[
                    ('posta rosada', 0.840),
                    ('Servilleta', 0.005), 
                    ('aceite vegetal', 0.120),
                    ('Cebolla', 0.480),
                    ('Aceitunas', 0.120), 
                    ('huevo', 0.060),
                    ('Bolsas kraft', 2),
                ]
            ),
            dict(
                nombre='empanadas de choclo/queso (1 uds)',
                cat='Empanadas', precio=2000,
                receta=[
                    ('choclo', 0.840),
                    ('Servilleta', 0.005),
                    ('queso', 0.480),
                    ('aceite vegetal', 0.120),
                    ('Bolsas kraft', 2),
                ]
            ),

            dict(
                nombre='empanadas de queso (1 uds)',
                cat='Empanadas', precio=2000,
                receta=[
                    ('queso', 0.840),
                    ('Servilleta', 0.005),
                    ('aceite vegetal', 0.480),
                    ('Bolsas kraft', 2),
                ]
            ),

            dict(
                nombre='empanadas de queso/carne (1 uds)',
                cat='Empanadas', precio=2000,
                receta=[
                    ('queso', 0.450),
                    ('posta rosada', 0.840),
                    ('Servilleta', 0.005),
                    ('aceite vegetal', 0.480),
                    ('Bolsas kraft', 2),
                ]
            ),

            dict(
                nombre='empanadas de napolitana (1 uds)',
                cat='Empanadas', precio=2000,
                receta=[
                    ('jamon', 0.450),
                    ('tomate', 0.450),
                    ('oregano', 0.020),
                    ('queso', 0.450),
                    ('Servilleta', 0.005),
                    ('aceite vegetal', 0.480),
                    ('Bolsas kraft', 2),
                ]
            ),

            # ── BEBIDAS CALIENTES ─────────────────────────────────────
            dict(
                nombre='Café normal',
                cat='Bebidas calientes', precio=1500,
                receta=[
                    ('Café molido', 0.010),
                    ('Vasos desechables', 1),
                    ('azucar', 0.015),
                ]
            ),
            dict(
                nombre='Cappuccino',
                cat='Bebidas calientes', precio=2000,
                receta=[
                    ('Café molido', 0.008), 
                    ('Leche entera', 0.150),
                    ('Vasos desechables', 1), 
                    ('azucar', 0.015),
                ]
            ),
            dict(
                nombre='Latte',
                cat='Bebidas calientes', precio=2000,
                receta=[
                    ('Café molido', 0.008), 
                    ('Leche entera', 0.200),
                    ('Vasos desechables', 1), 
                    ('azucar', 0.015),
                ]
            ),
            dict(
                nombre='Chocolate caliente',
                cat='Bebidas calientes', precio=1500,
                receta=[
                    ('Cacao en polvo', 0.025), 
                    ('Leche entera', 0.200),
                    ('Azúcar', 0.015), 
                    ('Vasos desechables', 1),
                ]
            ),
            dict(
                nombre='Té',
                cat='Bebidas calientes', precio=1500,
                receta=[
                    ('Té bolsas', 1),
                    ('Azúcar', 0.010), 
                    ('Vasos desechables', 1),
                ]
            ),

            # ── BEBIDAS FRÍAS ─────────────────────────────────────────
            dict(
                nombre='nectar de piña jumex',
                cat='Bebidas frías', precio=1500,
                receta=[]
                
            ),
            dict(
                nombre='kem piña lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='cocacola lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='limon soda lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='sprite lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='fanta lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='pepsi lata',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='nectar mango jumex',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),
            dict(
                nombre='agua mineral pequeña',
                cat='Bebidas frías', precio=1200,
                receta=[]
            ),
            dict(
                nombre='agua mineral grande',
                cat='Bebidas frías', precio=1500,
                receta=[]
            ),

            # ── SÁNDWICHES ────────────────────────────────────────────
            dict(
                nombre='Sándwich de jamón y queso',
                cat='Sándwiches', precio=1500,
                receta=[
                    ('Pan marraqueta', 1),
                    ('Jamón', 0.060),
                    ('Queso mantecoso', 0.040),
                    ('Bolsas kraft', 1),
                    ('alusa', 0.005),
                ]
            ),
            dict(
                nombre='Sándwich de pollo mayo',
                cat='Sándwiches', precio=1500,
                receta=[
                    ('Pan marraqueta', 1), 
                    ('Pollo', 0.100),
                    ('Mayonesa', 0.060), 
                    ('Bolsas kraft', 1),
                    ('alusa', 0.005),
                ]
            ),
            dict(
                nombre='Sándwich integral jamon y queso',
                cat='Sándwiches', precio=1500,
                receta=[
                    ('Pan integral', 2),
                    ('Jamón', 0.050),
                    ('Queso mantecoso', 0.040), 
                    ('alusa', 0.060),
                    ('servilletas', 0.005), 
                    ('Bolsas kraft', 1),
                ]
            ),
            dict(
                nombre='Sándwich integral mayonesa pollo',
                cat='Sándwiches', precio=1500,
                receta=[
                    ('Pan integral', 2),
                    ('pollo', 0.050),
                    ('mayonesa', 0.030), 
                    ('alusa', 0.060),
                    ('servilletas', 0.005), 
                    ('Bolsas kraft', 1),
                ]
            ),

            # ── DESAYUNOS ─────────────────────────────────────────────
            dict(
                nombre='Pack Desayuno clásico',
                cat='Desayunos', precio=5000,
                receta=[
                    ('Sándwiches->', 2),
                    ('bebidas calientes->', 10), 
                    ('Huevos duros', 2), 
                    ('bebidas frias->', 10),
                    ('Servilletas', 2),
                ]
            ),
            dict(
                nombre='Pack Desayuno XL',
                cat='Desayunos', precio=7500,
                receta=[
                    ('Sándwiches->', 4),
                    ('bebidas calientes->', 10), 
                    ('Huevos duros', 4), 
                    ('bebidas frias->', 10),
                    ('Servilletas', 2),
                ]
            ),
        ]

        creados = 0
        for d in productos:
            # Filtra recetas con insumo vacío
            receta_valida = [(n, c) for n, c in d['receta'] if n in ins and c > 0]

            producto, nuevo = Producto.objects.get_or_create(
                negocio=negocio,
                nombre=d['nombre'],
                defaults={
                    'categoria': cats[d['cat']],
                    'tipo': 'P',
                    'precio_venta': d['precio'],
                }
            )
            if nuevo:
                for nombre_ins, cantidad in receta_valida:
                    RecetaProducto.objects.get_or_create(
                        producto=producto,
                        insumo=ins[nombre_ins],
                        defaults={'cantidad': cantidad}
                    )
                creados += 1

        self.stdout.write(f'  → {creados} productos creados con recetas')
