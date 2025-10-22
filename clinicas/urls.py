from django.urls import path
from . import views

app_name = 'clinicas'

urlpatterns = [
    # Dashboard de administración de clínicas
    path('', views.dashboard_clinicas, name='dashboard'),
    
    # Gestión de clínicas
    path('crear/', views.crear_clinica, name='crear'),
    path('<int:clinica_id>/editar/', views.editar_clinica, name='editar'),
    path('<int:clinica_id>/detalle/', views.detalle_clinica, name='detalle'),
    
    # Gestión de usuarios por clínica
    path('<int:clinica_id>/usuarios/', views.usuarios_clinica, name='usuarios'),
    path('<int:clinica_id>/usuarios/agregar/', views.agregar_usuario_clinica, name='agregar_usuario'),
    path('usuario/<int:usuario_clinica_id>/editar/', views.editar_usuario_clinica, name='editar_usuario'),
    
    # Transferencias entre clínicas
    path('transferir-paciente/', views.transferir_paciente, name='transferir_paciente'),
    
    # Reportes consolidados
    path('reportes-consolidados/', views.reportes_consolidados, name='reportes_consolidados'),
]
