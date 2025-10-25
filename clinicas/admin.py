from django.contrib import admin
from django.utils.html import format_html
from .models import Clinica

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    list_display = ('get_clinic_name', 'get_location_info', 'get_contact_info', 'get_stats')
    search_fields = ('nombre', 'direccion', 'telefono', 'email')
    ordering = ('nombre',)
    list_per_page = 20
    
    fieldsets = (
        ('🏥 Información de la Clínica', {
            'fields': ('nombre',),
            'description': 'Nombre de la clínica'
        }),
        ('📍 Ubicación', {
            'fields': ('direccion',),
            'description': 'Dirección física de la clínica'
        }),
        ('📞 Contacto', {
            'fields': ('telefono', 'email'),
            'description': 'Información de contacto'
        }),
    )
    
    def get_clinic_name(self, obj):
        return format_html(
            '<strong style="color: #007bff;">🏥 {}</strong>',
            obj.nombre
        )
    get_clinic_name.short_description = '🏥 Clínica'
    get_clinic_name.admin_order_field = 'nombre'
    
    def get_location_info(self, obj):
        if obj.direccion:
            return format_html(
                '<span style="color: #28a745;">📍 {}</span>',
                obj.direccion[:50] + '...' if len(obj.direccion) > 50 else obj.direccion
            )
        return format_html('<span style="color: #6c757d;">❓ Sin dirección</span>')
    get_location_info.short_description = '📍 Ubicación'
    
    def get_contact_info(self, obj):
        contact_info = []
        
        if obj.telefono:
            contact_info.append(f'📞 {obj.telefono}')
        
        if obj.email:
            contact_info.append(f'📧 {obj.email}')
        
        if not contact_info:
            return format_html('<span style="color: #6c757d;">❓ Sin contacto</span>')
        
        return format_html('<br>'.join(contact_info))
    get_contact_info.short_description = '📞 Contacto'
    
    def get_stats(self, obj):
        doctor_count = obj.doctor_set.count()
        patient_count = obj.patient_set.count()
        appointment_count = obj.appointment_set.count()
        
        stats = []
        if doctor_count > 0:
            stats.append(f'👨‍⚕️ {doctor_count} doctores')
        if patient_count > 0:
            stats.append(f'👥 {patient_count} pacientes')
        if appointment_count > 0:
            stats.append(f'📅 {appointment_count} citas')
        
        if not stats:
            return format_html('<span style="color: #6c757d;">📊 Sin datos</span>')
        
        return format_html('<br>'.join(stats))
    get_stats.short_description = '📊 Estadísticas'
