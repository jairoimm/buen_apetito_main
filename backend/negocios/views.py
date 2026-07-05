from rest_framework.views import APIView
from rest_framework.response import Response

class TestApi(APIView):
    def get(self, request):
        return Response({"mensaje": "¡Conexión exitosa entre Django y React!"})