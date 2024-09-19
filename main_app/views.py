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
    queryset = User.objects.all()  # Fetch all users
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admin can view all users

# View to handle retrieve, update, and delete for a specific user
class UserDetailView(generics.RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'  # This will match the <int:pk> in your URL
    permission_classes = [permissions.IsAdminUser] 

# Doctor List and Creation (Admin Only)
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can create doctors

    def perform_create(self, serializer):
        logger.debug(f"User attempting to create doctor: {self.request.user.username}")

        # Check if the requesting user is staff/admin
        if not self.request.user.is_staff:
            logger.error(f"Permission denied for user: {self.request.user.username}")
            raise PermissionDenied("You must be an admin to create a doctor.")

        # Extract user data from the request
        user_data = self.request.data.get('user')
        if not user_data:
            logger.error("No user data provided.")
            raise serializers.ValidationError('User data is required to create a doctor.')

        # Create the user first
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save(role='doctor')  # Assign role 'doctor'
            logger.info(f"User {user.username} created successfully.")

            # Now proceed to create the doctor with the created user
            try:
                logger.debug(f"Attempting to create doctor with user {user.username} and name {self.request.data.get('name')}")
                serializer.save(user=user)
                logger.info(f"Doctor created successfully for user: {user.username}")
            except Exception as e:
                logger.error(f"Failed to create doctor: {str(e)}")
                raise serializers.ValidationError(f"Failed to create doctor: {str(e)}")

        else:
            logger.error(f"User creation failed: {user_serializer.errors}")
            raise serializers.ValidationError(user_serializer.errors)

# Doctor Detail, Update, Delete (Admin Only)
class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

# Patient List and Creation (Doctors Only)
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can create patients

    def perform_create(self, serializer):
        # Get the logged-in doctor
        doctor = self.request.user.doctor

        # Randomly assign a disease to the patient
        diseases = Disease.objects.all()
        if diseases.exists():
            random_disease = random.choice(diseases)
        else:
            raise serializers.ValidationError("No diseases available to assign.")

        # Save the patient with the assigned disease and the doctor who created them
        serializer.save(doctor=doctor, disease=random_disease)
        
# Patient Detail, Update, Delete (Doctors Only)
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can access this view

    def get_queryset(self):
        # Filter patients so doctors only see their assigned patients
        return Patient.objects.filter(doctor=self.request.user.doctor)

class TreatmentListCreateView(generics.ListCreateAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        # Ensure only the doctor assigned to the patient can create treatments
        patient_id = self.request.data.get('patient')
        patient = get_object_or_404(Patient, id=patient_id, doctor=self.request.user.doctor)
        serializer.save(doctor=self.request.user.doctor, patient=patient)

# Disease List (Admin and Doctors)
class DiseaseListView(generics.ListAPIView):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [permissions.IsAuthenticated]  # Both admins and doctors can view diseases

# Treatment List and Creation (Doctors Only)
class TreatmentListCreateView(generics.ListCreateAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can manage treatments

    def perform_create(self, serializer):
        doctor = self.request.user.doctor  # Assuming the user has a related doctor profile
        patient_id = self.request.data.get('patient')

        # Fetch the patient to ensure the treatment is for the correct disease
        patient = get_object_or_404(Patient, id=patient_id)

        # Only allow treatments for the patient's disease
        disease_treatments = patient.disease.treatments.all()
        treatment_name = self.request.data.get('name')

        # Check if the selected treatment is valid for the disease
        if treatment_name not in [t.name for t in disease_treatments]:
            doctor.incorrect_treatments += 1
            doctor.save()

            # Deactivate the doctor after 3 incorrect treatments
            if doctor.incorrect_treatments >= 3:
                doctor.is_active = False
                doctor.save()
                logger.info(f"Doctor {doctor.user.username} has been deactivated due to multiple incorrect treatments.")
                raise serializers.ValidationError("Doctor has been deactivated due to multiple incorrect treatments.")

            raise serializers.ValidationError(f"{treatment_name} is not a valid treatment for {patient.disease.name}")

        # Reset incorrect treatments if correct
        doctor.incorrect_treatments = 0
        doctor.save()

        # Save the treatment
        serializer.save(doctor=doctor, patient=patient)

# Treatment Detail, Update, Delete (Doctors Only)
class TreatmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can update/delete treatments

# Discharge List (Admin Only)
class DischargeListView(generics.ListAPIView):
    queryset = Discharge.objects.all()
    serializer_class = DischargeSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can view discharges

# Discharge a patient (Doctors Only)
class DischargePatientView(APIView):
    permission_classes = [IsDoctorUser]

    def post(self, request, patient_id):
        patient = get_object_or_404(Patient, id=patient_id)

        # Create discharge record
        discharge = Discharge.objects.create(patient=patient, doctor=request.user.doctor)
        patient.is_active = False  # Mark the patient as discharged
        patient.save()

        return Response({
            "message": f"Patient {patient.name} has been successfully discharged.",
            "discharge": DischargeSerializer(discharge).data
        })