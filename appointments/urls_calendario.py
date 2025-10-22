from django.urls import path
from . import views_calendario

app_name = 'calendario'

urlpatterns = [
    # Vista principal del calendario
    path('', views_calendario.vista_calendario, name='calendario'),
    
    # APIs para el calendario
    path('api/citas-dia/', views_calendario.obtener_citas_dia, name='api_citas_dia'),
    path('api/reagendar/', views_calendario.reagendar_cita, name='api_reagendar'),
    path('api/horarios-disponibles/', views_calendario.horarios_disponibles, name='api_horarios_disponibles'),
]
