from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    NegocioListCreateView, NegocioDetailView,
    InsumoListCreateView, InsumoDetailView,
    CategoriaListCreateView, CategoriaDetailView,
    ProductoListCreateView, ProductoDetailView,
    InventarioListView, InventarioDetailView, MovimientoListCreateView,
    ClienteListCreateView, ClienteDetailView,
    VentaListCreateView, VentaDetailView,
    ReporteVentasView, UsuariosNegocioView, UsuarioNegocioDetailView,
    MiPerfilNegocioView
)
from .public_views import MenuPublicoView, PedidoPublicoView, EstadoPedidoView, RegistroClienteView, IniciarPagoWebpayView, RetornoWebpayView

urlpatterns = [
    # Auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Negocios
    path('negocios/', NegocioListCreateView.as_view(), name='negocio-list'),
    path('negocios/<int:pk>/', NegocioDetailView.as_view(), name='negocio-detail'),

    # Insumos
    path('negocios/<int:negocio_id>/insumos/', InsumoListCreateView.as_view(), name='insumo-list'),
    path('negocios/<int:negocio_id>/insumos/<int:pk>/', InsumoDetailView.as_view(), name='insumo-detail'),

    # Categorías
    path('negocios/<int:negocio_id>/categorias/', CategoriaListCreateView.as_view(), name='categoria-list'),
    path('negocios/<int:negocio_id>/categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categoria-detail'),

    # Productos
    path('negocios/<int:negocio_id>/productos/', ProductoListCreateView.as_view(), name='producto-list'),
    path('negocios/<int:negocio_id>/productos/<int:pk>/', ProductoDetailView.as_view(), name='producto-detail'),

    # Inventario
    path('negocios/<int:negocio_id>/inventario/', InventarioListView.as_view(), name='inventario-list'),
    path('negocios/<int:negocio_id>/inventario/<int:pk>/', InventarioDetailView.as_view(), name='inventario-detail'),
    path('negocios/<int:negocio_id>/movimientos/', MovimientoListCreateView.as_view(), name='movimiento-list'),

    # Clientes
    path('negocios/<int:negocio_id>/clientes/', ClienteListCreateView.as_view(), name='cliente-list'),
    path('negocios/<int:negocio_id>/clientes/<int:pk>/', ClienteDetailView.as_view(), name='cliente-detail'),

    # Ventas
    path('negocios/<int:negocio_id>/ventas/', VentaListCreateView.as_view(), name='venta-list'),
    path('negocios/<int:negocio_id>/ventas/<int:pk>/', VentaDetailView.as_view(), name='venta-detail'),

    # Reportes
    path('negocios/<int:negocio_id>/reportes/ventas/', ReporteVentasView.as_view(), name='reporte-ventas'),

    # Staff / roles
    path('negocios/<int:negocio_id>/usuarios/',
         UsuariosNegocioView.as_view(), name='usuarios-negocio'),

    path('negocios/<int:negocio_id>/usuarios/<int:pk>/',
         UsuarioNegocioDetailView.as_view(), name='usuario-negocio-detail'),

    path('negocios/<int:negocio_id>/mi-perfil/',
         MiPerfilNegocioView.as_view(), name='mi-perfil-negocio'),

    # Público — app de pedidos para clientes
    path('negocios/<int:negocio_id>/menu/', MenuPublicoView.as_view(), name='menu-publico'),
    path('negocios/<int:negocio_id>/pedidos/', PedidoPublicoView.as_view(), name='pedido-crear'),
    path('negocios/<int:negocio_id>/pedidos/<uuid:token_publico>/', EstadoPedidoView.as_view(), name='pedido-estado'),
    path('clientes/registro/', RegistroClienteView.as_view(), name='cliente-registro'),

    # Pagos
    path('negocios/<int:negocio_id>/pedidos/<uuid:token_publico>/pago/', IniciarPagoWebpayView.as_view(), name='pedido-pago'),
    path('pagos/webpay/retorno/', RetornoWebpayView.as_view(), name='webpay-retorno'),
]