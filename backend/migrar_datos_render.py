import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

os.environ['DEBUG'] = 'True'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# Ensure sqlite_local is configured so we can read from old db.sqlite3
import settings
if 'sqlite_local' not in settings.DATABASES:
    settings.DATABASES['sqlite_local'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

import django
django.setup()

from django.db import transaction
from django.contrib.auth.models import User
from negocios.models import (
    Negocio, Categoria, Insumo, Inventario, Producto, RecetaProducto,
    Cliente, Venta, DetalleVenta, Pedido, ItemPedido, Pago, SecuenciaVenta, SecuenciaPedido, UsuarioNegocio
)

def limpiar_texto(texto):
    if not texto:
        return texto
    return texto.strip()

def normalizar_unidad(unidad):
    validas = ['KG', 'LT', 'GR', 'ML', 'UN']
    if unidad in validas:
        return unidad
    if unidad in ['MT', 'CM']:
        return 'UN'
    return 'UN'

@transaction.atomic
def migrar():
    print("=== INICIANDO MIGRACIÓN DE DATOS LOCALES A RENDER (POSTGRESQL) ===")
    
    # 1. Obtener o verificar usuario 'jairo' en el destino (default)
    try:
        usuario_jairo = User.objects.using('default').get(username='jairo')
        print(f"[OK] Usuario 'jairo' encontrado (ID: {usuario_jairo.id})")
    except User.DoesNotExist:
        print("[AVISO] Usuario 'jairo' no encontrado en default. Creándolo...")
        usuario_jairo = User.objects.using('default').create_superuser(
            username='jairo',
            email='jjj@gmail.com',
            password='PasswordSeguro123*'
        )

    # 2. Obtener o verificar Negocio 'Food Truck' en el destino (default)
    negocio_local = Negocio.objects.using('sqlite_local').filter(
        nombre__icontains='Food Truck',
        direccion__icontains='San pedro'
    ).first()

    if not negocio_local:
        print("[ERROR] No se encontró el negocio 'Food Truck' en la base de datos local.")
        return

    print(f"[INFO] Negocio local origen: {negocio_local.nombre} ({negocio_local.direccion})")

    negocio_destino, creado = Negocio.objects.using('default').get_or_create(
        nombre=negocio_local.nombre,
        direccion=negocio_local.direccion,
        defaults={
            'comuna': negocio_local.comuna,
            'telefono': negocio_local.telefono,
            'tipo_negocio': negocio_local.tipo_negocio,
            'margen': negocio_local.margen,
            'activo': negocio_local.activo,
            'propietario': usuario_jairo
        }
    )
    if creado:
        print(f"[OK] Negocio 'Food Truck' creado en destino (ID: {negocio_destino.id})")
    else:
        print(f"[OK] Negocio 'Food Truck' ya existe en destino (ID: {negocio_destino.id})")
        negocio_destino.propietario = usuario_jairo
        negocio_destino.save(using='default')

    # Vincular usuario_jairo como dueño en UsuarioNegocio
    UsuarioNegocio.objects.using('default').get_or_create(
        usuario=usuario_jairo,
        negocio=negocio_destino,
        defaults={'rol': UsuarioNegocio.Rol.DUENO, 'activo': True}
    )

    # 3. Migrar Categorías
    print("\n--- Migrando Categorías ---")
    cat_mapping = {} # old_id -> new_categoria_obj
    categorias_locales = Categoria.objects.using('sqlite_local').filter(negocio=negocio_local)
    for cat in categorias_locales:
        nombre_limpio = limpiar_texto(cat.nombre)
        cat_dest, _ = Categoria.objects.using('default').update_or_create(
            negocio=negocio_destino,
            nombre=nombre_limpio,
            defaults={'activo': cat.activo}
        )
        cat_mapping[cat.id] = cat_dest
        print(f"  Categoría sincronizada: {nombre_limpio} (Nuevo ID: {cat_dest.id})")

    # 4. Migrar Insumos
    print("\n--- Migrando Insumos ---")
    insumo_mapping = {} # old_id -> new_insumo_obj
    insumos_locales = Insumo.objects.using('sqlite_local').filter(negocio=negocio_local)
    for ins in insumos_locales:
        nombre_limpio = limpiar_texto(ins.nombre)
        unidad_normalizada = normalizar_unidad(ins.unidad_medida)
        ins_dest, _ = Insumo.objects.using('default').update_or_create(
            negocio=negocio_destino,
            nombre=nombre_limpio,
            defaults={
                'unidad_medida': unidad_normalizada,
                'costo_unitario': ins.costo_unitario,
                'activo': ins.activo,
                'stock': ins.stock
            }
        )
        insumo_mapping[ins.id] = ins_dest
        print(f"  Insumo sincronizado: {nombre_limpio} [{unidad_normalizada}] (Nuevo ID: {ins_dest.id})")

    # 5. Migrar Inventario
    print("\n--- Migrando Inventario ---")
    inventarios_locales = Inventario.objects.using('sqlite_local').filter(insumo__negocio=negocio_local)
    for inv in inventarios_locales:
        nuevo_insumo = insumo_mapping.get(inv.insumo_id)
        if nuevo_insumo:
            Inventario.objects.using('default').update_or_create(
                insumo=nuevo_insumo,
                defaults={
                    'stock_actual': inv.stock_actual,
                    'stock_reservado': inv.stock_reservado,
                    'stock_minimo': inv.stock_minimo
                }
            )
    print(f"  [OK] {inventarios_locales.count()} registros de inventario migrados.")

    # 6. Migrar Productos y Recetas
    print("\n--- Migrando Productos y Recetas ---")
    prod_mapping = {} # old_id -> new_producto_obj
    productos_locales = Producto.objects.using('sqlite_local').filter(negocio=negocio_local)
    for prod in productos_locales:
        nueva_cat = cat_mapping.get(prod.categoria_id)
        if not nueva_cat:
            continue
        nombre_limpio = limpiar_texto(prod.nombre)
        prod_dest, _ = Producto.objects.using('default').update_or_create(
            negocio=negocio_destino,
            nombre=nombre_limpio,
            defaults={
                'categoria': nueva_cat,
                'tipo': prod.tipo,
                'precio_venta': prod.precio_venta,
                'activo': prod.activo,
                'imagen': prod.imagen
            }
        )
        prod_mapping[prod.id] = prod_dest

    # Recetas (RecetaProducto)
    recetas_locales = RecetaProducto.objects.using('sqlite_local').filter(producto__negocio=negocio_local)
    for rec in recetas_locales:
        nuevo_prod = prod_mapping.get(rec.producto_id)
        nuevo_ins = insumo_mapping.get(rec.insumo_id)
        if nuevo_prod and nuevo_ins:
            RecetaProducto.objects.using('default').update_or_create(
                producto=nuevo_prod,
                insumo=nuevo_ins,
                defaults={'cantidad': rec.cantidad}
            )
    print(f"  [OK] {productos_locales.count()} productos y {recetas_locales.count()} relaciones de receta migradas.")

    # 7. Migrar Clientes y Secuencias
    print("\n--- Migrando Clientes y Secuencias ---")
    clientes_locales = Cliente.objects.using('sqlite_local').filter(negocio=negocio_local)
    for cli in clientes_locales:
        Cliente.objects.using('default').update_or_create(
            negocio=negocio_destino,
            nombre=cli.nombre,
            defaults={
                'usuario': usuario_jairo if cli.usuario_id else None,
                'telefono': cli.telefono,
                'email': cli.email,
                'activo': cli.activo
            }
        )

    SecuenciaVenta.objects.using('default').update_or_create(
        negocio=negocio_destino,
        defaults={'ultimo_numero': 1}
    )
    SecuenciaPedido.objects.using('default').update_or_create(
        negocio=negocio_destino,
        defaults={'ultimo_numero': 2}
    )

    print("\n=== ¡MIGRACIÓN COMPLETADA EXITOSAMENTE! ===")

if __name__ == '__main__':
    migrar()
