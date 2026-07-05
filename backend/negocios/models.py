from django.db import models
from django.contrib.auth.models import User


class Negocio(models.Model):
    class TipoNegocio(models.TextChoices):
        RESTAURANTE = "RESTAURANTE", "Restaurante"
        CAFETERIA = "CAFETERIA", "Cafetería"
        CARRO = "CARRO", "Carro"
        FOOD_TRUCK = "FOOD_TRUCK", "Food Truck"

    propietario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negocios', null=True, blank=True)
    nombre = models.CharField(max_length=200, verbose_name="Nombre del negocio")
    direccion = models.CharField(max_length=255)
    comuna = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    tipo_negocio = models.CharField(max_length=20, choices=TipoNegocio.choices)
    margen = models.DecimalField(max_digits=5, decimal_places=2)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.direccion})"

    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"
        ordering = ['-fecha_creacion']


class Insumo(models.Model):
    class TipoUnidad(models.TextChoices):
        KILOGRAMO = "KG", "Kilogramo"
        LITRO = "LT", "Litro"
        GRAMO = "GR", "Gramo"
        MILILITRO = "ML", "Mililitro"
        UNIDAD = "UN", "Unidad"

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='insumos')
    nombre = models.CharField(max_length=200, verbose_name="Nombre del insumo")
    unidad_medida = models.CharField(max_length=3, choices=TipoUnidad.choices, default=TipoUnidad.UNIDAD)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    stock = models.FloatField(default=0)

    class Meta:
        verbose_name = "Insumo"
        verbose_name_plural = "Insumos"
        ordering = ['-fecha_creacion']
        unique_together = ['negocio', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.unidad_medida})"


class Categoria(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, verbose_name="Negocio")
    nombre = models.CharField(max_length=177, verbose_name="Nombre de la categoría")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['-fecha_creacion']
        unique_together = ['negocio', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.negocio}"


class Producto(models.Model):
    class TipoOpciones(models.TextChoices):
        PRODUCTO = "P", "Producto"
        SERVICIO = "S", "Servicio"

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='productos')
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos', verbose_name="Categoría")
    tipo = models.CharField(max_length=1, choices=TipoOpciones.choices, default=TipoOpciones.PRODUCTO)
    nombre = models.CharField(max_length=255, verbose_name="Nombre del producto")
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    insumos = models.ManyToManyField(Insumo, through='RecetaProducto', related_name='productos')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']
        unique_together = ['negocio', 'nombre']

    def __str__(self):
        return f"{self.nombre} - {self.categoria}"


class RecetaProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='recetas')
    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT, related_name="usado_en")
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Receta producto"
        verbose_name_plural = "Receta productos"
        ordering = ['-fecha_creacion']
        unique_together = ['producto', 'insumo']

    def __str__(self):
        return f"{self.producto} - {self.insumo}"


class Inventario(models.Model):
    insumo = models.OneToOneField(Insumo, on_delete=models.PROTECT, related_name='inventario')
    stock_actual = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    stock_reservado = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    stock_minimo = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    @property
    def stock_disponible(self):
        return self.stock_actual - self.stock_reservado

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo

    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"

    def __str__(self):
        return f"Inventario de {self.insumo.nombre}"


class MovimientoInventario(models.Model):
    class TipoMovimiento(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        VENTA = "VENTA", "Venta"
        MERMA = "MERMA", "Merma"
        AJUSTE = "AJUSTE", "Ajuste Manual"
        RESERVA = "RESERVA", "Reserva Evento"
        LIBERACION = "LIBERACION", "Liberación Reserva"

    insumo = models.ForeignKey(Insumo, on_delete=models.PROTECT, related_name='movimiento_inventarios')
    tipo = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3)
    referencia = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.tipo} - {self.insumo.nombre} - {self.cantidad}"


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='perfiles_cliente')
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='clientes')
    nombre = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['-fecha_creacion']
        unique_together = ['negocio', 'usuario']

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, verbose_name='Negocio')
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    numero = models.CharField(max_length=20, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name='Total de venta')
    fecha = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de venta')
    pagado = models.BooleanField(default=False)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta {self.numero} - {self.negocio}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalle')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Detalle Venta"
        verbose_name_plural = "Detalles Ventas"
        unique_together = ['venta', 'producto']

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad}"


class SecuenciaVenta(models.Model):
    negocio = models.OneToOneField(Negocio, on_delete=models.CASCADE, related_name='secuencia_venta')
    ultimo_numero = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.negocio.nombre} - {self.ultimo_numero}"

class UsuarioNegocio(models.Model):
    """
    Tabla intermedia que conecta usuarios con negocios.
    Un usuario puede pertenecer a varios negocios con distintos roles.
    Un negocio puede tener varios usuarios con distintos roles.
    """
    class Rol(models.TextChoices):
        ADMINISTRADOR        = 'ADMINISTRADOR',        'Administrador'
        DUENO               = 'DUENO',               'Dueño'        
        CAJERO       = 'CAJERO',       'Cajero'
        COCINERO     = 'COCINERO',     'Cocinero'

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='negocios_usuario'
    )
    negocio = models.ForeignKey(
        Negocio, on_delete=models.CASCADE, related_name='usuarios_negocio'
    )
    rol = models.CharField(max_length=20, choices=Rol.choices)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuario', 'negocio']
        verbose_name = 'Usuario del negocio'
        verbose_name_plural = 'Usuarios del negocio'

    def __str__(self):
        return f'{self.usuario.username} — {self.negocio.nombre} ({self.rol})'

    # Helpers de permisos
    @property
    def es_dueno(self):
        return self.rol == self.Rol.DUENO

    @property
    def puede_ver_reportes(self):
        return self.rol in [self.Rol.DUENO, self.Rol.ADMINISTRADOR]

    @property
    def puede_gestionar_inventario(self):
        return self.rol in [self.Rol.DUENO, self.Rol.ADMINISTRADOR]

    @property
    def puede_crear_ventas(self):
        return self.rol in [
            self.Rol.DUENO, self.Rol.ADMINISTRADOR, self.Rol.CAJERO
        ]
    
    @property
    def puede_gestionar_pedidos(self):
        return self.rol in [self.Rol.DUENO, self.Rol.ADMINISTRADOR, self.Rol.COCINERO]
    
    @property
    def gestionar_staff(self):
        return self.rol in [self.Rol.DUENO, self.Rol.ADMINISTRADOR]


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE_PAGO   = 'PENDIENTE_PAGO',   'Pendiente de pago'
        PAGADO           = 'PAGADO',           'Pagado'
        EN_PREPARACION   = 'EN_PREPARACION',   'En preparación'
        LISTO            = 'LISTO',            'Listo para retirar'
        ENTREGADO        = 'ENTREGADO',        'Entregado'
        CANCELADO        = 'CANCELADO',        'Cancelado'

    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE, related_name='pedidos')
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
    numero = models.CharField(max_length=20, unique=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE_PAGO)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    notas = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    venta = models.OneToOneField(Venta, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedido_origen')

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido {self.numero} - {self.get_estado_display()}"


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.DecimalField(max_digits=12, decimal_places=3, default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)


class Pago(models.Model):
    class Pasarela(models.TextChoices):
        WEBPAY = 'WEBPAY', 'Webpay Plus'
        FLOW = 'FLOW', 'Flow'

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        APROBADO  = 'APROBADO',  'Aprobado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'
        ANULADO   = 'ANULADO',   'Anulado'

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='pago')
    pasarela = models.CharField(max_length=10, choices=Pasarela.choices)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    token_pasarela = models.CharField(max_length=255, null=True, blank=True)
    referencia_externa = models.CharField(max_length=255, null=True, blank=True)
    respuesta_cruda = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Pago {self.pasarela} - {self.pedido.numero} ({self.estado})"


class SecuenciaPedido(models.Model):
    negocio = models.OneToOneField(Negocio, on_delete=models.CASCADE, related_name='secuencia_pedido')
    ultimo_numero = models.IntegerField(default=0)