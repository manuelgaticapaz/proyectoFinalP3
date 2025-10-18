from django import forms
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import Appointment
from patients.models import Patient

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['paciente', 'fecha', 'motivo', 'observaciones']
        widgets = {
            'fecha': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'required': True
                }
            ),
            'paciente': forms.Select(
                attrs={
                    'class': 'form-select',
                    'required': True
                }
            ),
            'motivo': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Describa el motivo de la consulta médica...',
                    'required': True
                }
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Observaciones adicionales (opcional)...'
                }
            ),
        }
        labels = {
            'paciente': 'Seleccionar Paciente',
            'fecha': 'Fecha y Hora de la Cita',
            'motivo': 'Motivo de la Consulta',
            'observaciones': 'Observaciones Adicionales'
        }

    def __init__(self, *args, **kwargs):
        self.doctor = kwargs.pop('doctor', None)
        super().__init__(*args, **kwargs)
        
        # Set minimum datetime to current time
        now = timezone.now()
        min_datetime = now.strftime('%Y-%m-%dT%H:%M')
        self.fields['fecha'].widget.attrs['min'] = min_datetime
        
        # Filter patients if doctor is provided
        if self.doctor:
            # Get patients that have had appointments with this doctor
            self.fields['paciente'].queryset = Patient.objects.filter(
                appointment__doctor=self.doctor
            ).distinct().order_by('nombre', 'apellidos')
        else:
            self.fields['paciente'].queryset = Patient.objects.all().order_by('nombre', 'apellidos')

    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        
        if fecha:
            # Check if the appointment is in the past
            if fecha < timezone.now():
                raise forms.ValidationError(
                    "No se pueden crear citas en el pasado. Por favor seleccione una fecha y hora futura."
                )
            
            # Check if the appointment is too far in the future (e.g., more than 1 year)
            max_future_date = timezone.now() + timedelta(days=365)
            if fecha > max_future_date:
                raise forms.ValidationError(
                    "No se pueden crear citas con más de un año de anticipación."
                )
            
            # Check business hours (8 AM to 6 PM)
            if fecha.hour < 8 or fecha.hour >= 18:
                raise forms.ValidationError(
                    "Las citas solo pueden agendarse entre las 8:00 AM y las 6:00 PM."
                )
            
            # Check if it's a weekend
            if fecha.weekday() >= 5:  # Saturday = 5, Sunday = 6
                raise forms.ValidationError(
                    "Las citas solo pueden agendarse de lunes a viernes."
                )
            
            # Check for appointment conflicts if doctor is provided
            if self.doctor:
                # Check for existing appointments within 30 minutes
                start_time = fecha - timedelta(minutes=15)
                end_time = fecha + timedelta(minutes=15)
                
                conflicting_appointments = Appointment.objects.filter(
                    doctor=self.doctor,
                    fecha__range=[start_time, end_time]
                )
                
                # Exclude current appointment if editing
                if self.instance and self.instance.pk:
                    conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)
                
                if conflicting_appointments.exists():
                    raise forms.ValidationError(
                        f"Ya existe una cita programada cerca de esta hora. "
                        f"Por favor seleccione otro horario."
                    )
        
        return fecha

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo')
        
        if motivo:
            # Minimum length validation
            if len(motivo.strip()) < 10:
                raise forms.ValidationError(
                    "El motivo debe tener al menos 10 caracteres para ser descriptivo."
                )
            
            # Maximum length validation
            if len(motivo) > 500:
                raise forms.ValidationError(
                    "El motivo no puede exceder los 500 caracteres."
                )
        
        return motivo.strip() if motivo else motivo

    def clean_observaciones(self):
        observaciones = self.cleaned_data.get('observaciones')
        
        if observaciones:
            # Maximum length validation
            if len(observaciones) > 1000:
                raise forms.ValidationError(
                    "Las observaciones no pueden exceder los 1000 caracteres."
                )
            
            return observaciones.strip()
        
        return observaciones
