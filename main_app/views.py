import logging
from rest_framework import serializers, generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView  
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Doctor, Patient, Disease, Treatment, Discharge, User
from .serializers import (
    DoctorSerializer,
    PatientSerializer,
    DiseaseSerializer,
    TreatmentSerializer,
    DischargeSerializer,
    CustomTokenObtainPairSerializer,
    UserSerializer,
)
from .permissions import IsAdminUserOrReadOnly, IsDoctorUser, IsAdminWithRole
import random

# Set up logger
logger = logging.getLogger(__name__)

# Root API view
class RootView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to Quick Care MD API. Please use the appropriate endpoints."})

# Custom JWT login view to include roles and other claims
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Admin Registration View
class RegisterAdminView(APIView):
    def post(self, request):
        request.data['role'] = 'admin'  # Automatically assign role as 'admin'
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# User List (Admin Only)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

# View to handle retrieve, update, and delete for a specific user
class UserDetailView(generics.RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

# Doctor List and Creation (Admin Only)
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        user_data = self.request.data.get('user')
        if not user_data:
            raise serializers.ValidationError("User data is required to create a doctor.")

        user = User.objects.filter(username=user_data['username']).first()

        if user and hasattr(user, 'doctor'):
            raise serializers.ValidationError(f"Doctor already exists for user {user.username}.")

        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save(role='doctor')
            serializer.save(user=user)
        else:
            raise serializers.ValidationError(user_serializer.errors)

# Doctor Detail, Update, Delete (Admin Only)
class DoctorDetailView(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        user_id = self.kwargs.get('pk')  # 'pk' is the user_id passed in the URL
        doctor = get_object_or_404(Doctor, user_id=user_id)
        return doctor

# Patient List and Creation (Doctors Only)
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor
        logger.info(f"Doctor {doctor.user.username} is attempting to create a new patient.")

        available_diseases = Disease.objects.all()

        # Randomly assign 1-3 diseases to the patient
        num_diseases = random.randint(1, 3)
        random_diseases = random.sample(list(available_diseases), num_diseases)

        patient = serializer.save(doctor=doctor)

        # Assign diseases to the patient
        patient.disease.set(random_diseases)

        # Create treatments for the assigned diseases
        self.create_treatments_for_diseases(patient, doctor, random_diseases)

    def create_treatments_for_diseases(self, patient, doctor, diseases):
        """ Helper method to create treatments for each disease the patient has """
        valid_treatments = {
            "Diabetes": "Insulin therapy, Lifestyle changes",
            "Hypertension": "ACE inhibitors, Lifestyle changes",
            "Heart Disease": "Medication, Bypass surgery, Lifestyle changes",
            "Cancer": "Chemotherapy, Radiation therapy, Surgery",
            "Chronic Kidney Disease": "Dialysis, Kidney transplant",
            "Asthma": "Inhalers, Steroids, Avoiding triggers",
            "COVID-19": "Supportive care, Antiviral medications",
            "Influenza": "Antiviral drugs, Rest and hydration"
        }

        for disease in diseases:
            treatment_option = valid_treatments.get(disease.name, "")
            success = random.choice([True, False])

            Treatment.objects.create(
                patient=patient,
                doctor=doctor,
                treatment_options=treatment_option,
                success=success
            )

            logger.info(f"Assigned treatment for {disease.name}: {treatment_option}, success: {success}")

# Patient Detail, Update, Delete (Doctors Only)
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

    def get_queryset(self):
        return Patient.objects.filter(doctor=self.request.user.doctor)

# Treatment List and Creation (Doctors Only)
class TreatmentListCreateView(generics.ListCreateAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor
        patient = serializer.validated_data['patient']

        diseases = patient.disease.all()
        treatment_options = serializer.validated_data['treatment_options']

        valid_treatments = [
            "Insulin therapy, Lifestyle changes",
            "ACE inhibitors, Lifestyle changes",
            "Medication, Bypass surgery, Lifestyle changes",
            "Chemotherapy, Radiation therapy, Surgery",
            "Dialysis, Kidney transplant",
            "Inhalers, Steroids, Avoiding triggers",
            "Supportive care, Antiviral medications",
            "Antiviral drugs, Rest and hydration"
        ]

        if treatment_options not in valid_treatments:
            raise serializers.ValidationError(f"{treatment_options} is not valid for the patient's disease.")

        serializer.save(doctor=doctor)

# Disease List (Admin and Doctors)
class DiseaseListView(generics.ListAPIView):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [permissions.IsAuthenticated]

# Treatment Detail, Update, Delete (Doctors Only)
class TreatmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]

# Discharge List (Admin Only)
class DischargeListView(generics.ListAPIView):
    queryset = Discharge.objects.all()
    serializer_class = DischargeSerializer
    permission_classes = [permissions.IsAdminUser]

# Discharge a patient (Doctors Only)
class DischargePatientView(APIView):
    permission_classes = [IsDoctorUser]

    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)
        discharge = Discharge.objects.create(patient=patient, doctor=request.user.doctor)
        patient.is_active = False
        patient.save()

        return Response({
            "message": f"Patient {patient.name} has been successfully discharged.",
            "discharge": DischargeSerializer(discharge).data
        })