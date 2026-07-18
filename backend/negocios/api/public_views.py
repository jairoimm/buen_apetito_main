from django.shortcuts import get_object_or_404, redirect
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import serializers, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from negocios.models import Negocio, Categoria, Producto, Cliente, ItemPedido, Pedido
from negocios.services.pedido_service import crear_pedido
from negocios.services.pago_service import iniciar_pago_webpay, confirmar_pago_webpay
from .serializers import CategoriaSerializer


# ── Registro de clientes ──────────────────────────────────────────────────────

class RegistroClienteSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    nombre = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Ese nombre de usuario ya está en uso.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value


class RegistroClienteView(APIView):
    """Endpoint público: cualquiera puede crear una cuenta de cliente."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegistroClienteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            username=data['username'],
            password=data['password'],
            email=data.get('email', ''),
            first_name=data['nombre'],
        )
        return Response(
            {'id': user.id, 'username': user.username, 'nombre': data['nombre']},
            status=status.HTTP_201_CREATED
        )


# ── Menú público ─────────────────────────────────────────────────────────────

class ProductoPublicoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'precio_venta', 'categoria', 'categoria_nombre', 'imagen_url']

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if obj.imagen and request:
            return request.build_absolute_uri(obj.imagen.url)
        return None


class MenuPublicoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, negocio_id):
        negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
        categorias = Categoria.objects.filter(negocio=negocio, activo=True)
        productos = Producto.objects.filter(
            negocio=negocio, activo=True, tipo=Producto.TipoOpciones.PRODUCTO
        ).select_related('categoria')
        return Response({
            'negocio': {'id': negocio.id, 'nombre': negocio.nombre, 'direccion': negocio.direccion},
            'categorias': CategoriaSerializer(categorias, many=True).data,
            'productos': ProductoPublicoSerializer(productos, many=True, context={'request': request}).data,
        })


# ── Crear pedido ─────────────────────────────────────────────────────────────

class ItemPedidoInputSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=3)


class CrearPedidoSerializer(serializers.Serializer):
    items = ItemPedidoInputSerializer(many=True)
    notas = serializers.CharField(required=False, allow_blank=True)
    nombre_cliente = serializers.CharField(required=False, allow_blank=True)
    telefono_cliente = serializers.CharField(required=False, allow_blank=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Debe incluir al menos un producto.")
        return items


class ItemPedidoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)

    class Meta:
        model = ItemPedido
        fields = ['id', 'producto', 'producto_nombre', 'cantidad', 'precio_unitario', 'subtotal']


class PedidoSerializer(serializers.ModelSerializer):
    items = ItemPedidoSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'numero','token_publico', 'estado', 'estado_display', 'total', 'notas', 'items', 'fecha_creacion']


class PedidoPublicoView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, negocio_id):
        negocio = get_object_or_404(Negocio, id=negocio_id, activo=True)
        serializer = CrearPedidoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cliente = self._resolver_cliente(request, negocio, data)

        items = []
        for item in data['items']:
            try:
                producto = Producto.objects.get(id=item['producto_id'], negocio=negocio, activo=True)
            except Producto.DoesNotExist:
                return Response(
                    {'error': f"Producto {item['producto_id']} no existe en este negocio."}, status=400
                )
            items.append({'producto': producto, 'cantidad': item['cantidad']})

        try:
            pedido = crear_pedido(negocio, cliente, items, notas=data.get('notas', ''))
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        return Response(PedidoSerializer(pedido).data, status=201)

    def _resolver_cliente(self, request, negocio, data):
        if request.user and request.user.is_authenticated:
            cliente, _ = Cliente.objects.get_or_create(
                negocio=negocio, usuario=request.user,
                defaults={'nombre': request.user.first_name or request.user.username, 'email': request.user.email},
            )
            return cliente

        nombre = data.get('nombre_cliente')
        telefono = data.get('telefono_cliente')
        if not nombre or not telefono:
            raise serializers.ValidationError(
                "Debes indicar nombre_cliente y telefono_cliente, o iniciar sesión."
            )
        cliente, _ = Cliente.objects.get_or_create(
            negocio=negocio, usuario=None, telefono=telefono,
            defaults={'nombre': nombre},
        )
        return cliente


# ── Consultar estado ─────────────────────────────────────────────────────────

class EstadoPedidoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, negocio_id, token_publico):
        pedido = get_object_or_404(Pedido, negocio_id=negocio_id, token_publico=token_publico)
        return Response(PedidoSerializer(pedido).data)


# ── Pagos: Webpay ────────────────────────────────────────────────────────────

class IniciarPagoWebpayView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, negocio_id, token_publico):
        pedido = get_object_or_404(Pedido, negocio_id=negocio_id, token_publico=token_publico)
        if pedido.estado != pedido.estado.PENDIENTE_PAGO:
            return Response({'error': 'El pedido ya no está pendiente de pago.'}, status=400)
        try:
            data = iniciar_pago_webpay(pedido)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        return Response(data)  # { url, token } — el frontend arma el POST con esto


class RetornoWebpayView(APIView):
    """
    Transbank puede redirigir de vuelta por POST (SDKs antiguos) o por GET
    (SDK 6.x en adelante), así que buscamos el token_ws en cualquiera de los dos.
    """
    permission_classes = [permissions.AllowAny]

    def _obtener_token(self, request):
        return (
            request.data.get('token_ws')
            or request.POST.get('token_ws')
            or request.query_params.get('token_ws')
        )

    def _procesar(self, request):
        token = self._obtener_token(request)
        if not token:
            return Response({'error': 'No se recibió token_ws.'}, status=400)
        pago = confirmar_pago_webpay(token)
        destino = f"{settings.FRONTEND_CLIENTE_URL}/pedido/{pago.pedido.numero}"
        return redirect(destino)

    def post(self, request):
        return self._procesar(request)

    def get(self, request):
        return self._procesar(request)