# nombre_de_tu_app/admin.py

from django.contrib import admin
from .models import Patient # Importa tu modelo Patient

# --- Opción 1: Registro Básico ---
# La forma más simple de registrar el modelo.
# admin.site.register(Patient)

# --- Opción 2: Registro Personalizado (Recomendado) ---
# Permite configurar cómo se muestra y se interactúa con el modelo en el admin.
@admin.register(Patient) # Usa el decorador @admin.register (alternativa a admin.site.register)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('dni', 'apellidos', 'nombre', 'fecha_nacimiento', 'prioridad', 'calcular_edad') # Campos a mostrar en la lista
    list_filter = ('prioridad',) # Campos por los que se puede filtrar en la barra lateral
    search_fields = ('dni', 'apellidos', 'nombre') # Campos en los que se puede buscar
    ordering = ('apellidos', 'nombre') # Orden por defecto en el admin
    # readonly_fields = ('calcular_edad',) # Si quieres mostrar la edad en el formulario pero no permitir editarla

    # Opcional: Agrupar campos en el formulario de edición/creación
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellidos', 'dni', 'fecha_nacimiento')
        }),
        ('Información Médica y Contacto', {
            'fields': ('historial_medico_basico', 'informacion_contacto'),
            'classes': ('collapse',) # Hace esta sección colapsable
        }),
        ('Clasificación', {
            'fields': ('prioridad',)
        }),
    )

    # Para que 'calcular_edad' funcione en list_display, necesita estar definida
    # como un método en el modelo Patient (como lo hicimos antes) o aquí en PatientAdmin.
    # Si está en el modelo, Django lo encontrará. Si lo defines aquí:
    # def edad_paciente(self, obj):
    #     return obj.calcular_edad()
    # edad_paciente.short_description = 'Edad' # Nombre de la columna
    # Y luego usas 'edad_paciente' en list_display

# Nota: Elige solo UNA de las opciones (la básica o la personalizada).
# La opción personalizada (Opción 2) es mucho más útil.