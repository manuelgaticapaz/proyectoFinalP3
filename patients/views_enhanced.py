from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from rest_framework import viewsets
from .serializers import PatientSerializaer

@login_required
def lista_pacientes(request):
    """List all patients with search and filtering"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Get search query
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', '')
    
    # Base queryset - patients that have appointments with this doctor
    patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct()
    
    # Apply search filter
    if search_query:
        patients = patients.filter(
            Q(nombre__icontains=search_query) |
            Q(apellidos__icontains=search_query) |
            Q(dni__icontains=search_query) |
            Q(informacion_contacto__icontains=search_query)
        )
    
    # Apply priority filter
    if priority_filter:
        patients = patients.filter(prioridad=priority_filter)
    
    # Annotate with appointment count
    patients = patients.annotate(
        total_appointments=Count('appointment', filter=Q(appointment__doctor=doctor))
    ).order_by('nombre', 'apellidos')
    
    # Pagination
    paginator = Paginator(patients, 12)  # 12 patients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get priority choices for filter dropdown
    priority_choices = Patient.PRIORIDAD_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'priority_filter': priority_filter,
        'priority_choices': priority_choices,
        'doctor': doctor,
        'total_patients': patients.count(),
    }
    
    return render(request, 'patients/lista_pacientes.html', context)

@login_required
def detalle_paciente(request, paciente_id):
    """Patient detail view with appointment history"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Get patient - must be accessible to this doctor
    paciente = get_object_or_404(
        Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct(),
        id=paciente_id
    )
    
    # Get appointment history for this doctor
    appointments = Appointment.objects.filter(
        paciente=paciente,
        doctor=doctor
    ).order_by('-fecha')
    
    # Pagination for appointments
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)
    
    # Get statistics
    total_appointments = appointments.count()
    upcoming_appointments = appointments.filter(fecha__gt=timezone.now()).count()
    completed_appointments = appointments.filter(fecha__lte=timezone.now()).count()
    
    context = {
        'paciente': paciente,
        'appointments_page': appointments_page,
        'doctor': doctor,
        'total_appointments': total_appointments,
        'upcoming_appointments': upcoming_appointments,
        'completed_appointments': completed_appointments,
    }
    
    return render(request, 'patients/detalle_paciente.html', context)

@login_required
def buscar_pacientes_ajax(request):
    """AJAX endpoint for patient search"""
    if request.method == 'GET':
        try:
            doctor = Doctor.objects.get(usuario=request.user)
        except Doctor.DoesNotExist:
            return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
        
        query = request.GET.get('q', '')
        
        if len(query) < 2:
            return JsonResponse({'patients': []})
        
        patients = Patient.objects.filter(
            appointment__doctor=doctor
        ).filter(
            Q(nombre__icontains=query) |
            Q(apellidos__icontains=query) |
            Q(dni__icontains=query)
        ).distinct()[:10]  # Limit to 10 results
        
        patient_data = []
        for patient in patients:
            patient_data.append({
                'id': patient.id,
                'name': f"{patient.nombre} {patient.apellidos}",
                'dni': patient.dni,
                'priority': patient.get_prioridad_display(),
                'priority_class': get_priority_class(patient.prioridad)
            })
        
        return JsonResponse({'patients': patient_data})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def get_priority_class(priority):
    """Get CSS class for priority badge"""
    priority_classes = {
        'U': 'bg-danger',    # Urgente
        'A': 'bg-warning',   # Alta
        'M': 'bg-info',      # Media
        'B': 'bg-success',   # Baja
    }
    return priority_classes.get(priority, 'bg-secondary')

@login_required
def estadisticas_pacientes(request):
    """Patient statistics dashboard"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Get all patients for this doctor
    patients = Patient.objects.filter(
        appointment__doctor=doctor
    ).distinct()
    
    # Priority breakdown
    priority_stats = patients.values('prioridad').annotate(
        count=Count('id')
    ).order_by('prioridad')
    
    # Age groups (if birth_date is available)
    # This would require adding birth_date field to Patient model
    
    # Most frequent patients (by appointment count)
    frequent_patients = patients.annotate(
        appointment_count=Count('appointment', filter=Q(appointment__doctor=doctor))
    ).filter(appointment_count__gt=0).order_by('-appointment_count')[:10]
    
    # Recent patients (by last appointment)
    recent_patients = patients.filter(
        appointment__doctor=doctor
    ).annotate(
        last_appointment=Max('appointment__fecha')
    ).order_by('-last_appointment')[:10]
    
    context = {
        'doctor': doctor,
        'total_patients': patients.count(),
        'priority_stats': priority_stats,
        'frequent_patients': frequent_patients,
        'recent_patients': recent_patients,
    }
    
    return render(request, 'patients/estadisticas_pacientes.html', context)

# Keep the existing ViewSet for API
class PatientsViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-id')
    serializer_class = PatientSerializaer
