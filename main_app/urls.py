from django.urls import path
from .views import (
    DoctorListCreateView,
    DoctorDetailView,
    PatientListCreateView,
    PatientDetailView,
    DiseaseListView,
    TreatmentListCreateView,
    TreatmentDetailView,
    DischargeListView,
    DoctorLoginView,
    RootView,
)

urlpatterns = [
    path('', RootView.as_view(), name='root'),
    
    # Doctor management
    path('doctors/', DoctorListCreateView.as_view(), name='doctor-list-create'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),

    # Patient management
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),

    # Disease list
    path('diseases/', DiseaseListView.as_view(), name='disease-list'),

    # Treatment management
    path('treatments/', TreatmentListCreateView.as_view(), name='treatment-list-create'),
    path('treatments/<int:pk>/', TreatmentDetailView.as_view(), name='treatment-detail'),

    # Discharge list (viewable only by admin)
    path('discharges/', DischargeListView.as_view(), name='discharge-list'),

    # Doctor login
    path('doctors/login/', DoctorLoginView.as_view(), name='doctor-login'),
]