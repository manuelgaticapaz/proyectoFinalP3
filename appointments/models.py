from django.db import models
from django.apps import apps  # Usamos apps para obtener el modelo sin importar directamente

class Appointment(models.Model):
    """
    Modelo para gestionar las citas médicas.
    """

    # Referencia del modelo Patient usando una cadena
    paciente = models.ForeignKey(
        'patients.Patient',  # Usa la referencia en cadena para evitar importaciones cíclicas
        on_delete=models.CASCADE, 
        verbose_name="Paciente"
    )
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE)  # Referencia correcta al modelo Doctor

    fecha = models.DateTimeField(verbose_name="Fecha y hora de la cita")
    motivo = models.TextField(verbose_name="Motivo de la consulta")
    observaciones = models.TextField(blank=True, null=True, verbose_name="Observaciones del doctor")
    creada_en = models.DateTimeField(auto_now_add=True)
    
    # Referencia a la clínica (para sistema multi-tenant)
    clinica = models.ForeignKey(
        'clinicas.Clinica', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name="Clínica"
    )
    
    # Estados de la cita
    ESTADOS = [
        ('programada', 'Programada'),
        ('confirmada', 'Confirmada'),
        ('en_curso', 'En Curso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ]
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS, 
        default='programada',
        verbose_name="Estado de la Cita"
    )

    class Meta:
        verbose_name = "Cita Médica"
        verbose_name_plural = "Citas Médicas"
        ordering = ['-fecha']

    def __str__(self):
        return f"Cita de {self.paciente} con {self.doctor} el {self.fecha.strftime('%d/%m/%Y %H:%M')}"
