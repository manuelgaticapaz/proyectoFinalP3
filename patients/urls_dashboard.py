from django.urls import path
from .views_dashboard import (
    patient_dashboard,
    create_patient,
    edit_patient,
    patient_detail,
    patient_search_ajax
)

urlpatterns = [
    path('dashboard/', patient_dashboard, name='patient_dashboard'),
    path('create/', create_patient, name='create_patient'),
    path('edit/<int:patient_id>/', edit_patient, name='edit_patient'),
    path('detail/<int:patient_id>/', patient_detail, name='patient_detail'),
    path('search-ajax/', patient_search_ajax, name='patient_search_ajax'),
]
