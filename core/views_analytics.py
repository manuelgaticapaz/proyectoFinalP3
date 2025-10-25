from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count, Q, Avg
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
# from core.database_utils import MySQLStoredProcedures  # Comentado temporalmente
import json


@login_required
def analytics_dashboard(request):
    """Dashboard principal de analytics y reportes"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Parámetros de fecha
    end_date = request.GET.get('end_date', timezone.now().date().strftime('%Y-%m-%d'))
    start_date = request.GET.get('start_date', (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Formato de fecha inválido.')
        start_date_obj = timezone.now().date() - timedelta(days=30)
        end_date_obj = timezone.now().date()
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    # Usar consultas Django directamente (más confiable)
    # Estadísticas básicas del doctor
    total_appointments = Appointment.objects.filter(doctor=doctor).count()
    today_appointments = Appointment.objects.filter(
        doctor=doctor, 
        fecha__date=timezone.now().date()
    ).count()
    
    week_start = timezone.now().date() - timedelta(days=7)
    month_start = timezone.now().date() - timedelta(days=30)
    
    week_appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__gte=week_start
    ).count()
    
    month_appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__gte=month_start
    ).count()
    
    doctor_stats = {
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'week_appointments': week_appointments,
        'month_appointments': month_appointments,
        'total_patients': Patient.objects.filter(appointment__doctor=doctor).distinct().count(),
        'upcoming_appointments': Appointment.objects.filter(
            doctor=doctor, 
            fecha__gt=timezone.now()
        ).count(),
    }
    
    # Estadísticas de pacientes
    patient_stats = Patient.objects.filter(
        appointment__doctor=doctor
    ).annotate(
        total_appointments=Count('appointment')
    ).order_by('-total_appointments')[:10]
    
    # Analytics de citas en el período
    appointment_analytics = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__range=[start_date_obj, end_date_obj]
    ).values('fecha__date').annotate(
        count=Count('id')
    ).order_by('fecha__date')
    
    # Citas filtradas
    filtered_appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__range=[start_date_obj, end_date_obj]
    ).select_related('paciente').order_by('-fecha')[:20]
    
    # Preparar datos para gráficos
    chart_data = prepare_chart_data(doctor, start_date_obj, end_date_obj)
    
    context = {
        'doctor': doctor,
        'doctor_stats': doctor_stats,
        'patient_stats': patient_stats[:10],  # Top 10
        'appointment_analytics': appointment_analytics,
        'filtered_appointments': filtered_appointments[:20],  # Últimas 20
        'start_date': start_date,
        'end_date': end_date,
        'chart_data': json.dumps(chart_data),
        'date_range_days': (end_date_obj - start_date_obj).days,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def appointment_analytics_ajax(request):
    """AJAX endpoint para analytics de citas"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    chart_type = request.GET.get('chart_type', 'appointments_by_day')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    try:
        if chart_type == 'appointments_by_day':
            data = get_appointments_by_day_chart(doctor, start_date_obj, end_date_obj)
        elif chart_type == 'priority_distribution':
            data = get_priority_distribution_chart(doctor, start_date_obj, end_date_obj)
        elif chart_type == 'patient_age_groups':
            data = get_patient_age_groups_chart(doctor)
        elif chart_type == 'appointments_by_hour':
            data = get_appointments_by_hour_chart(doctor, start_date_obj, end_date_obj)
        else:
            return JsonResponse({'error': 'Tipo de gráfico no válido'}, status=400)
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': f'Error generando gráfico: {str(e)}'}, status=500)


@login_required
def export_analytics_report(request):
    """Exportar reporte de analytics en formato JSON/CSV"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    format_type = request.GET.get('format', 'json')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Generar reporte completo
        report_data = {
            'doctor': {
                'name': f"{doctor.nombre} {doctor.apellidos}",
                'specialty': doctor.especialidad,
                'phone': doctor.telefono
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date_obj - start_date_obj).days
            },
            'generated_at': timezone.now().isoformat(),
        }
        
        # Usar consultas Django básicas
        appointments = Appointment.objects.filter(
            doctor=doctor,
            fecha__date__range=[start_date_obj, end_date_obj]
        )
        
        report_data.update({
            'statistics': {
                'total_appointments_period': appointments.count(),
                'unique_patients_period': appointments.values('paciente').distinct().count(),
                'total_appointments_doctor': Appointment.objects.filter(doctor=doctor).count(),
            },
            'data_source': 'django_queries'
        })
        
        if format_type == 'json':
            response = JsonResponse(report_data, json_dumps_params={'indent': 2})
            response['Content-Disposition'] = f'attachment; filename="analytics_report_{start_date}_{end_date}.json"'
            return response
        
        # TODO: Implementar exportación CSV si se necesita
        return JsonResponse({'error': 'Formato no soportado'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': f'Error generando reporte: {str(e)}'}, status=500)


def prepare_chart_data(doctor, start_date, end_date):
    """Preparar datos para gráficos del dashboard"""
    chart_data = {}
    
    try:
        # Usar consultas Django básicas (más confiable)
        appointments = Appointment.objects.filter(
            doctor=doctor,
            fecha__date__range=[start_date, end_date]
        ).select_related('paciente')
        
        # Inicializar contadores
        daily_counts = {}
        priority_counts = {'Urgente': 0, 'Alta': 0, 'Media': 0, 'Baja': 0}
        hourly_counts = {i: 0 for i in range(8, 19)}  # 8 AM to 6 PM
        
        # Procesar citas
        for apt in appointments:
            # Citas por día
            apt_date = apt.fecha.strftime('%Y-%m-%d')
            daily_counts[apt_date] = daily_counts.get(apt_date, 0) + 1
            
            # Distribución por prioridad
            if hasattr(apt.paciente, 'prioridad'):
                priority = apt.paciente.get_prioridad_display()
                if priority in priority_counts:
                    priority_counts[priority] += 1
            
            # Citas por hora
            hour = apt.fecha.hour
            if hour in hourly_counts:
                hourly_counts[hour] += 1
        
        # Generar todas las fechas en el rango
        current_date = start_date
        all_dates = []
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            all_dates.append(date_str)
            if date_str not in daily_counts:
                daily_counts[date_str] = 0
            current_date += timedelta(days=1)
        
        chart_data = {
            'appointments_by_day': {
                'labels': sorted(all_dates),
                'data': [daily_counts[date] for date in sorted(all_dates)]
            },
            'priority_distribution': {
                'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
                'data': [priority_counts['Urgente'], priority_counts['Alta'], priority_counts['Media'], priority_counts['Baja']],
                'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
            },
            'appointments_by_hour': {
                'labels': [f"{i}:00" for i in range(8, 19)],
                'data': [hourly_counts[i] for i in range(8, 19)]
            }
        }
    
    except Exception as e:
        # Datos vacíos en caso de error
        chart_data = {
            'appointments_by_day': {'labels': [], 'data': []},
            'priority_distribution': {
                'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
                'data': [0, 0, 0, 0],
                'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
            },
            'appointments_by_hour': {
                'labels': [f"{i}:00" for i in range(8, 19)],
                'data': [0] * 11
            }
        }
    
    return chart_data


def get_appointments_by_day_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de citas por día"""
    try:
        appointments = Appointment.objects.filter(
            doctor=doctor,
            fecha__date__range=[start_date, end_date]
        )
        
        daily_counts = {}
        current_date = start_date
        
        # Inicializar todos los días con 0
        while current_date <= end_date:
            daily_counts[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)
        
        # Contar citas por día
        for apt in appointments:
            apt_date = apt.fecha.strftime('%Y-%m-%d')
            if apt_date in daily_counts:
                daily_counts[apt_date] += 1
        
        return {
            'labels': list(daily_counts.keys()),
            'data': list(daily_counts.values()),
            'title': 'Citas por Día'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Citas por Día', 'error': 'No se pudieron cargar los datos'}


def get_priority_distribution_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de distribución por prioridad"""
    try:
        appointments = Appointment.objects.filter(
            doctor=doctor,
            fecha__date__range=[start_date, end_date]
        ).select_related('paciente')
        
        priority_counts = {'Urgente': 0, 'Alta': 0, 'Media': 0, 'Baja': 0}
        
        for apt in appointments:
            if hasattr(apt.paciente, 'prioridad'):
                priority = apt.paciente.get_prioridad_display()
                if priority in priority_counts:
                    priority_counts[priority] += 1
        
        return {
            'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
            'data': [priority_counts['Urgente'], priority_counts['Alta'], priority_counts['Media'], priority_counts['Baja']],
            'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
            'title': 'Distribución por Prioridad'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'colors': [], 'title': 'Distribución por Prioridad', 'error': 'No se pudieron cargar los datos'}


def get_patient_age_groups_chart(doctor):
    """Generar datos para gráfico de grupos de edad de pacientes"""
    try:
        patients = Patient.objects.filter(appointment__doctor=doctor).distinct()
        
        age_groups = {
            '0-18': 0,
            '19-35': 0,
            '36-50': 0,
            '51-65': 0,
            '66+': 0
        }
        
        today = timezone.now().date()
        
        for patient in patients:
            if patient.fecha_nacimiento:
                age = (today - patient.fecha_nacimiento).days // 365
                
                if age <= 18:
                    age_groups['0-18'] += 1
                elif age <= 35:
                    age_groups['19-35'] += 1
                elif age <= 50:
                    age_groups['36-50'] += 1
                elif age <= 65:
                    age_groups['51-65'] += 1
                else:
                    age_groups['66+'] += 1
        
        return {
            'labels': list(age_groups.keys()),
            'data': list(age_groups.values()),
            'title': 'Distribución por Edad de Pacientes'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Distribución por Edad', 'error': 'No se pudieron cargar los datos'}


def get_appointments_by_hour_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de citas por hora del día"""
    try:
        appointments = Appointment.objects.filter(
            doctor=doctor,
            fecha__date__range=[start_date, end_date]
        )
        
        hourly_counts = {i: 0 for i in range(8, 19)}  # 8 AM to 6 PM
        
        for apt in appointments:
            hour = apt.fecha.hour
            if hour in hourly_counts:
                hourly_counts[hour] += 1
        
        return {
            'labels': [f"{i}:00" for i in range(8, 19)],
            'data': [hourly_counts[i] for i in range(8, 19)],
            'title': 'Distribución de Citas por Hora'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Citas por Hora', 'error': 'No se pudieron cargar los datos'}
