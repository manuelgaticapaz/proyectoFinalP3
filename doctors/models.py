from django.contrib.auth.models import User
from django.db import models

class Doctor(models.Model):
    """
    Modelo para registrar doctores que están vinculados a un usuario del sistema.
    """

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    apellidos = models.CharField(max_length=150, verbose_name="Apellidos")
    especialidad = models.CharField(max_length=100, verbose_name="Especialidad")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono de contacto")

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctores"
        ordering = ['apellidos', 'nombre']

    def __str__(self):
        return f"Dr(a). {self.nombre} {self.apellidos} ({self.especialidad})"