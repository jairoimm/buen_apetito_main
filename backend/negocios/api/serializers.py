from rest_framework import serializers
from django.contrib.auth.models import User
from negocios.models import (
    Negocio, Insumo, Categoria, Producto, RecetaProducto,
    Inventario, MovimientoInventario, Cliente, Venta, DetalleVenta,
    UsuarioNegocio
)


# ── Negocio ──────────────────────────────────────────────────────────────────

class NegocioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Negocio
        fields = ['id', 'nombre', 'direccion', 'comuna', 'telefono',
                  'tipo_negocio', 'margen', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ── Insumo ───────────────────────────────────────────────────────────────────

class InsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Insumo
        fields = ['id', 'nombre', 'unidad_medida', 'costo_unitario',
                  'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ── Categoría ────────────────────────────────────────────────────────────────

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ── Receta ───────────────────────────────────────────────────────────────────

class RecetaProductoSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    unidad_medida = serializers.CharField(source='insumo.unidad_medida', read_only=True)

    class Meta:
        model = RecetaProducto
        fields = ['id', 'insumo', 'insumo_nombre', 'unidad_medida', 'cantidad']


class RecetaProductoWriteSerializer(serializers.Serializer):
    insumo_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=3)


# ── Producto ─────────────────────────────────────────────────────────────────

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    recetas = RecetaProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'tipo', 'precio_venta', 'activo',
                  'categoria', 'categoria_nombre', 'recetas', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


class ProductoWriteSerializer(serializers.ModelSerializer):
    recetas = RecetaProductoWriteSerializer(many=True, required=False)

    class Meta:
        model = Producto
        fields = ['nombre', 'tipo', 'precio_venta', 'activo', 'categoria', 'recetas']

    def validate_categoria(self, categoria):
        negocio = self.context['negocio']
        if categoria.negocio != negocio:
            raise serializers.ValidationError("La categoría no pertenece a este negocio.")
        return categoria

    def _sync_recetas(self, producto, recetas_data, negocio):
        if recetas_data is None:
            return
        producto.recetas.all().delete()
        for r in recetas_data:
            try:
                insumo = Insumo.objects.get(id=r['insumo_id'], negocio=negocio)
            except Insumo.DoesNotExist:
                raise serializers.ValidationError(
                    f"Insumo {r['insumo_id']} no existe en este negocio."
                )
            RecetaProducto.objects.create(
                producto=producto, insumo=insumo, cantidad=r['cantidad']
            )

    def create(self, validated_data):
        recetas_data = validated_data.pop('recetas', None)
        negocio = self.context['negocio']
        producto = Producto.objects.create(negocio=negocio, **validated_data)
        self._sync_recetas(producto, recetas_data, negocio)
        return producto

    def update(self, instance, validated_data):
        recetas_data = validated_data.pop('recetas', None)
        negocio = self.context['negocio']
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self._sync_recetas(instance, recetas_data, negocio)
        return instance


# ── Inventario ───────────────────────────────────────────────────────────────

class InventarioSerializer(serializers.ModelSerializer):
    insumo_nombre = serializers.CharField(source='insumo.nombre', read_only=True)
    unidad_medida = serializers.CharField(source='insumo.unidad_medida', read_only=True)
    stock_disponible = serializers.DecimalField(max_digits=12, decimal_places=3, read_only=True)
    bajo_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventario
        fields = ['id', 'insumo', 'insumo_nombre', 'unidad_medida',
                  'stock_actual', 'stock_reservado', 'stock_minimo',
                  'stock_disponible', 'bajo_stock', 'fecha_actualizacion']
        read_only_fields = ['id', 'stock_reservado', 'fecha_actualizacion']


class MovimientoInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoInventario
        fields = ['id', 'insumo', 'tipo', 'cantidad', 'referencia', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']

    def validate_insumo(self, insumo):
        negocio = self.context['negocio']
        if insumo.negocio != negocio:
            raise serializers.ValidationError("El insumo no pertenece a este negocio.")
        return insumo


# ── Cliente ──────────────────────────────────────────────────────────────────

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'telefono', 'email', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'fecha_creacion']


# ── Ventas ───────────────────────────────────────────────────────────────────

class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ['id', 'producto', 'producto_nombre', 'cantidad',
                  'precio_unitario', 'subtotal']


class VentaSerializer(serializers.ModelSerializer):
    detalle = DetalleVentaSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)

    class Meta:
        model = Venta
        fields = ['id', 'numero', 'cliente', 'cliente_nombre', 'total',
                  'pagado', 'observaciones', 'fecha', 'detalle']
        read_only_fields = ['id', 'numero', 'total', 'fecha']


class ItemVentaSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=3)


class VentaCreateSerializer(serializers.Serializer):
    cliente_id = serializers.IntegerField(required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)
    items = ItemVentaSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Debe incluir al menos un producto.")
        return items


# ── Reportes ─────────────────────────────────────────────────────────────────

class ReporteVentasSerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField(required=False)
    fecha_fin = serializers.DateField(required=False)

# ── Usuarios del negocio ─────────────────────────────────────────────────────

class UsuarioNegocioSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='usuario.username', read_only=True)
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)

    class Meta:
        model = UsuarioNegocio
        fields = ['id', 'usuario', 'username', 'rol', 'rol_display', 'activo', 'fecha_creacion']
        read_only_fields = ['id', 'usuario', 'fecha_creacion']


class InvitarUsuarioSerializer(serializers.Serializer):
    username = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )
    rol = serializers.ChoiceField(choices=UsuarioNegocio.Rol.choices)
