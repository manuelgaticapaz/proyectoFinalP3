# appointments/urls.py

from django.urls import path, include # Necesitas 'include' aquí también
from rest_framework.routers import DefaultRouter
from .views import AppointmentsViewSet # Asegúrate de que el nombre de tu ViewSet sea este o cámbialo

# Creamos un router y registramos nuestro ViewSet con él.
router = DefaultRouter()
# El primer argumento 'citas' será el prefijo para los endpoints de esta app.
# Por ejemplo: /api/appointments/citas/ y /api/appointments/citas/<pk>/
# 'basename' es opcional si tienes un queryset definido en el ViewSet, pero es buena práctica.
router.register(r'citas', AppointmentsViewSet, basename='appointment')

# Las URLs de la API son ahora determinadas automáticamente por el router.
urlpatterns = [
    path('', include(router.urls)), # Incluimos las URLs generadas por el router
]