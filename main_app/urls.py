# urls.py
from django.urls import path
from .views import (
    UserListView,
    UserDetailView,
    DoctorListCreateView,
    DoctorDetailView,
    PatientListCreateView,
    PatientDetailView,
    DiseaseListView,
    TreatmentListCreateView,
    TreatmentDetailView,
    DischargeListView,
    RootView,
    RegisterAdminView,
    FireDoctorView,
    TreatmentOptionsView,
    DischargePatientView,
    BulkDeleteDischargedPatientsView,
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import CustomTokenObtainPairView  # Import custom token view

urlpatterns = [
    path('', RootView.as_view(), name='root'),
    
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/register/', RegisterAdminView.as_view(), name='register_admin'),
    
    # Doctor management
    path('doctors/', DoctorListCreateView.as_view(), name='doctor-list-create'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('doctors/<int:doctor_id>/fire/', FireDoctorView.as_view(), name='fire-doctor'),

    # Patient management
    path('patients/', PatientListCreateView.as_view(), name='patient-list-create'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('patients/<int:patient_id>/discharge/', DischargePatientView.as_view(), name='discharge-patient'),

    # Disease list
    path('diseases/', DiseaseListView.as_view(), name='disease-list'),

    # Treatment management
    path('treatments/', TreatmentListCreateView.as_view(), name='treatment-list-create'),
    path('treatments/<int:pk>/', TreatmentDetailView.as_view(), name='treatment-detail'),
    path('treatments/options/', TreatmentOptionsView.as_view(), name='treatment-options'),


    # Discharge list (viewable only by admin)
    path('discharges/', DischargeListView.as_view(), name='discharge-list'),
    path('patients/discharged/purge/', BulkDeleteDischargedPatientsView.as_view(), name='purge-discharged-patients'),

    # JWT Authentication routes
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]