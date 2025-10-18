from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .forms import AppointmentForm
from .models import Appointment
from .serializers import AppointmentSerializaer
from doctors.models import Doctor
from doctors.utils import get_appointment_conflicts, suggest_optimal_appointment_time
from rest_framework import viewsets

@login_required
def crear_cita(request):
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')

    if request.method == "POST":
        form = AppointmentForm(request.POST, doctor=doctor)
        if form.is_valid():
            try:
                cita = form.save(commit=False)
                cita.doctor = doctor
                cita.save()
                
                messages.success(
                    request, 
                    f'¡Cita creada exitosamente! '
                    f'Paciente: {cita.paciente.nombre} {cita.paciente.apellidos} - '
                    f'Fecha: {cita.fecha.strftime("%d/%m/%Y a las %H:%M")}'
                )
                return redirect('doctor_dashboard')
            except Exception as e:
                messages.error(request, f'Error al guardar la cita: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AppointmentForm(doctor=doctor)
    
    # Get suggested times for today and tomorrow
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    suggested_times_today = suggest_optimal_appointment_time(doctor, today)
    suggested_times_tomorrow = suggest_optimal_appointment_time(doctor, tomorrow)
    
    context = {
        'form': form,
        'doctor': doctor,
        'suggested_times_today': suggested_times_today[:3],  # First 3 suggestions
        'suggested_times_tomorrow': suggested_times_tomorrow[:3],
        'today': today,
        'tomorrow': tomorrow,
    }
    
    return render(request, 'crear_cita.html', context)

@login_required
def check_appointment_availability(request):
    """AJAX endpoint to check appointment availability"""
    if request.method == 'GET':
        doctor = get_object_or_404(Doctor, usuario=request.user)
        fecha_str = request.GET.get('fecha')
        
        if not fecha_str:
            return JsonResponse({'error': 'Fecha requerida'}, status=400)
        
        try:
            fecha = timezone.datetime.fromisoformat(fecha_str.replace('Z', '+00:00'))
            
            # Check for conflicts
            start_time = fecha - timedelta(minutes=15)
            end_time = fecha + timedelta(minutes=15)
            
            conflicts = get_appointment_conflicts(doctor, start_time, end_time)
            
            if conflicts:
                return JsonResponse({
                    'available': False,
                    'message': 'Ya existe una cita programada cerca de esta hora.',
                    'suggestions': suggest_optimal_appointment_time(doctor, fecha.date())[:3]
                })
            else:
                return JsonResponse({
                    'available': True,
                    'message': 'Horario disponible'
                })
                
        except ValueError:
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required
def editar_cita(request, cita_id):
    """Edit an existing appointment"""
    doctor = get_object_or_404(Doctor, usuario=request.user)
    cita = get_object_or_404(Appointment, id=cita_id, doctor=doctor)
    
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=cita, doctor=doctor)
        if form.is_valid():
            try:
                cita_actualizada = form.save()
                messages.success(
                    request, 
                    f'¡Cita actualizada exitosamente! '
                    f'Paciente: {cita_actualizada.paciente.nombre} {cita_actualizada.paciente.apellidos}'
                )
                return redirect('doctor_dashboard')
            except Exception as e:
                messages.error(request, f'Error al actualizar la cita: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AppointmentForm(instance=cita, doctor=doctor)
    
    context = {
        'form': form,
        'cita': cita,
        'doctor': doctor,
        'editing': True,
    }
    
    return render(request, 'crear_cita.html', context)

@login_required
def eliminar_cita(request, cita_id):
    """Delete an appointment"""
    doctor = get_object_or_404(Doctor, usuario=request.user)
    cita = get_object_or_404(Appointment, id=cita_id, doctor=doctor)
    
    if request.method == "POST":
        paciente_nombre = f"{cita.paciente.nombre} {cita.paciente.apellidos}"
        fecha_cita = cita.fecha.strftime("%d/%m/%Y a las %H:%M")
        
        cita.delete()
        messages.success(
            request, 
            f'Cita eliminada exitosamente. Paciente: {paciente_nombre} - Fecha: {fecha_cita}'
        )
        return redirect('doctor_dashboard')
    
    context = {
        'cita': cita,
        'doctor': doctor,
    }
    
    return render(request, 'confirmar_eliminar_cita.html', context)

class AppointmentsViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-id') # Define el conjunto de datos base
    serializer_class = AppointmentSerializaer