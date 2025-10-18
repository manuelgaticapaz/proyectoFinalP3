from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from faker import Faker

from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment


class Command(BaseCommand):
    help = 'Create comprehensive test data for MediCitas Pro MySQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--doctors',
            type=int,
            default=5,
            help='Number of doctors to create (default: 5)'
        )
        parser.add_argument(
            '--patients',
            type=int,
            default=50,
            help='Number of patients to create (default: 50)'
        )
        parser.add_argument(
            '--appointments',
            type=int,
            default=200,
            help='Number of appointments to create (default: 200)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba completos para MySQL...'))
        
        # Initialize Faker for realistic data
        fake = Faker('es_ES')  # Spanish locale for realistic names
        
        num_doctors = options['doctors']
        num_patients = options['patients']
        num_appointments = options['appointments']
        
        if options['clear']:
            self.clear_existing_data()
        
        # Create superuser if not exists
        self.create_superuser()
        
        # Create doctors
        doctors = self.create_doctors(fake, num_doctors)
        self.stdout.write(self.style.SUCCESS(f'Creados {len(doctors)} doctores'))
        
        # Create patients
        patients = self.create_patients(fake, num_patients)
        self.stdout.write(self.style.SUCCESS(f'Creados {len(patients)} pacientes'))
        
        # Create appointments
        appointments_created = self.create_appointments(fake, doctors, patients, num_appointments)
        self.stdout.write(self.style.SUCCESS(f'Creadas {appointments_created} citas'))
        
        # Show summary
        self.show_summary(doctors, patients, appointments_created)

    def clear_existing_data(self):
        """Clear existing test data"""
        self.stdout.write('Limpiando datos existentes...')
        
        # Delete in correct order to avoid foreign key constraints
        Appointment.objects.all().delete()
        Patient.objects.all().delete()
        Doctor.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        self.stdout.write(self.style.WARNING('Datos existentes eliminados'))

    def create_superuser(self):
        """Create superuser if not exists"""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@medicitas.com',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema'
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado: admin / admin123'))
        else:
            self.stdout.write('Superusuario ya existe: admin')

    def create_doctors(self, fake, num_doctors):
        """Create realistic doctors"""
        specialties = [
            'Cardiología', 'Pediatría', 'Neurología', 'Dermatología', 
            'Ginecología', 'Traumatología', 'Oftalmología', 'Psiquiatría',
            'Endocrinología', 'Gastroenterología', 'Neumología', 'Urología',
            'Oncología', 'Reumatología', 'Medicina Interna', 'Medicina Familiar'
        ]
        
        doctors = []
        
        for i in range(num_doctors):
            # Generate realistic names
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                first_name = fake.first_name_male()
            else:
                first_name = fake.first_name_female()
            
            last_name = fake.last_name()
            username = f"dr.{first_name.lower()}.{last_name.lower()}".replace(' ', '')
            
            # Create user
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@medicitas.com",
                    password='doctor123',
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create doctor profile
                doctor = Doctor.objects.create(
                    usuario=user,
                    nombre=first_name,
                    apellidos=last_name,
                    especialidad=random.choice(specialties),
                    telefono=fake.phone_number()[:20]  # Limit to 20 chars
                )
                
                doctors.append(doctor)
                
        return doctors

    def create_patients(self, fake, num_patients):
        """Create realistic patients"""
        priorities = ['U', 'A', 'M', 'B']
        priority_weights = [0.1, 0.2, 0.5, 0.2]  # More medium priority patients
        
        patients = []
        
        for i in range(num_patients):
            # Generate realistic patient data
            gender = random.choice(['M', 'F'])
            if gender == 'M':
                first_name = fake.first_name_male()
            else:
                first_name = fake.first_name_female()
            
            last_name = fake.last_name()
            
            # Generate realistic DNI (Spanish format)
            dni = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
            
            # Generate birth date (age between 0 and 90)
            birth_date = fake.date_of_birth(minimum_age=0, maximum_age=90)
            
            # Generate medical history based on age
            age = (timezone.now().date() - birth_date).days // 365
            medical_conditions = self.generate_medical_history(fake, age)
            
            # Generate contact information
            contact_info = self.generate_contact_info(fake)
            
            # Ensure unique DNI
            if not Patient.objects.filter(dni=dni).exists():
                patient = Patient.objects.create(
                    nombre=first_name,
                    apellidos=last_name,
                    dni=dni,
                    fecha_nacimiento=birth_date,
                    prioridad=random.choices(priorities, weights=priority_weights)[0],
                    historial_medico_basico=medical_conditions,
                    informacion_contacto=contact_info
                )
                
                patients.append(patient)
        
        return patients

    def generate_medical_history(self, fake, age):
        """Generate realistic medical history based on age"""
        conditions = []
        
        # Age-based conditions
        if age > 60:
            conditions.extend(random.sample([
                'Hipertensión arterial', 'Diabetes tipo 2', 'Artritis',
                'Colesterol alto', 'Problemas cardíacos'
            ], k=random.randint(0, 3)))
        elif age > 40:
            conditions.extend(random.sample([
                'Hipertensión leve', 'Colesterol borderline', 
                'Dolor de espalda crónico'
            ], k=random.randint(0, 2)))
        elif age < 18:
            conditions.extend(random.sample([
                'Asma infantil', 'Alergias alimentarias', 'Dermatitis'
            ], k=random.randint(0, 1)))
        
        # Common allergies
        if random.random() < 0.3:  # 30% have allergies
            allergies = random.sample([
                'Penicilina', 'Aspirina', 'Mariscos', 'Frutos secos', 'Polen'
            ], k=random.randint(1, 2))
            conditions.extend([f"Alergia a {allergy}" for allergy in allergies])
        
        # Current medications
        if conditions and random.random() < 0.6:  # 60% with conditions take medication
            medications = random.sample([
                'Paracetamol según necesidad', 'Ibuprofeno 400mg',
                'Enalapril 10mg diario', 'Metformina 850mg'
            ], k=random.randint(1, 2))
            conditions.extend([f"Medicación: {med}" for med in medications])
        
        return '. '.join(conditions) if conditions else 'Sin antecedentes médicos relevantes'

    def generate_contact_info(self, fake):
        """Generate realistic contact information"""
        phone = fake.phone_number()
        email = fake.email()
        address = fake.address().replace('\n', ', ')
        
        # Emergency contact
        emergency_name = fake.name()
        emergency_phone = fake.phone_number()
        
        contact_info = f"Teléfono: {phone}\n"
        contact_info += f"Email: {email}\n"
        contact_info += f"Dirección: {address}\n"
        contact_info += f"Contacto emergencia: {emergency_name} - {emergency_phone}"
        
        return contact_info

    def create_appointments(self, fake, doctors, patients, num_appointments):
        """Create realistic appointments"""
        if not doctors or not patients:
            self.stdout.write(self.style.WARNING('No hay doctores o pacientes para crear citas'))
            return 0
        
        appointment_reasons = [
            'Consulta de control general',
            'Seguimiento de tratamiento',
            'Dolor de cabeza recurrente',
            'Chequeo médico anual',
            'Renovación de recetas',
            'Consulta por síntomas gripales',
            'Control de presión arterial',
            'Evaluación de resultados de laboratorio',
            'Consulta dermatológica',
            'Dolor abdominal',
            'Problemas de sueño',
            'Control de diabetes',
            'Consulta cardiológica',
            'Revisión post-operatoria',
            'Vacunación',
            'Consulta por ansiedad',
            'Control de peso',
            'Dolor de espalda',
            'Consulta ginecológica',
            'Examen de la vista'
        ]
        
        observations_templates = [
            'Paciente refiere mejoría en síntomas',
            'Se recomienda continuar con tratamiento actual',
            'Signos vitales dentro de parámetros normales',
            'Se solicitan estudios complementarios',
            'Paciente presenta buen estado general',
            'Se ajusta dosis de medicación',
            'Control en 30 días',
            'Se deriva a especialista',
            'Tratamiento sintomático indicado',
            'Evolución favorable del cuadro'
        ]
        
        appointments_created = 0
        
        # Create appointments distributed over time
        start_date = timezone.now().date() - timedelta(days=90)  # 3 months ago
        end_date = timezone.now().date() + timedelta(days=60)    # 2 months ahead
        
        for _ in range(num_appointments):
            try:
                # Random date within range
                random_date = fake.date_between(start_date=start_date, end_date=end_date)
                
                # Random time during business hours (8 AM to 6 PM)
                hour = random.randint(8, 17)
                minute = random.choice([0, 15, 30, 45])  # 15-minute intervals
                
                appointment_datetime = timezone.make_aware(
                    datetime.combine(random_date, datetime.min.time().replace(hour=hour, minute=minute))
                )
                
                # Select random doctor and patient
                doctor = random.choice(doctors)
                patient = random.choice(patients)
                
                # Check for conflicts (same doctor, same time)
                if not Appointment.objects.filter(doctor=doctor, fecha=appointment_datetime).exists():
                    # Generate realistic reason and observations
                    reason = random.choice(appointment_reasons)
                    
                    # Add specialty-specific reasons
                    if 'cardio' in doctor.especialidad.lower():
                        reason = random.choice([
                            'Control cardiológico', 'Evaluación de arritmias',
                            'Control de hipertensión', 'Ecocardiograma de control'
                        ])
                    elif 'pediatr' in doctor.especialidad.lower():
                        reason = random.choice([
                            'Control de crecimiento', 'Vacunación infantil',
                            'Consulta pediátrica', 'Control del niño sano'
                        ])
                    
                    observations = ''
                    if random.random() < 0.7:  # 70% have observations
                        observations = random.choice(observations_templates)
                        
                        # Add specific observations for past appointments
                        if appointment_datetime < timezone.now():
                            observations += f". Peso: {random.randint(45, 120)}kg. "
                            observations += f"Presión: {random.randint(110, 140)}/{random.randint(70, 90)} mmHg."
                    
                    appointment = Appointment.objects.create(
                        doctor=doctor,
                        paciente=patient,
                        fecha=appointment_datetime,
                        motivo=reason,
                        observaciones=observations
                    )
                    
                    appointments_created += 1
                    
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error creando cita: {e}'))
                continue
        
        return appointments_created

    def show_summary(self, doctors, patients, appointments_created):
        """Show creation summary with statistics"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CREADOS'))
        self.stdout.write('='*60)
        
        # Basic counts
        self.stdout.write(f'Doctores creados: {len(doctors)}')
        self.stdout.write(f'Pacientes creados: {len(patients)}')
        self.stdout.write(f'Citas creadas: {appointments_created}')
        
        # Doctor specialties
        if doctors:
            self.stdout.write('\nEspecialidades de doctores:')
            specialties = {}
            for doctor in doctors:
                spec = doctor.especialidad
                specialties[spec] = specialties.get(spec, 0) + 1
            
            for specialty, count in specialties.items():
                self.stdout.write(f'  - {specialty}: {count}')
        
        # Patient priorities
        if patients:
            self.stdout.write('\nDistribución de prioridades:')
            priorities = {'U': 0, 'A': 0, 'M': 0, 'B': 0}
            for patient in patients:
                priorities[patient.prioridad] += 1
            
            priority_names = {'U': 'Urgente', 'A': 'Alta', 'M': 'Media', 'B': 'Baja'}
            for priority, count in priorities.items():
                percentage = (count / len(patients)) * 100
                self.stdout.write(f'  - {priority_names[priority]}: {count} ({percentage:.1f}%)')
        
        # Appointment distribution
        if appointments_created > 0:
            today = timezone.now().date()
            past_appointments = Appointment.objects.filter(fecha__date__lt=today).count()
            future_appointments = Appointment.objects.filter(fecha__date__gte=today).count()
            
            self.stdout.write('\nDistribución temporal de citas:')
            self.stdout.write(f'  - Citas pasadas: {past_appointments}')
            self.stdout.write(f'  - Citas futuras: {future_appointments}')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('CREDENCIALES DE ACCESO'))
        self.stdout.write('='*60)
        self.stdout.write('Administrador: admin / admin123')
        
        if doctors:
            self.stdout.write('\nDoctores (todos con contraseña: doctor123):')
            for doctor in doctors[:5]:  # Show first 5
                self.stdout.write(f'  - {doctor.usuario.username} (Dr. {doctor.nombre} {doctor.apellidos} - {doctor.especialidad})')
            
            if len(doctors) > 5:
                self.stdout.write(f'  ... y {len(doctors) - 5} doctores más')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('¡Datos de prueba creados exitosamente!'))
        self.stdout.write('Ejecute: python manage.py create_stored_procedures')
        self.stdout.write('Luego inicie el servidor: python manage.py runserver')
        self.stdout.write('='*60)
