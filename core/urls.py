"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView  # Importa LogoutView
from appointments.views import crear_cita

from doctors.views import dashboard  # Importa LoginView


from core.views_analytics import analytics_dashboard, appointment_analytics_ajax, export_analytics_report

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),  # Pantalla principal
    path('doctors/dashboard/', dashboard, name='doctor_dashboard'),  # Ruta para el dashboard del doctor
    path('logout/', LogoutView.as_view(), name='logout'),  # Añadir la ruta de cierre de sesión
    
    # Appointments URLs
    path('appointments/', include('appointments.urls')),
    
    # Patients URLs
    path('patients/', include('patients.urls_dashboard')),
    
    # Analytics URLs
    path('analytics/', analytics_dashboard, name='analytics_dashboard'),
    path('analytics/ajax/', appointment_analytics_ajax, name='appointment_analytics_ajax'),
    path('analytics/export/', export_analytics_report, name='export_analytics_report'),
    
    #apis
    path('api/v1/appointments/', include('appointments.urls')),
    path('api/v1/doctors/', include('doctors.urls')),
    path('api/v1/patients/', include('patients.urls')),
]
