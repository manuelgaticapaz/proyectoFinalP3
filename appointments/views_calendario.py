from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
import json
import calendar

from .models import Appointment
from doctors.models import Doctor
from patients.models import Patient

@login_required
def vista_calendario(request):
    """
    Vista principal del calendario interactivo
    """
    # Obtener el mes y año actual o los especificados
    hoy = timezone.now().date()
    mes = int(request.GET.get('mes', hoy.month))
    año = int(request.GET.get('año', hoy.year))
    
    # Obtener el doctor actual (asumiendo que está logueado)
    try:
        doctor = Doctor.objects.get(usuario=request.user)
        clinica = doctor.clinica
    except Doctor.DoesNotExist:
        doctor = None
        clinica = None
    
    # Generar datos del calendario
    cal = calendar.monthcalendar(año, mes)
    
    # Obtener citas del mes
    primer_dia = datetime(año, mes, 1).date()
    if mes == 12:
        ultimo_dia = datetime(año + 1, 1, 1).date() - timedelta(days=1)
    else:
        ultimo_dia = datetime(año, mes + 1, 1).date() - timedelta(days=1)
    
    citas_query = Appointment.objects.filter(
        fecha__date__gte=primer_dia,
        fecha__date__lte=ultimo_dia
    )
    
    # Filtrar por clínica si existe
    if clinica:
        citas_query = citas_query.filter(clinica=clinica)
    
    # Filtrar por doctor si se especifica
    doctor_id = request.GET.get('doctor_id')
    if doctor_id:
        citas_query = citas_query.filter(doctor_id=doctor_id)
    
    citas = citas_query.select_related('paciente', 'doctor').order_by('fecha')
    
    # Organizar citas por día
    citas_por_dia = {}
    for cita in citas:
        dia = cita.fecha.date().day
        if dia not in citas_por_dia:
            citas_por_dia[dia] = []
        citas_por_dia[dia].append({
            'id': cita.id,
            'paciente': str(cita.paciente),
            'doctor': str(cita.doctor),
            'hora': cita.fecha.strftime('%H:%M'),
            'motivo': cita.motivo[:50] + '...' if len(cita.motivo) > 50 else cita.motivo,
            'estado': cita.estado,
        })
    
    # Obtener lista de doctores para el filtro
    doctores = Doctor.objects.filter(activo=True)
    if clinica:
        doctores = doctores.filter(clinica=clinica)
    
    context = {
        'calendario': cal,
        'mes': mes,
        'año': año,
        'mes_nombre': calendar.month_name[mes],
        'citas_por_dia': citas_por_dia,
        'doctores': doctores,
        'doctor_seleccionado': doctor_id,
        'hoy': hoy,
    }
    
    return render(request, 'appointments/calendario.html', context)

@login_required
def obtener_citas_dia(request):
    """
    API para obtener citas de un día específico
    """
    fecha_str = request.GET.get('fecha')
    if not fecha_str:
        return JsonResponse({'error': 'Fecha requerida'}, status=400)
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    # Obtener doctor y clínica
    try:
        doctor = Doctor.objects.get(usuario=request.user)
        clinica = doctor.clinica
    except Doctor.DoesNotExist:
        doctor = None
        clinica = None
    
    # Obtener citas del día
    citas_query = Appointment.objects.filter(fecha__date=fecha)
    
    if clinica:
        citas_query = citas_query.filter(clinica=clinica)
    
    citas = citas_query.select_related('paciente', 'doctor').order_by('fecha')
    
    citas_data = []
    for cita in citas:
        citas_data.append({
            'id': cita.id,
            'paciente': str(cita.paciente),
            'doctor': str(cita.doctor),
            'fecha': cita.fecha.strftime('%Y-%m-%d'),
            'hora': cita.fecha.strftime('%H:%M'),
            'motivo': cita.motivo,
            'estado': cita.estado,
            'observaciones': cita.observaciones or '',
        })
    
    return JsonResponse({'citas': citas_data})

@csrf_exempt
@login_required
def reagendar_cita(request):
    """
    API para reagendar una cita (drag & drop)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        cita_id = data.get('cita_id')
        nueva_fecha = data.get('nueva_fecha')
        nueva_hora = data.get('nueva_hora')
        
        if not all([cita_id, nueva_fecha, nueva_hora]):
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Obtener la cita
        cita = get_object_or_404(Appointment, id=cita_id)
        
        # Verificar permisos (solo el doctor de la cita o admin puede reagendar)
        try:
            doctor_usuario = Doctor.objects.get(usuario=request.user)
            if cita.doctor != doctor_usuario and not request.user.is_staff:
                return JsonResponse({'error': 'Sin permisos para reagendar esta cita'}, status=403)
        except Doctor.DoesNotExist:
            if not request.user.is_staff:
                return JsonResponse({'error': 'Sin permisos'}, status=403)
        
        # Crear nueva fecha y hora
        nueva_datetime = datetime.strptime(f"{nueva_fecha} {nueva_hora}", '%Y-%m-%d %H:%M')
        nueva_datetime = timezone.make_aware(nueva_datetime)
        
        # Verificar que no haya conflictos
        conflictos = Appointment.objects.filter(
            doctor=cita.doctor,
            fecha=nueva_datetime
        ).exclude(id=cita.id)
        
        if conflictos.exists():
            return JsonResponse({
                'error': 'Ya existe una cita en ese horario',
                'conflicto': True
            }, status=400)
        
        # Actualizar la cita
        fecha_anterior = cita.fecha
        cita.fecha = nueva_datetime
        cita.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Cita reagendada exitosamente',
            'fecha_anterior': fecha_anterior.strftime('%Y-%m-%d %H:%M'),
            'fecha_nueva': nueva_datetime.strftime('%Y-%m-%d %H:%M')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def horarios_disponibles(request):
    """
    API para obtener horarios disponibles de un doctor en una fecha
    """
    doctor_id = request.GET.get('doctor_id')
    fecha_str = request.GET.get('fecha')
    
    if not all([doctor_id, fecha_str]):
        return JsonResponse({'error': 'Doctor y fecha requeridos'}, status=400)
    
    try:
        doctor = get_object_or_404(Doctor, id=doctor_id)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    # Obtener citas existentes del doctor en esa fecha
    citas_existentes = Appointment.objects.filter(
        doctor=doctor,
        fecha__date=fecha
    ).values_list('fecha__time', flat=True)
    
    # Generar horarios disponibles (cada 30 minutos de 8:00 a 18:00)
    horarios_disponibles = []
    hora_inicio = datetime.strptime('08:00', '%H:%M').time()
    hora_fin = datetime.strptime('18:00', '%H:%M').time()
    
    hora_actual = datetime.combine(fecha, hora_inicio)
    hora_limite = datetime.combine(fecha, hora_fin)
    
    while hora_actual < hora_limite:
        if hora_actual.time() not in citas_existentes:
            horarios_disponibles.append(hora_actual.strftime('%H:%M'))
        hora_actual += timedelta(minutes=30)
    
    return JsonResponse({'horarios': horarios_disponibles})
