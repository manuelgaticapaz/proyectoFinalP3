from django.contrib import admin
from django.utils.html import format_html
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'dni', 'get_age', 'get_priority_badge', 'clinica', 'get_appointment_count')
    list_filter = ('prioridad', 'clinica', 'fecha_nacimiento')
    search_fields = ('dni', 'apellidos', 'nombre', 'informacion_contacto')
    ordering = ('apellidos', 'nombre')
    list_per_page = 25
    
    fieldsets = (
        ('👤 Información Personal', {
            'fields': ('nombre', 'apellidos', 'dni', 'fecha_nacimiento'),
            'description': 'Datos básicos de identificación del paciente'
        }),
        ('🏥 Información Médica', {
            'fields': ('historial_medico_basico', 'prioridad'),
            'description': 'Historial médico y nivel de prioridad'
        }),
        ('📞 Contacto', {
            'fields': ('informacion_contacto',),
            'classes': ('collapse',),
            'description': 'Información de contacto del paciente'
        }),
        ('🏢 Clínica', {
            'fields': ('clinica',),
            'description': 'Clínica a la que pertenece el paciente'
        }),
    )
    
    def get_full_name(self, obj):
        return f"{obj.apellidos}, {obj.nombre}"
    get_full_name.short_description = '👤 Paciente'
    get_full_name.admin_order_field = 'apellidos'
    
    def get_age(self, obj):
        age = obj.calcular_edad()
        if age is not None:
            if age < 18:
                return format_html('<span style="color: #28a745;">👶 {} años</span>', age)
            elif age > 65:
                return format_html('<span style="color: #dc3545;">👴 {} años</span>', age)
            else:
                return format_html('<span>🧑 {} años</span>', age)
        return format_html('<span style="color: #6c757d;">❓ N/A</span>')
    get_age.short_description = '📅 Edad'
    
    def get_priority_badge(self, obj):
        colors = {
            'U': '#dc3545',  # Rojo para urgente
            'A': '#fd7e14',  # Naranja para alta
            'M': '#ffc107',  # Amarillo para media
            'B': '#28a745',  # Verde para baja
        }
        icons = {
            'U': '🚨',
            'A': '⚠️',
            'M': '📋',
            'B': '✅',
        }
        color = colors.get(obj.prioridad, '#6c757d')
        icon = icons.get(obj.prioridad, '📋')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_prioridad_display()
        )
    get_priority_badge.short_description = '🎯 Prioridad'
    get_priority_badge.admin_order_field = 'prioridad'
    
    def get_appointment_count(self, obj):
        count = obj.appointment_set.count()
        if count > 0:
            return format_html('<span style="color: #007bff; font-weight: bold;">📅 {}</span>', count)
        return format_html('<span style="color: #6c757d;">➖ 0</span>')
    get_appointment_count.short_description = '📊 Citas'