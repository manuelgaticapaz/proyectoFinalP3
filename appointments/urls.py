# appointments/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AppointmentsViewSet, 
    crear_cita, 
    editar_cita, 
    eliminar_cita, 
    check_appointment_availability
)

# API Router
router = DefaultRouter()
router.register(r'citas', AppointmentsViewSet, basename='appointment')

# Web URLs
urlpatterns = [
    # Web views
    path('crear/', crear_cita, name='crear_cita'),
    path('editar/<int:cita_id>/', editar_cita, name='editar_cita'),
    path('eliminar/<int:cita_id>/', eliminar_cita, name='eliminar_cita'),
    path('check-availability/', check_appointment_availability, name='check_appointment_availability'),
    
    # API endpoints
    path('api/', include(router.urls)),
]