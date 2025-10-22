from django.db import models
from django.contrib.auth.models import User

class ReporteGenerado(models.Model):
    """
    Modelo para almacenar información sobre reportes generados
    """
    TIPOS_REPORTE = [
        ('citas_diarias', 'Citas Diarias'),
        ('citas_mensuales', 'Citas Mensuales'),
        ('estadisticas_doctor', 'Estadísticas por Doctor'),
        ('estadisticas_paciente', 'Estadísticas por Paciente'),
        ('ocupacion_clinica', 'Ocupación de Clínica'),
        ('ingresos', 'Reporte de Ingresos'),
        ('personalizado', 'Reporte Personalizado'),
    ]
    
    FORMATOS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Reporte")
    tipo = models.CharField(max_length=30, choices=TIPOS_REPORTE, verbose_name="Tipo de Reporte")
    formato = models.CharField(max_length=10, choices=FORMATOS, verbose_name="Formato")
    
    # Filtros aplicados (almacenados como JSON)
    filtros_aplicados = models.JSONField(default=dict, verbose_name="Filtros Aplicados")
    
    # Metadatos
    generado_por = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Generado por")
    clinica = models.ForeignKey('clinicas.Clinica', on_delete=models.CASCADE, null=True, blank=True)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    
    # Archivo generado
    archivo = models.FileField(upload_to='reportes/', null=True, blank=True)
    tamaño_archivo = models.IntegerField(null=True, blank=True, verbose_name="Tamaño en bytes")
    
    class Meta:
        verbose_name = "Reporte Generado"
        verbose_name_plural = "Reportes Generados"
        ordering = ['-fecha_generacion']

    def __str__(self):
        return f"{self.nombre} - {self.formato.upper()} ({self.fecha_generacion.strftime('%d/%m/%Y %H:%M')})"
