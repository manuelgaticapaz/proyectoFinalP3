from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Doctor

class DoctorInline(admin.StackedInline):
    model = Doctor
    can_delete = False
    verbose_name_plural = '👨‍⚕️ Información del Doctor'
    fk_name = 'usuario'
    fieldsets = (
        ('🩺 Información Profesional', {
            'fields': ('nombre', 'apellidos', 'especialidad'),
            'description': 'Datos profesionales del doctor'
        }),
        ('📞 Contacto', {
            'fields': ('telefono',),
            'description': 'Información de contacto'
        }),
        ('🏢 Clínica', {
            'fields': ('clinica', 'activo'),
            'description': 'Clínica y estado del doctor'
        }),
    )

# Define un nuevo UserAdmin mezclando nuestra información de doctor
class UserAdmin(BaseUserAdmin):
    inlines = (DoctorInline,)
    fieldsets = (
        ('🔐 Acceso', {'fields': ('username', 'password')}),
        ('👤 Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('🛡️ Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('📅 Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('get_user_info', 'get_doctor_info', 'get_status_badges', 'get_contact_info', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'doctor__especialidad', 'doctor__activo')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'doctor__nombre', 'doctor__apellidos', 'doctor__especialidad')
    list_per_page = 25
    
    def get_user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #6c757d;">@{}</small>',
            f"{obj.first_name} {obj.last_name}" if obj.first_name else obj.username,
            obj.username
        )
    get_user_info.short_description = '👤 Usuario'
    get_user_info.admin_order_field = 'username'
    
    def get_doctor_info(self, obj):
        try:
            doctor = obj.doctor
            return format_html(
                '<strong>Dr(a). {}</strong><br><small style="color: #007bff;">🩺 {}</small>',
                f"{doctor.nombre} {doctor.apellidos}",
                doctor.especialidad
            )
        except Doctor.DoesNotExist:
            return format_html('<span style="color: #dc3545;">❌ Sin perfil médico</span>')
    get_doctor_info.short_description = '👨‍⚕️ Doctor'
    
    def get_status_badges(self, obj):
        badges = []
        
        # Badge de usuario activo
        if obj.is_active:
            badges.append('<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">✅ Activo</span>')
        else:
            badges.append('<span style="background-color: #dc3545; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">❌ Inactivo</span>')
        
        # Badge de staff
        if obj.is_staff:
            badges.append('<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">👑 Staff</span>')
        
        # Badge de superuser
        if obj.is_superuser:
            badges.append('<span style="background-color: #6f42c1; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">⚡ Admin</span>')
        
        # Badge de doctor activo
        try:
            if obj.doctor.activo:
                badges.append('<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px;">🩺 Médico</span>')
        except Doctor.DoesNotExist:
            pass
        
        return format_html('<br>'.join(badges))
    get_status_badges.short_description = '🏷️ Estado'
    
    def get_contact_info(self, obj):
        contact_info = []
        
        if obj.email:
            contact_info.append(f'📧 {obj.email}')
        
        try:
            if obj.doctor.telefono:
                contact_info.append(f'📞 {obj.doctor.telefono}')
        except Doctor.DoesNotExist:
            pass
        
        if not contact_info:
            return format_html('<span style="color: #6c757d;">❓ Sin contacto</span>')
        
        return format_html('<br>'.join(contact_info))
    get_contact_info.short_description = '📞 Contacto'

# Re-registra UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin independiente para Doctor
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'especialidad', 'get_status_badge', 'telefono', 'clinica', 'get_appointment_count')
    list_filter = ('especialidad', 'activo', 'clinica')
    search_fields = ('nombre', 'apellidos', 'especialidad', 'telefono', 'usuario__username')
    ordering = ('apellidos', 'nombre')
    list_per_page = 25
    
    fieldsets = (
        ('👨‍⚕️ Información Personal', {
            'fields': ('usuario', 'nombre', 'apellidos'),
            'description': 'Datos básicos del doctor'
        }),
        ('🩺 Información Profesional', {
            'fields': ('especialidad', 'activo'),
            'description': 'Especialidad y estado profesional'
        }),
        ('📞 Contacto', {
            'fields': ('telefono',),
            'description': 'Información de contacto'
        }),
        ('🏢 Clínica', {
            'fields': ('clinica',),
            'description': 'Clínica donde trabaja'
        }),
    )
    
    def get_full_name(self, obj):
        return format_html(
            '<strong>Dr(a). {}</strong><br><small style="color: #6c757d;">👤 {}</small>',
            f"{obj.nombre} {obj.apellidos}",
            obj.usuario.username
        )
    get_full_name.short_description = '👨‍⚕️ Doctor'
    get_full_name.admin_order_field = 'apellidos'
    
    def get_status_badge(self, obj):
        if obj.activo:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">✅ Activo</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">❌ Inactivo</span>'
            )
    get_status_badge.short_description = '📊 Estado'
    get_status_badge.admin_order_field = 'activo'
    
    def get_appointment_count(self, obj):
        count = obj.appointment_set.count()
        if count > 0:
            return format_html('<span style="color: #007bff; font-weight: bold;">📅 {}</span>', count)
        return format_html('<span style="color: #6c757d;">➖ 0</span>')
    get_appointment_count.short_description = '📊 Citas'
#     search_fields = ('nombre', 'apellidos', 'especialidad')
#     ordering = ('apellidos', 'nombre')
#     filter_horizontal = []