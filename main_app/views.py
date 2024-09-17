from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
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
from .permissions import IsAdminUserOrReadOnly, IsDoctorUser

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
    serializer_class = UserSerializer  # Use the UserSerializer to serialize the data

# View to handle retrieve, update, and delete for a specific user
class UserDetailView(generics.RetrieveDestroyAPIView):  # You can also add UpdateAPIView if you want to allow updates
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'  # This will match the <int:pk> in your URL

# Doctor List and Creation (Admin Only)
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)  # Associate doctor with the logged-in user

# Doctor Detail, Update, Delete (Admin Only)
class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

# Patient List and Creation (Doctors Only)
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor  # Assuming a user has a related doctor profile
        serializer.save(doctor=doctor)

# Patient Detail, Update, Delete (Doctors Only)
class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

# Disease List (Admin and Doctors)
class DiseaseListView(generics.ListAPIView):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [permissions.IsAuthenticated]

# Treatment List and Creation (Doctors Only)
class TreatmentListCreateView(generics.ListCreateAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor  # Assuming a user has a related doctor profile
        serializer.save(doctor=doctor)

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