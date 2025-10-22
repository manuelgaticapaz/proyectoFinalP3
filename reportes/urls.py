from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Dashboard principal de reportes
    path('', views.dashboard_reportes, name='dashboard'),
    
    # Generación de reportes
    path('generar-pdf/', views.generar_reporte_pdf, name='generar_pdf'),
    path('generar-excel/', views.generar_reporte_excel, name='generar_excel'),
    
    # API para gráficos
    path('grafico/', views.generar_grafico_estadisticas, name='api_grafico'),
]
