from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from core.database_utils import MySQLStoredProcedures
from .forms import PatientForm


@login_required
def patient_dashboard(request):
    """Dashboard principal de gestión de pacientes"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Filtros
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', '')
    age_min = request.GET.get('age_min', '')
    age_max = request.GET.get('age_max', '')
    
    # Convertir filtros de edad
    age_min_int = int(age_min) if age_min.isdigit() else None
    age_max_int = int(age_max) if age_max.isdigit() else None
    
    # Paginación
    page = request.GET.get('page', 1)
    per_page = 12
    offset = (int(page) - 1) * per_page
    
    try:
        # Usar stored procedure para filtrar pacientes
        patients_data = MySQLStoredProcedures.call_filter_patients(
            doctor_id=doctor.id,
            search_term=search_query if search_query else None,
            priority_filter=priority_filter if priority_filter else None,
            age_min=age_min_int,
            age_max=age_max_int,
            limit_count=per_page,
            offset_count=offset
        )
        
        # Obtener estadísticas de pacientes
        patient_stats = MySQLStoredProcedures.call_patient_statistics(doctor.id)
        
    except Exception as e:
        # Fallback a consultas Django si los SP no están disponibles
        messages.warning(request, 'Usando consultas básicas. Ejecute: python manage.py create_stored_procedures')
        
        patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct()
        
        if search_query:
            patients = patients.filter(
                Q(nombre__icontains=search_query) |
                Q(apellidos__icontains=search_query) |
                Q(dni__icontains=search_query) |
                Q(informacion_contacto__icontains=search_query)
            )
        
        if priority_filter:
            patients = patients.filter(prioridad=priority_filter)
        
        patients = patients.annotate(
            total_appointments=Count('appointment', filter=Q(appointment__doctor=doctor))
        ).order_by('apellidos', 'nombre')
        
        # Paginación manual
        paginator = Paginator(patients, per_page)
        page_obj = paginator.get_page(page)
        
        patients_data = []
        for patient in page_obj:
            age = None
            if patient.fecha_nacimiento:
                age = timezone.now().date().year - patient.fecha_nacimiento.year
            
            patients_data.append({
                'id': patient.id,
                'nombre': patient.nombre,
                'apellidos': patient.apellidos,
                'dni': patient.dni,
                'prioridad': patient.prioridad,
                'priority_display': patient.get_prioridad_display(),
                'age': age,
                'total_appointments': patient.total_appointments,
                'last_appointment': None,  # Requeriría consulta adicional
            })
        
        patient_stats = []
    
    # Choices para filtros
    priority_choices = Patient.PRIORITY_CHOICES
    
    # Calcular el total de citas del doctor
    total_appointments_count = Appointment.objects.filter(doctor=doctor).count()
    
    context = {
        'patients_data': patients_data,
        'patient_stats': patient_stats[:10],  # Top 10 pacientes
        'doctor': doctor,
        'search_query': search_query,
        'priority_filter': priority_filter,
        'age_min': age_min,
        'age_max': age_max,
        'priority_choices': priority_choices,
        'total_patients': len(patients_data),
        'total_appointments_count': total_appointments_count,
        'current_page': int(page),
        'has_next': len(patients_data) == per_page,  # Aproximación
        'has_previous': int(page) > 1,
    }
    
    return render(request, 'patients/dashboard.html', context)


@login_required
def create_patient(request):
    """Crear nuevo paciente"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            try:
                patient = form.save()
                messages.success(
                    request, 
                    f'Paciente {patient.nombre} {patient.apellidos} creado exitosamente.'
                )
                return redirect('patient_dashboard')
            except Exception as e:
                messages.error(request, f'Error al crear el paciente: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PatientForm()
    
    context = {
        'form': form,
        'doctor': doctor,
        'creating': True,
    }
    
    return render(request, 'patients/create_edit.html', context)


@login_required
def edit_patient(request, patient_id):
    """Editar paciente existente"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Verificar que el paciente tenga citas con este doctor
    patient = get_object_or_404(
        Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct(),
        id=patient_id
    )
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            try:
                patient = form.save()
                messages.success(
                    request, 
                    f'Paciente {patient.nombre} {patient.apellidos} actualizado exitosamente.'
                )
                return redirect('patient_dashboard')
            except Exception as e:
                messages.error(request, f'Error al actualizar el paciente: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = PatientForm(instance=patient)
    
    context = {
        'form': form,
        'patient': patient,
        'doctor': doctor,
        'editing': True,
    }
    
    return render(request, 'patients/create_edit.html', context)


@login_required
def patient_detail(request, patient_id):
    """Vista detallada del paciente con historial completo"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Verificar acceso al paciente
    patient = get_object_or_404(
        Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct(),
        id=patient_id
    )
    
    # Obtener historial de citas
    appointments = Appointment.objects.filter(
        paciente=patient,
        doctor=doctor
    ).order_by('-fecha')
    
    # Paginación de citas
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)
    
    # Estadísticas del paciente
    total_appointments = appointments.count()
    upcoming_appointments = appointments.filter(fecha__gt=timezone.now()).count()
    completed_appointments = appointments.filter(fecha__lte=timezone.now()).count()
    
    # Calcular edad
    age = None
    if patient.fecha_nacimiento:
        today = timezone.now().date()
        age = today.year - patient.fecha_nacimiento.year
        if today.month < patient.fecha_nacimiento.month or \
           (today.month == patient.fecha_nacimiento.month and today.day < patient.fecha_nacimiento.day):
            age -= 1
    
    context = {
        'patient': patient,
        'appointments_page': appointments_page,
        'doctor': doctor,
        'total_appointments': total_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
        'age': age,
    }
    
    return render(request, 'patients/detail.html', context)


@login_required
def patient_search_ajax(request):
    """Búsqueda AJAX de pacientes para autocompletado"""
    if request.method == 'GET':
        try:
            doctor = Doctor.objects.get(usuario=request.user)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
        
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return JsonResponse({'patients': []})
        
        try:
            # Usar stored procedure si está disponible
            patients_data = MySQLStoredProcedures.call_filter_patients(
                doctor_id=doctor.id,
                search_term=query,
                limit_count=10,
                offset_count=0
            )
            
            results = []
            for patient in patients_data:
                results.append({
                    'id': patient['id'],
                    'name': f"{patient['nombre']} {patient['apellidos']}",
                    'dni': patient['dni'],
                    'priority': patient['priority_display'],
                    'age': patient['age'],
                    'total_appointments': patient['total_appointments']
                })
            
            return JsonResponse({'patients': results})
            
        except Exception:
            # Fallback a consulta Django
            patients = Patient.objects.filter(
                appointment__doctor=doctor
            ).filter(
                Q(nombre__icontains=query) |
                Q(apellidos__icontains=query) |
                Q(dni__icontains=query)
            ).distinct()[:10]
            
            results = []
            for patient in patients:
                results.append({
                    'id': patient.id,
                    'name': f"{patient.nombre} {patient.apellidos}",
                    'dni': patient.dni,
                    'priority': patient.get_prioridad_display(),
                    'age': None,
                    'total_appointments': 0
                })
            
            return JsonResponse({'patients': results})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
