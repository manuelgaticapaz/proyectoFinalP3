from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment


class Command(BaseCommand):
    help = 'Create demo data for MediCitas Pro'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba para MediCitas Pro...'))
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@medicitas.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin / admin123'))
        else:
            self.stdout.write('Superusuario ya existe: admin')
        
        # Create test doctors
        doctors_data = [
            {
                'username': 'dr.martinez',
                'email': 'martinez@medicitas.com',
                'password': 'doctor123',
                'first_name': 'Carlos',
                'last_name': 'Martínez',
                'especialidad': 'Cardiología',
                'telefono': '+1234567890',
                'direccion': 'Av. Principal 123, Ciudad'
            },
            {
                'username': 'dra.rodriguez',
                'email': 'rodriguez@medicitas.com',
                'password': 'doctor123',
                'first_name': 'Ana',
                'last_name': 'Rodríguez',
                'especialidad': 'Pediatría',
                'telefono': '+1234567891',
                'direccion': 'Calle Secundaria 456, Ciudad'
            }
        ]
        
        created_doctors = []
        for doctor_data in doctors_data:
            if not User.objects.filter(username=doctor_data['username']).exists():
                user = User.objects.create_user(
                    username=doctor_data['username'],
                    email=doctor_data['email'],
                    password=doctor_data['password'],
                    first_name=doctor_data['first_name'],
                    last_name=doctor_data['last_name']
                )
                
                doctor = Doctor.objects.create(
                    usuario=user,
                    nombre=doctor_data['first_name'],
                    apellidos=doctor_data['last_name'],
                    especialidad=doctor_data['especialidad'],
                    telefono=doctor_data['telefono']
                )
                created_doctors.append(doctor)
                self.stdout.write(self.style.SUCCESS(f'Doctor creado: {doctor_data["username"]} / doctor123'))
            else:
                user = User.objects.get(username=doctor_data['username'])
                try:
                    doctor = Doctor.objects.get(usuario=user)
                    created_doctors.append(doctor)
                    self.stdout.write(f'Doctor ya existe: {doctor_data["username"]}')
                except Doctor.DoesNotExist:
                    # User exists but doctor profile doesn't, create it
                    doctor = Doctor.objects.create(
                        usuario=user,
                        nombre=doctor_data['first_name'],
                        apellidos=doctor_data['last_name'],
                        especialidad=doctor_data['especialidad'],
                        telefono=doctor_data['telefono']
                    )
                    created_doctors.append(doctor)
                    self.stdout.write(self.style.SUCCESS(f'Perfil de doctor creado para usuario existente: {doctor_data["username"]}'))
        
        # Create test patients
        patients_data = [
            {
                'nombre': 'Juan',
                'apellidos': 'Pérez García',
                'dni': '12345678A',
                'fecha_nacimiento': '1985-03-15',
                'prioridad': 'M',
                'historial_medico_basico': 'Hipertensión controlada, alergia a penicilina',
                'informacion_contacto': 'Tel: +1111111111, Email: juan.perez@email.com'
            },
            {
                'nombre': 'María',
                'apellidos': 'González López',
                'dni': '87654321B',
                'fecha_nacimiento': '1990-07-22',
                'prioridad': 'A',
                'historial_medico_basico': 'Diabetes tipo 2, seguimiento nutricional',
                'informacion_contacto': 'Tel: +2222222222, Email: maria.gonzalez@email.com'
            },
            {
                'nombre': 'Pedro',
                'apellidos': 'Martín Ruiz',
                'dni': '11223344C',
                'fecha_nacimiento': '1978-12-03',
                'prioridad': 'B',
                'historial_medico_basico': 'Paciente sano, chequeos rutinarios',
                'informacion_contacto': 'Tel: +3333333333, Email: pedro.martin@email.com'
            }
        ]
        
        created_patients = []
        for patient_data in patients_data:
            if not Patient.objects.filter(dni=patient_data['dni']).exists():
                patient = Patient.objects.create(
                    nombre=patient_data['nombre'],
                    apellidos=patient_data['apellidos'],
                    dni=patient_data['dni'],
                    fecha_nacimiento=datetime.strptime(patient_data['fecha_nacimiento'], '%Y-%m-%d').date(),
                    prioridad=patient_data['prioridad'],
                    historial_medico_basico=patient_data['historial_medico_basico'],
                    informacion_contacto=patient_data['informacion_contacto']
                )
                created_patients.append(patient)
                self.stdout.write(self.style.SUCCESS(f'Paciente creado: {patient_data["nombre"]} {patient_data["apellidos"]}'))
            else:
                patient = Patient.objects.get(dni=patient_data['dni'])
                created_patients.append(patient)
                self.stdout.write(f'Paciente ya existe: {patient_data["nombre"]} {patient_data["apellidos"]}')
        
        # Create test appointments
        self.stdout.write('\nCreando citas de prueba...')
        
        today = timezone.now().date()
        
        appointment_templates = [
            {
                'motivo': 'Consulta de control cardiovascular',
                'observaciones': 'Revisar presión arterial y medicación actual'
            },
            {
                'motivo': 'Chequeo pediátrico rutinario',
                'observaciones': 'Vacunas al día, desarrollo normal'
            },
            {
                'motivo': 'Consulta por dolor de cabeza recurrente',
                'observaciones': 'Evaluar posibles causas'
            }
        ]
        
        appointments_created = 0
        for i in range(10):  # Create 10 appointments
            random_days = random.randint(1, 15)
            appointment_date = today + timedelta(days=random_days)
            
            random_hour = random.randint(9, 16)
            random_minute = random.choice([0, 30])
            
            appointment_datetime = timezone.make_aware(
                datetime.combine(appointment_date, datetime.min.time().replace(hour=random_hour, minute=random_minute))
            )
            
            doctor = random.choice(created_doctors)
            patient = random.choice(created_patients)
            template = random.choice(appointment_templates)
            
            if not Appointment.objects.filter(doctor=doctor, fecha=appointment_datetime).exists():
                appointment = Appointment.objects.create(
                    doctor=doctor,
                    paciente=patient,
                    fecha=appointment_datetime,
                    motivo=template['motivo'],
                    observaciones=template['observaciones']
                )
                appointments_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'{appointments_created} citas creadas'))
        
        self.stdout.write(self.style.SUCCESS('\nDatos de prueba creados exitosamente!'))
        self.stdout.write('\nCredenciales de acceso:')
        self.stdout.write('Administrador: admin / admin123')
        self.stdout.write('Doctores: dr.martinez / doctor123, dra.rodriguez / doctor123')
        self.stdout.write(f'\nResumen: {len(created_doctors)} doctores, {len(created_patients)} pacientes, {appointments_created} citas')
