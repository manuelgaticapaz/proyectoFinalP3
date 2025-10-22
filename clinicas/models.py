from django.db import models
from django.contrib.auth.models import User

class Clinica(models.Model):
    """
    Modelo para gestionar múltiples clínicas en el sistema multi-tenant
    """
    nombre = models.CharField(max_length=200, verbose_name="Nombre de la Clínica")
    codigo = models.CharField(max_length=10, unique=True, verbose_name="Código de Clínica")
    direccion = models.TextField(verbose_name="Dirección")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email de Contacto")
    
    # Configuraciones específicas de la clínica
    horario_inicio = models.TimeField(default='08:00', verbose_name="Horario de Inicio")
    horario_fin = models.TimeField(default='18:00', verbose_name="Horario de Fin")
    dias_laborales = models.CharField(
        max_length=20, 
        default='1,2,3,4,5',  # Lunes a Viernes
        verbose_name="Días Laborales (1=Lun, 7=Dom)"
    )
    
    # Configuración de citas
    duracion_cita_default = models.IntegerField(default=30, verbose_name="Duración Default de Cita (min)")
    max_citas_por_dia = models.IntegerField(default=50, verbose_name="Máximo Citas por Día")
    
    # Metadatos
    activa = models.BooleanField(default=True, verbose_name="Clínica Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Administrador de la clínica
    administrador = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Administrador Principal"
    )

    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

class UsuarioClinica(models.Model):
    """
    Modelo para gestionar qué usuarios tienen acceso a qué clínicas
    """
    ROLES = [
        ('admin', 'Administrador'),
        ('doctor', 'Doctor'),
        ('recepcionista', 'Recepcionista'),
        ('enfermera', 'Enfermera'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    rol = models.CharField(max_length=20, choices=ROLES, verbose_name="Rol en la Clínica")
    activo = models.BooleanField(default=True, verbose_name="Acceso Activo")
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Usuario de Clínica"
        verbose_name_plural = "Usuarios de Clínicas"
        unique_together = ['usuario', 'clinica']

    def __str__(self):
        return f"{self.usuario.username} - {self.clinica.nombre} ({self.rol})"
