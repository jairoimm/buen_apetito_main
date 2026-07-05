from django.db.models import Sum, Count, Avg
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated

from negocios.models import (
    Negocio, Insumo, Categoria, Producto, Inventario,
    MovimientoInventario, Cliente, Venta, UsuarioNegocio
)
from negocios.services.venta_service import crear_venta
from .serializers import (
    NegocioSerializer, InsumoSerializer, CategoriaSerializer,
    ProductoSerializer, ProductoWriteSerializer,
    InventarioSerializer, MovimientoInventarioSerializer,
    ClienteSerializer, VentaSerializer, VentaCreateSerializer,
    UsuarioNegocioSerializer, InvitarUsuarioSerializer,
)
from .permissions import EsDueno, TieneAccesoAlNegocio, PuedeVerReportes, PuedeGestionarInventario, PuedeGestionarCatalogo, PuedeCrearVentas


# ── Mixin base ───────────────────────────────────────────────────────────────

class NegocioMixin:
    permission_classes = [TieneAccesoAlNegocio]

    def get_negocio(self):
        return Negocio.objects.get(id=self.kwargs['negocio_id'])


# ── Negocio ──────────────────────────────────────────────────────────────────

class NegocioListCreateView(ListCreateAPIView):
    serializer_class = NegocioSerializer

    def get_queryset(self):
        return Negocio.objects.filter(
            usuarios_negocio__usuario=self.request.user,
            usuarios_negocio__activo=True,
            activo=True
        ).distinct()

    def perform_create(self, serializer):
        negocio = serializer.save(propietario=self.request.user)
        UsuarioNegocio.objects.create(
            usuario=self.request.user, negocio=negocio, rol=UsuarioNegocio.Rol.DUENO
        )

class NegocioDetailView(RetrieveUpdateDestroyAPIView):
    """Ver/editar un negocio individual. Solo para miembros activos de ese negocio."""
    serializer_class = NegocioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Negocio.objects.filter(
            usuarios_negocio__usuario=self.request.user,
            usuarios_negocio__activo=True,
        ).distinct()

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()


# ── Insumos ──────────────────────────────────────────────────────────────────

class InsumoListCreateView(NegocioMixin, ListCreateAPIView):
    permission_classes = [PuedeGestionarInventario]
    serializer_class = InsumoSerializer

    def get_queryset(self):
        return Insumo.objects.filter(negocio_id=self.kwargs['negocio_id'])

    def perform_create(self, serializer):
        serializer.save(negocio=self.get_negocio())


class InsumoDetailView(NegocioMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [PuedeGestionarInventario]
    serializer_class = InsumoSerializer

    def get_queryset(self):
        return Insumo.objects.filter(negocio_id=self.kwargs['negocio_id'])

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()


# ── Categorías ───────────────────────────────────────────────────────────────

class CategoriaListCreateView(NegocioMixin, ListCreateAPIView):
    permission_classes = [PuedeGestionarCatalogo]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        return Categoria.objects.filter(negocio_id=self.kwargs['negocio_id'])

    def perform_create(self, serializer):
        serializer.save(negocio=self.get_negocio())


class CategoriaDetailView(NegocioMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [PuedeGestionarCatalogo]
    serializer_class = CategoriaSerializer

    def get_queryset(self):
        return Categoria.objects.filter(negocio_id=self.kwargs['negocio_id'])

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()


# ── Productos ────────────────────────────────────────────────────────────────

class ProductoListCreateView(NegocioMixin, APIView):
    permission_classes = [PuedeGestionarCatalogo]
    def get(self, request, negocio_id):
        productos = Producto.objects.filter(negocio_id=negocio_id)
        return Response(ProductoSerializer(productos, many=True).data)

    def post(self, request, negocio_id):
        negocio = self.get_negocio()
        serializer = ProductoWriteSerializer(
            data=request.data, context={'negocio': negocio}
        )
        serializer.is_valid(raise_exception=True)
        producto = serializer.save()
        return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)


class ProductoDetailView(NegocioMixin, APIView):
    permission_classes = [PuedeGestionarCatalogo]
    def get_object(self, negocio_id, pk):
        return Producto.objects.get(id=pk, negocio_id=negocio_id)

    def get(self, request, negocio_id, pk):
        producto = self.get_object(negocio_id, pk)
        return Response(ProductoSerializer(producto).data)

    def put(self, request, negocio_id, pk):
        negocio = self.get_negocio()
        producto = self.get_object(negocio_id, pk)
        serializer = ProductoWriteSerializer(
            producto, data=request.data, context={'negocio': negocio}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductoSerializer(producto).data)

    def patch(self, request, negocio_id, pk):
        negocio = self.get_negocio()
        producto = self.get_object(negocio_id, pk)
        serializer = ProductoWriteSerializer(
            producto, data=request.data, partial=True, context={'negocio': negocio}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProductoSerializer(producto).data)

    def delete(self, request, negocio_id, pk):
        producto = self.get_object(negocio_id, pk)
        producto.activo = False
        producto.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Inventario ───────────────────────────────────────────────────────────────

class InventarioListView(NegocioMixin, APIView):
    permission_classes = [PuedeGestionarInventario]
    def get(self, request, negocio_id):
        inventarios = Inventario.objects.filter(
            insumo__negocio_id=negocio_id
        ).select_related('insumo')
        bajo_stock = request.query_params.get('bajo_stock')
        if bajo_stock == 'true':
            inventarios = [i for i in inventarios if i.bajo_stock]
        return Response(InventarioSerializer(inventarios, many=True).data)


class InventarioDetailView(NegocioMixin, APIView):
    permission_classes = [PuedeGestionarInventario]
    def get(self, request, negocio_id, pk):
        inv = Inventario.objects.get(id=pk, insumo__negocio_id=negocio_id)
        return Response(InventarioSerializer(inv).data)

    def patch(self, request, negocio_id, pk):
        inv = Inventario.objects.get(id=pk, insumo__negocio_id=negocio_id)
        serializer = InventarioSerializer(inv, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(InventarioSerializer(inv).data)


class MovimientoListCreateView(NegocioMixin, APIView):
    permission_classes = [PuedeGestionarInventario]
    def get(self, request, negocio_id):
        movs = MovimientoInventario.objects.filter(
            insumo__negocio_id=negocio_id
        ).select_related('insumo')
        return Response(MovimientoInventarioSerializer(movs, many=True).data)

    def post(self, request, negocio_id):
        negocio = self.get_negocio()
        serializer = MovimientoInventarioSerializer(
            data=request.data, context={'negocio': negocio}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ── Clientes ─────────────────────────────────────────────────────────────────

class ClienteListCreateView(NegocioMixin, ListCreateAPIView):
    serializer_class = ClienteSerializer

    def get_queryset(self):
        return Cliente.objects.filter(negocio_id=self.kwargs['negocio_id'], activo=True)

    def perform_create(self, serializer):
        serializer.save(negocio=self.get_negocio())


class ClienteDetailView(NegocioMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = ClienteSerializer

    def get_queryset(self):
        return Cliente.objects.filter(negocio_id=self.kwargs['negocio_id'])

    def perform_destroy(self, instance):
        instance.activo = False
        instance.save()


# ── Ventas ───────────────────────────────────────────────────────────────────

class VentaListCreateView(NegocioMixin, APIView):
    permission_classes = [PuedeCrearVentas]
    def get(self, request, negocio_id):
        ventas = Venta.objects.filter(negocio_id=negocio_id).prefetch_related('detalle')
        return Response(VentaSerializer(ventas, many=True).data)

    def post(self, request, negocio_id):
        negocio = self.get_negocio()
        serializer = VentaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cliente = None
        if 'cliente_id' in data:
            try:
                cliente = Cliente.objects.get(id=data['cliente_id'], negocio=negocio)
            except Cliente.DoesNotExist:
                return Response(
                    {'error': 'Cliente no encontrado.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        items = []
        for item in data['items']:
            try:
                producto = Producto.objects.get(id=item['producto_id'], negocio=negocio)
            except Producto.DoesNotExist:
                return Response(
                    {'error': f"Producto {item['producto_id']} no encontrado."},
                    status=status.HTTP_404_NOT_FOUND
                )
            items.append({'producto': producto, 'cantidad': item['cantidad']})

        try:
            venta = crear_venta(
                negocio=negocio,
                cliente=cliente,
                items=items,
                observaciones=data.get('observaciones', '')
            )
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(VentaSerializer(venta).data, status=status.HTTP_201_CREATED)


class VentaDetailView(NegocioMixin, APIView):
    permission_classes = [PuedeCrearVentas]
    def get(self, request, negocio_id, pk):
        venta = Venta.objects.prefetch_related('detalle').get(
            id=pk, negocio_id=negocio_id
        )
        return Response(VentaSerializer(venta).data)

    def patch(self, request, negocio_id, pk):
        venta = Venta.objects.get(id=pk, negocio_id=negocio_id)
        serializer = VentaSerializer(venta, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(VentaSerializer(venta).data)


# ── Reportes ─────────────────────────────────────────────────────────────────

class ReporteVentasView(NegocioMixin, APIView):
    permission_classes = [PuedeVerReportes]
    def get(self, request, negocio_id):
        ventas = Venta.objects.filter(negocio_id=negocio_id)

        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        if fecha_inicio:
            ventas = ventas.filter(fecha__date__gte=parse_date(fecha_inicio))
        if fecha_fin:
            ventas = ventas.filter(fecha__date__lte=parse_date(fecha_fin))

        resumen = ventas.aggregate(
            total_ventas=Count('id'),
            ingresos_totales=Sum('total'),
            ticket_promedio=Avg('total'),
        )

        productos_top = (
            Producto.objects
            .filter(detalleventa__venta__negocio_id=negocio_id)
            .annotate(
                veces_vendido=Count('detalleventa'),
                ingresos=Sum('detalleventa__subtotal')
            )
            .order_by('-veces_vendido')[:5]
            .values('id', 'nombre', 'veces_vendido', 'ingresos')
        )

        return Response({
            'resumen': resumen,
            'productos_top': list(productos_top),
        })

class UsuariosNegocioView(APIView):
    """Lista los usuarios del negocio e invita nuevos."""
    permission_classes = [EsDueno]

    def get(self, request, negocio_id):
        negocio  = Negocio.objects.get(id=negocio_id)
        usuarios = UsuarioNegocio.objects.filter(
            negocio=negocio
        ).select_related('usuario')
        return Response(UsuarioNegocioSerializer(usuarios, many=True).data)

    def post(self, request, negocio_id):
        negocio = Negocio.objects.get(id=negocio_id)
        serializer = InvitarUsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['username']  # ya es objeto User
        rol  = serializer.validated_data['rol']

        if user == request.user:
            return Response(
                {'error': 'No puedes invitarte a ti mismo.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        miembro, creado = UsuarioNegocio.objects.get_or_create(
            usuario=user,
            negocio=negocio,
            defaults={'rol': rol}
        )
        if not creado:
            miembro.rol    = rol
            miembro.activo = True
            miembro.save()

        return Response(
            UsuarioNegocioSerializer(miembro).data,
            status=status.HTTP_201_CREATED if creado else status.HTTP_200_OK
        )


class UsuarioNegocioDetailView(APIView):
    """Cambia el rol o elimina a un usuario del negocio."""
    permission_classes = [EsDueno]

    def patch(self, request, negocio_id, pk):
        miembro = UsuarioNegocio.objects.get(id=pk, negocio_id=negocio_id)
        serializer = UsuarioNegocioSerializer(
            miembro, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UsuarioNegocioSerializer(miembro).data)

    def delete(self, request, negocio_id, pk):
        miembro = UsuarioNegocio.objects.get(id=pk, negocio_id=negocio_id)
        miembro.activo = False
        miembro.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MiPerfilNegocioView(APIView):
    """Retorna el rol del usuario actual en el negocio."""
    permission_classes = [TieneAccesoAlNegocio]

    def get(self, request, negocio_id):
        negocio = Negocio.objects.get(id=negocio_id)
        # Propietario
        if negocio.propietario == request.user:
            return Response({
                'rol': 'DUENO',
                'rol_display': 'Dueño',
                'permisos': {
                    'ver_reportes': True,
                    'gestionar_inventario': True,
                    'crear_ventas': True,
                    'gestionar_usuarios': True,
                }
            })
        # Miembro
        m = UsuarioNegocio.objects.get(
            usuario=request.user, negocio_id=negocio_id
        )
        return Response({
            'rol': m.rol,
            'rol_display': m.get_rol_display(),
            'permisos': {
                'ver_reportes':          m.puede_ver_reportes,
                'gestionar_inventario':  m.puede_gestionar_inventario,
                'crear_ventas':          m.puede_crear_ventas,
                'gestionar_usuarios':    False,
            }
        })