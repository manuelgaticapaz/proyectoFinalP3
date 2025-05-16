from django import forms
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['paciente', 'fecha', 'motivo', 'observaciones']  # NO doctor
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
