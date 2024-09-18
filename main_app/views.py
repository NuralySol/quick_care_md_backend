import logging
from rest_framework import serializers, generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import PermissionDenied
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
        if not self.request.user.is_staff:
            logger.error(f"Permission denied for user: {self.request.user.username}")
            raise PermissionDenied("You must be an admin to create a doctor.")

        user_data = self.request.data.get('user')
        if user_data:
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user = user_serializer.save(role='doctor')  # Assign role 'doctor'
                serializer.save(user=user)
                logger.info(f"Doctor created successfully for user: {user.username}")
            else:
                logger.error(f"User creation failed: {user_serializer.errors}")
                raise serializers.ValidationError(user_serializer.errors)
        else:
            logger.error("No user data provided.")
            raise serializers.ValidationError('User data is required to create a doctor.')

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
        doctor = self.request.user.doctor  # Assuming a user has a related doctor profile
        serializer.save(doctor=doctor)

# Patient Detail, Update, Delete (Doctors Only)
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]  # Only doctors can manage patients

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
        doctor = self.request.user.doctor  # Assuming a user has a related doctor profile
        serializer.save(doctor=doctor)

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