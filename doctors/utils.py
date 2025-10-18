"""
Utility functions for doctors app optimization and data processing
"""
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from appointments.models import Appointment
from patients.models import Patient


def get_doctor_statistics(doctor):
    """
    Get comprehensive statistics for a doctor
    """
    today = timezone.now().date()
    
    stats = {
        'total_appointments': Appointment.objects.filter(doctor=doctor).count(),
        'today_appointments': Appointment.objects.filter(
            doctor=doctor, 
            fecha__date=today
        ).count(),
        'week_appointments': Appointment.objects.filter(
            doctor=doctor,
            fecha__date__gte=today,
            fecha__date__lt=today + timedelta(days=7)
        ).count(),
        'month_appointments': Appointment.objects.filter(
            doctor=doctor,
            fecha__date__gte=today.replace(day=1),
            fecha__date__lt=(today.replace(day=1) + timedelta(days=32)).replace(day=1)
        ).count(),
        'total_patients': Patient.objects.filter(
            appointment__doctor=doctor
        ).distinct().count(),
        'priority_breakdown': get_priority_breakdown(doctor),
        'upcoming_appointments': get_upcoming_appointments(doctor, limit=5),
        'recent_patients': get_recent_patients(doctor, limit=5)
    }
    
    return stats


def get_priority_breakdown(doctor):
    """
    Get breakdown of appointments by patient priority
    """
    priorities = Patient.objects.filter(
        appointment__doctor=doctor
    ).values('prioridad').annotate(
        count=Count('appointment')
    ).order_by('-count')
    
    return {priority['prioridad']: priority['count'] for priority in priorities}


def get_upcoming_appointments(doctor, limit=10):
    """
    Get upcoming appointments for a doctor
    """
    today = timezone.now()
    return Appointment.objects.filter(
        doctor=doctor,
        fecha__gte=today
    ).select_related('paciente').order_by('fecha')[:limit]


def get_recent_patients(doctor, limit=10):
    """
    Get recently seen patients
    """
    return Patient.objects.filter(
        appointment__doctor=doctor
    ).annotate(
        last_appointment=Count('appointment')
    ).order_by('-last_appointment')[:limit]


def optimize_appointments_query(doctor, start_date=None, end_date=None):
    """
    Optimized query for appointments with proper select_related and prefetch_related
    """
    queryset = Appointment.objects.filter(doctor=doctor)
    
    if start_date:
        queryset = queryset.filter(fecha__gte=start_date)
    if end_date:
        queryset = queryset.filter(fecha__lte=end_date)
    
    return queryset.select_related('paciente', 'doctor').order_by('fecha')


def get_appointment_conflicts(doctor, fecha_inicio, fecha_fin):
    """
    Check for appointment conflicts in a given time range
    """
    return Appointment.objects.filter(
        doctor=doctor,
        fecha__range=[fecha_inicio, fecha_fin]
    ).exists()


def format_appointment_duration(appointment):
    """
    Calculate and format appointment duration
    """
    # Assuming appointments are 30 minutes by default
    # You can modify this based on your appointment model
    duration = timedelta(minutes=30)
    end_time = appointment.fecha + duration
    return {
        'start': appointment.fecha,
        'end': end_time,
        'duration_minutes': 30
    }


def get_doctor_workload(doctor, date_range_days=7):
    """
    Calculate doctor's workload for the next N days
    """
    today = timezone.now().date()
    end_date = today + timedelta(days=date_range_days)
    
    appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__gte=today,
        fecha__date__lte=end_date
    ).values('fecha__date').annotate(
        daily_count=Count('id')
    ).order_by('fecha__date')
    
    workload = {}
    for appointment in appointments:
        date_str = appointment['fecha__date'].strftime('%Y-%m-%d')
        workload[date_str] = appointment['daily_count']
    
    return workload


def suggest_optimal_appointment_time(doctor, preferred_date):
    """
    Suggest optimal appointment times based on doctor's schedule
    """
    existing_appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date=preferred_date
    ).values_list('fecha__time', flat=True)
    
    # Define working hours (9 AM to 5 PM)
    working_hours = []
    for hour in range(9, 17):
        for minute in [0, 30]:  # 30-minute slots
            time_slot = datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").time()
            if time_slot not in existing_appointments:
                working_hours.append(time_slot)
    
    return working_hours[:5]  # Return first 5 available slots


def generate_appointment_report(doctor, start_date, end_date):
    """
    Generate a comprehensive appointment report for a doctor
    """
    appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date__gte=start_date,
        fecha__date__lte=end_date
    ).select_related('paciente')
    
    report = {
        'period': f"{start_date} to {end_date}",
        'total_appointments': appointments.count(),
        'appointments_by_day': {},
        'appointments_by_priority': {},
        'most_common_reasons': [],
        'patient_demographics': {}
    }
    
    # Group by day
    for appointment in appointments:
        day = appointment.fecha.date()
        if day not in report['appointments_by_day']:
            report['appointments_by_day'][day] = 0
        report['appointments_by_day'][day] += 1
    
    # Group by priority
    for appointment in appointments:
        priority = appointment.paciente.get_prioridad_display()
        if priority not in report['appointments_by_priority']:
            report['appointments_by_priority'][priority] = 0
        report['appointments_by_priority'][priority] += 1
    
    return report


def cache_doctor_data(doctor):
    """
    Cache frequently accessed doctor data for performance optimization
    """
    from django.core.cache import cache
    
    cache_key = f"doctor_stats_{doctor.id}"
    stats = get_doctor_statistics(doctor)
    
    # Cache for 1 hour
    cache.set(cache_key, stats, 3600)
    return stats


def get_cached_doctor_data(doctor):
    """
    Retrieve cached doctor data or generate if not available
    """
    from django.core.cache import cache
    
    cache_key = f"doctor_stats_{doctor.id}"
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = cache_doctor_data(doctor)
    
    return stats


def get_appointment_conflicts(doctor, start_time, end_time):
    """
    Check for appointment conflicts in a given time range
    """
    return Appointment.objects.filter(
        doctor=doctor,
        fecha__range=[start_time, end_time]
    )


def suggest_optimal_appointment_time(doctor, date):
    """
    Suggest optimal appointment times for a given date
    """
    # Business hours: 8 AM to 6 PM
    business_start = 8
    business_end = 18
    
    # Get existing appointments for the date
    existing_appointments = Appointment.objects.filter(
        doctor=doctor,
        fecha__date=date
    ).values_list('fecha__hour', flat=True)
    
    suggestions = []
    for hour in range(business_start, business_end):
        if hour not in existing_appointments:
            # Create datetime for suggestion
            suggested_time = timezone.datetime.combine(date, timezone.datetime.min.time().replace(hour=hour))
            suggestions.append({
                'time': suggested_time,
                'display': f"{hour:02d}:00"
            })
    
    return suggestions[:5]  # Return first 5 suggestions
