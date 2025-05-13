from django.contrib import admin
from .models import Appointment

# Registro personalizado para el modelo Appointment
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'doctor', 'fecha', 'motivo', 'observaciones', 'creada_en')
    list_filter = ('doctor', 'fecha')  # Permite filtrar por doctor y fecha
    search_fields = ('paciente__dni', 'doctor__nombre', 'doctor__apellidos', 'motivo')  # Buscable por paciente y doctor
    ordering = ('-fecha',)  # Orden por defecto por fecha, más reciente primero

    # Agrupar campos en el formulario de creación/edición
    fieldsets = (
        ('Información de la Cita', {
            'fields': ('paciente', 'doctor', 'fecha', 'motivo', 'observaciones')
        }),
    )
