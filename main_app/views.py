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
    permission_classes = [permissions.IsAdminUser]  # Only admin can view all users

# View to handle retrieve, update, and delete for a specific user
class UserDetailView(generics.RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        try:
            instance.delete()  # This will call the custom delete() in your model
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT) 

# Doctor List and Creation (Admin Only)
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]  # Only admins can create doctors

    def perform_create(self, serializer):
        user_data = self.request.data.get('user')

        if not user_data:
            raise serializers.ValidationError("User data is required to create a doctor.")

        # Check if the user already exists in the User model
        user = User.objects.filter(username=user_data['username']).first()

        if user and hasattr(user, 'doctor'):
            raise serializers.ValidationError(f"Doctor already exists for user {user.username}.")

        # Proceed to create the doctor and the user if necessary
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
        # Retrieve the doctor by the user's id, not the doctor's id
        user_id = self.kwargs.get('pk')  # 'pk' is the user_id passed in the URL
        doctor = get_object_or_404(Doctor, user_id=user_id)
        return doctor

# Patient List and Creation (Doctors Only)
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can create patients

    def perform_create(self, serializer):
        doctor = self.request.user.doctor
        logger.info(f"Doctor {doctor.user.username} is attempting to create a new patient.")

        # Hardcoded diseases instead of fetching from the database
        available_diseases = [
            {'disease_id': 1, 'name': 'Diabetes', 'is_terminal': False},
            {'disease_id': 2, 'name': 'Hypertension', 'is_terminal': False},
            {'disease_id': 3, 'name': 'Heart Disease', 'is_terminal': False},
            {'disease_id': 4, 'name': 'Cancer', 'is_terminal': True},
            {'disease_id': 5, 'name': 'Chronic Kidney Disease', 'is_terminal': True},
            {'disease_id': 6, 'name': 'Asthma', 'is_terminal': False},
            {'disease_id': 7, 'name': 'COVID-19', 'is_terminal': False},
            {'disease_id': 8, 'name': 'Influenza', 'is_terminal': False}
        ]

        # Save diseases to the database if they do not already exist
        for disease_data in available_diseases:
            Disease.objects.get_or_create(disease_id=disease_data['disease_id'], defaults={
                'name': disease_data['name'],
                'is_terminal': disease_data['is_terminal']
            })

        # Randomly assign 1-3 diseases to the patient
        num_diseases = random.randint(1, 3)
        random_diseases = random.sample(available_diseases, num_diseases)
        logger.info(f"Random diseases assigned: {[d['name'] for d in random_diseases]}")

        # Create the patient without diseases first
        patient = serializer.save(doctor=doctor)

        # Fetch the diseases from the database and assign them to the patient
        disease_instances = Disease.objects.filter(disease_id__in=[d['disease_id'] for d in random_diseases])
        patient.disease.set(disease_instances)

        logger.info(f"Patient {patient.name} created successfully with doctor {doctor.user.username}.")

        # Hardcoded treatments for each disease
        for disease in disease_instances:
            treatment_success = random.choice([True, False])
            Treatment.objects.create(
                patient=patient,
                doctor=doctor,
                treatment_options=random.choice([
                    "Insulin therapy, Lifestyle changes",
                    "ACE inhibitors, Lifestyle changes",
                    "Medication, Bypass surgery, Lifestyle changes",
                    "Chemotherapy, Radiation therapy, Surgery",
                    "Dialysis, Kidney transplant",
                    "Inhalers, Steroids, Avoiding triggers",
                    "Supportive care, Antiviral medications",
                    "Antiviral drugs, Rest and hydration"
                ]),
                success=treatment_success
            )
            logger.info(f"Assigned treatment for {disease.name}, success: {treatment_success}")
        
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
        doctor = self.request.user.doctor  # Assuming the user has a related doctor profile
        patient_id = self.request.data.get('patient')

        # Fetch the patient to ensure the treatment is for the correct disease
        patient = get_object_or_404(Patient, id=patient_id)

        # Fetch the disease(s) associated with the patient
        diseases = patient.disease.all()
        if not diseases:
            raise serializers.ValidationError("No diseases associated with the patient.")

        # Validate the treatment against the patient's diseases
        treatment_name = self.request.data.get('treatment_options')
        valid_treatments = [
            {"treatment_id": 1, "treatment_options": "Insulin therapy, Lifestyle changes"},
            {"treatment_id": 2, "treatment_options": "ACE inhibitors, Lifestyle changes"},
            {"treatment_id": 3, "treatment_options": "Medication, Bypass surgery, Lifestyle changes"},
            {"treatment_id": 4, "treatment_options": "Chemotherapy, Radiation therapy, Surgery"},
            {"treatment_id": 5, "treatment_options": "Dialysis, Kidney transplant"},
            {"treatment_id": 6, "treatment_options": "Inhalers, Steroids, Avoiding triggers"},
            {"treatment_id": 7, "treatment_options": "Supportive care, Antiviral medications"},
            {"treatment_id": 8, "treatment_options": "Antiviral drugs, Rest and hydration"}
        ]

        if treatment_name not in valid_treatments:
            doctor.incorrect_treatments += 1
            doctor.save()

            # Deactivate the doctor after 3 incorrect treatments
            if doctor.incorrect_treatments >= 3:
                doctor.is_active = False
                doctor.save()
                logger.info(f"Doctor {doctor.user.username} has been deactivated due to multiple incorrect treatments.")
                raise serializers.ValidationError("Doctor has been deactivated due to multiple incorrect treatments.")

            raise serializers.ValidationError(f"{treatment_name} is not a valid treatment.")

        # Reset incorrect treatments if the treatment is valid
        doctor.incorrect_treatments = 0
        doctor.save()

        # Save the treatment
        serializer.save(doctor=doctor, patient=patient)

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