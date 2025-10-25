from django.contrib import admin
from django.contrib.admin import AdminSite
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from clinicas.models import Clinica

class MediCitasAdminSite(AdminSite):
    """
    Admin site personalizado para MediCitas Pro
    """
    site_header = "🏥 MediCitas Pro - Panel de Administración"
    site_title = "MediCitas Pro - Administración"
    index_title = "Sistema de Gestión Médica"
    
    def index(self, request, extra_context=None):
        """
        Personaliza el contexto del index del admin con estadísticas
        """
        extra_context = extra_context or {}
        
        # Obtener estadísticas
        try:
            extra_context.update({
                'total_patients': Patient.objects.count(),
                'total_doctors': Doctor.objects.filter(activo=True).count(),
                'total_appointments': Appointment.objects.count(),
                'total_clinics': Clinica.objects.count(),
            })
        except Exception:
            # En caso de error con la base de datos
            extra_context.update({
                'total_patients': 0,
                'total_doctors': 0,
                'total_appointments': 0,
                'total_clinics': 0,
            })
        
        return super().index(request, extra_context)

# Crear instancia del admin site personalizado
# medicitas_admin_site = MediCitasAdminSite(name='medicitas_admin')
