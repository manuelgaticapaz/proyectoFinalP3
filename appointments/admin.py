from django.contrib import admin
from .models import Appointment

from django.contrib import admin

# 1. Cambiar el título en la pestaña del navegador
admin.site.site_title = "Citas Admin" 

# 2. Cambiar el título principal (el texto en azul grande)
admin.site.site_header = "Panel de Control Citas"

# 3. Cambiar el texto de bienvenida en la página de inicio del Admin
admin.site.index_title = "Bienvenido al Portal de Administración"
# Registro personalizado para el modelo Appointment
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha', 'motivo', 'observaciones', 'creada_en')
    list_filter = ('doctor', 'fecha', 'paciente')  # Permite filtrar por doctor y fecha
    search_fields = ('paciente__dni', 'doctor__nombre', 'doctor__apellidos', 'motivo')  # Buscable por paciente y doctor
    ordering = ('-fecha',)  # Orden por defecto por fecha, más reciente primero

    # Agrupar campos en el formulario de creación/edición
    fieldsets = (
        ('Información de la Cita', {
            'fields': ('paciente', 'doctor', 'fecha', 'motivo', 'observaciones')
        }),
    )
