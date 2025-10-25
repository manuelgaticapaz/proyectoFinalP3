from django.contrib import admin
from django.utils.html import format_html
from .models import Appointment

# Personalización visual del admin para MediCitas Pro
admin.site.site_title = "MediCitas Pro - Administración"
admin.site.site_header = "🏥 MediCitas Pro - Panel de Administración"
admin.site.index_title = "Sistema de Gestión Médica"
# Registro personalizado para el modelo Appointment
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('get_patient_info', 'get_doctor_info', 'get_appointment_date', 'get_status_badge', 'get_priority_info', 'estado')
    list_filter = ('doctor', 'fecha', 'estado', 'paciente__prioridad', 'clinica')
    search_fields = ('paciente__dni', 'paciente__nombre', 'paciente__apellidos', 'doctor__nombre', 'doctor__apellidos', 'motivo')
    ordering = ('-fecha',)
    list_per_page = 30
    date_hierarchy = 'fecha'

    fieldsets = (
        ('📅 Información de la Cita', {
            'fields': ('paciente', 'doctor', 'fecha', 'estado'),
            'description': 'Datos principales de la cita médica'
        }),
        ('📝 Detalles Médicos', {
            'fields': ('motivo', 'observaciones'),
            'description': 'Motivo de consulta y observaciones del doctor'
        }),
        ('🏢 Ubicación', {
            'fields': ('clinica',),
            'description': 'Clínica donde se realizará la cita'
        }),
    )
    
    def get_patient_info(self, obj):
        priority_colors = {'U': '#dc3545', 'A': '#fd7e14', 'M': '#ffc107', 'B': '#28a745'}
        priority_icons = {'U': '🚨', 'A': '⚠️', 'M': '📋', 'B': '✅'}
        
        color = priority_colors.get(obj.paciente.prioridad, '#6c757d')
        icon = priority_icons.get(obj.paciente.prioridad, '📋')
        
        return format_html(
            '<strong>{}</strong><br><small style="color: #6c757d;">DNI: {}</small><br>'
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">{} {}</span>',
            f"{obj.paciente.nombre} {obj.paciente.apellidos}",
            obj.paciente.dni,
            color, icon, obj.paciente.get_prioridad_display()
        )
    get_patient_info.short_description = '👤 Paciente'
    get_patient_info.admin_order_field = 'paciente__apellidos'
    
    def get_doctor_info(self, obj):
        return format_html(
            '<strong>Dr(a). {}</strong><br><small style="color: #007bff;">📞 {}</small><br>'
            '<small style="color: #28a745;">🩺 {}</small>',
            f"{obj.doctor.nombre} {obj.doctor.apellidos}",
            obj.doctor.telefono or 'Sin teléfono',
            obj.doctor.especialidad
        )
    get_doctor_info.short_description = '👨‍⚕️ Doctor'
    get_doctor_info.admin_order_field = 'doctor__apellidos'
    
    def get_appointment_date(self, obj):
        from django.utils import timezone
        now = timezone.now()
        
        if obj.fecha > now:
            status_color = '#28a745'
            status_icon = '⏰'
            status_text = 'Próxima'
        else:
            status_color = '#6c757d'
            status_icon = '✅'
            status_text = 'Realizada'
            
        return format_html(
            '<strong>{}</strong><br><small style="color: {};">{} {}</small>',
            obj.fecha.strftime('%d/%m/%Y %H:%M'),
            status_color, status_icon, status_text
        )
    get_appointment_date.short_description = '📅 Fecha y Hora'
    get_appointment_date.admin_order_field = 'fecha'
    
    def get_status_badge(self, obj):
        status_colors = {
            'programada': '#007bff',
            'confirmada': '#28a745',
            'en_curso': '#ffc107',
            'completada': '#6c757d',
            'cancelada': '#dc3545',
            'no_asistio': '#fd7e14',
        }
        status_icons = {
            'programada': '📋',
            'confirmada': '✅',
            'en_curso': '🔄',
            'completada': '✔️',
            'cancelada': '❌',
            'no_asistio': '❗',
        }
        
        color = status_colors.get(obj.estado, '#6c757d')
        icon = status_icons.get(obj.estado, '📋')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_estado_display()
        )
    get_status_badge.short_description = '📊 Estado'
    get_status_badge.admin_order_field = 'estado'
    
    def get_priority_info(self, obj):
        return format_html(
            '<div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">'
            '<strong>Motivo:</strong><br><small>{}</small></div>',
            obj.motivo[:50] + '...' if len(obj.motivo) > 50 else obj.motivo
        )
    get_priority_info.short_description = '📝 Motivo'
