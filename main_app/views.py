from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Doctor, Patient, Disease, Treatment, Discharge
from .serializers import (
    DoctorSerializer,
    PatientSerializer,
    DiseaseSerializer,
    TreatmentSerializer,
    DischargeSerializer,
)
from .permissions import IsAdminUserOrReadOnly, IsDoctorUser

# Doctor List and Creation (Admin Only)
class DoctorListCreateView(generics.ListCreateAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save()

# Doctor Detail, Update, Delete (Admin Only)
class DoctorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]

# Doctor Login (JWT Authentication)
class DoctorLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user and user.is_doctor:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': DoctorSerializer(user.doctor).data  # assuming a doctor is linked to the user
            })
        return Response({'error': 'Invalid credentials or not a doctor'}, status=status.HTTP_401_UNAUTHORIZED)

# Patient List and Creation (Doctors Only)
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor  # Assume user is a doctor
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
    permission_classes = [permissions.IsAuthenticated]  # Accessible to both doctors and admin

# Treatment List and Creation (Doctors Only)
class TreatmentListCreateView(generics.ListCreateAPIView):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [IsDoctorUser]

    def perform_create(self, serializer):
        doctor = self.request.user.doctor  # Assume user is a doctor
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