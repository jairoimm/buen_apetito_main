from rest_framework.permissions import BasePermission
from negocios.models import Negocio, UsuarioNegocio
from django.db.models import Q


def get_membresia(user, negocio_id):
    """Retorna el UsuarioNegocio si existe, sino None."""
    try:
        return UsuarioNegocio.objects.get(
            usuario=user,
            negocio_id=negocio_id,
            activo=True
        )
    except UsuarioNegocio.DoesNotExist:
        return None


class TieneAccesoAlNegocio(BasePermission):
    """Cualquier rol activo puede acceder al negocio."""
    message = 'No tienes acceso a este negocio.'

    def has_permission(self, request, view):
        negocio_id = view.kwargs.get('negocio_id')
        if not negocio_id:
            return False
        # El propietario siempre tiene acceso
        if Negocio.objects.filter(
            id=negocio_id, propietario=request.user
        ).exists():
            return True
        # O cualquier usuario con membresía activa
        return UsuarioNegocio.objects.filter(
            usuario=request.user,
            negocio_id=negocio_id,
            activo=True
        ).exists()


class PuedeVerReportes(TieneAccesoAlNegocio):
    message = 'Solo el dueño o administrador puede ver reportes.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        negocio_id = view.kwargs.get('negocio_id')
        # Propietario siempre puede
        if Negocio.objects.filter(
            id=negocio_id, propietario=request.user
        ).exists():
            return True
        m = get_membresia(request.user, negocio_id)
        return m and m.puede_ver_reportes


class PuedeGestionarInventario(TieneAccesoAlNegocio):
    message = 'Solo el dueño o administrador puede gestionar el inventario.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method == 'GET':
            return True
        negocio_id = view.kwargs.get('negocio_id')
        if Negocio.objects.filter(id=negocio_id, propietario=request.user).exists():
            return True
        m = get_membresia(request.user, negocio_id)
        return m and m.puede_gestionar_inventario
        


class PuedeCrearVentas(TieneAccesoAlNegocio):
    message = 'No tienes permiso para registrar ventas.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method == 'GET':
            return True  # Ver ventas → cualquier rol
        negocio_id = view.kwargs.get('negocio_id')
        if Negocio.objects.filter(
            id=negocio_id, propietario=request.user
        ).exists():
            return True
        m = get_membresia(request.user, negocio_id)
        return m and m.puede_crear_ventas


class EsDueno(TieneAccesoAlNegocio):
    message = 'Solo el dueño puede realizar esta acción.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        negocio_id = view.kwargs.get('negocio_id')
        return Negocio.objects.filter(
            id=negocio_id, propietario=request.user
        ).exists()
    

class PuedeGestionarCatalogo(TieneAccesoAlNegocio):
    message = 'Solo el dueño o administrador puede modificar el menú.'

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method == 'GET':
            return True
        negocio_id = view.kwargs.get('negocio_id')
        if Negocio.objects.filter(id=negocio_id, propietario=request.user).exists():
            return True
        m = get_membresia(request.user, negocio_id)
        return m and m.puede_gestionar_inventario