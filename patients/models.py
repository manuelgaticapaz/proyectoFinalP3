from django.db import models
from django.utils import timezone # Útil para manejar fechas

class Patient(models.Model):
    """
    Modelo para gestionar la información de los pacientes.
    """

    # --- Constantes para Prioridad (Opcional pero recomendado) ---
    PRIORITY_LOW = 'B'
    PRIORITY_MEDIUM = 'M'
    PRIORITY_HIGH = 'A'
    PRIORITY_URGENT = 'U'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Baja'),
        (PRIORITY_MEDIUM, 'Media'),
        (PRIORITY_HIGH, 'Alta'),
        (PRIORITY_URGENT, 'Urgente'),
    ]

    # --- Campos del Modelo ---

    # Información personal básica
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )
    apellidos = models.CharField(
        max_length=150,
        verbose_name="Apellidos"
    )
    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de Nacimiento",
        null=True,  # Puede ser opcional si no siempre se conoce
        blank=True  # Permite dejarlo vacío en formularios
    )
    dni = models.CharField(
        max_length=20,
        unique=True,  # Asegura que no haya dos pacientes con el mismo DNI/ID
        verbose_name="DNI / ID",
        help_text="Documento Personal de Identidad del paciente."
    )

    # Información médica y de contacto
    historial_medico_basico = models.TextField(
        verbose_name="Historial Médico Básico",
        blank=True, # Puede estar vacío
        null=True,  # Permite valor NULL en la base de datos
        help_text="Alergias conocidas, condiciones preexistentes, medicación actual relevante, etc."
    )
    informacion_contacto = models.TextField(
        verbose_name="Información de Contacto",
        blank=True,
        null=True,
        help_text="Teléfono, email, dirección, contacto de emergencia, etc."
    )

    # Prioridad
    prioridad = models.CharField(
        max_length=1,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_LOW, # Establece 'Baja' como prioridad por defecto
        verbose_name="Prioridad",
        help_text="Nivel de prioridad para la atención del paciente."
    )
    
    # Referencia a la clínica (para sistema multi-tenant)
    clinica = models.ForeignKey(
        'clinicas.Clinica', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Clínica"
    )

    # --- Metadatos y Métodos ---

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['apellidos', 'nombre'] # Ordenar por defecto por apellidos, luego nombre

    def __str__(self):
        """
        Representación en cadena del objeto Paciente.
        Útil en el admin de Django y en la consola.
        """
        return f"{self.apellidos}, {self.nombre} (DNI: {self.dni})"

    # --- Métodos adicionales (Opcional) ---

    def calcular_edad(self):
        """
        Calcula la edad del paciente basada en su fecha de nacimiento.
        """
        if not self.fecha_nacimiento:
            return None # No se puede calcular si no hay fecha de nacimiento
        hoy = timezone.now().date()
        edad = hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))
        return edad