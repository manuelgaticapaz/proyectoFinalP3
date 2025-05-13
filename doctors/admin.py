from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Doctor

class DoctorInline(admin.StackedInline):
    model = Doctor
    can_delete = False
    verbose_name_plural = 'Información del Doctor'
    fk_name = 'usuario' # Especifica el campo de clave foránea en el modelo Doctor

# Define un nuevo UserAdmin mezclando nuestra información de doctor
class UserAdmin(BaseUserAdmin):
    inlines = (DoctorInline,)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Re-registra UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# No necesitas registrar DoctorAdmin por separado si usas UserAdmin con inline
# @admin.register(Doctor)
# class DoctorAdmin(admin.ModelAdmin):
#     list_display = ('nombre', 'apellidos', 'especialidad', 'telefono')
#     list_filter = ('especialidad',)
#     search_fields = ('nombre', 'apellidos', 'especialidad')
#     ordering = ('apellidos', 'nombre')
#     filter_horizontal = []