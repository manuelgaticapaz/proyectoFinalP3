from django.core.management.base import BaseCommand
from core.database_utils import MySQLStoredProcedures


class Command(BaseCommand):
    help = 'Create MySQL stored procedures for MediCitas Pro'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando stored procedures de MySQL...'))
        
        try:
            MySQLStoredProcedures.create_all_procedures()
            self.stdout.write(self.style.SUCCESS('Stored procedures creados exitosamente!'))
            
            self.stdout.write('\nStored procedures disponibles:')
            self.stdout.write('- FilterAppointmentsByDate: Filtrar citas por fecha y prioridad')
            self.stdout.write('- GetDoctorStatistics: Estadisticas completas de doctor')
            self.stdout.write('- GetPatientStatistics: Estadisticas de pacientes por doctor')
            self.stdout.write('- GetAppointmentAnalytics: Analytics de citas por periodo')
            self.stdout.write('- FilterPatients: Filtrado avanzado de pacientes')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creando stored procedures: {e}'))
            self.stdout.write('Asegurate de que MySQL este corriendo y la base de datos exista.')
