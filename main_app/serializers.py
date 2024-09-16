from rest_framework import serializers
from .models import User, Doctor, Patient, Disease, Treatment, Discharge
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Custom JWT Token Serializer to add custom claimsclass CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        if user.is_superuser:
            token['role'] = 'superuser'  # Explicitly label superusers
        else:
            token['role'] = user.role  # Assume 'role' exists for non-superusers

        token['is_superuser'] = user.is_superuser
        token['is_active'] = user.is_active

        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Ensure that the password is properly hashed when creating the user
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

# Doctor Serializer
class DoctorSerializer(serializers.ModelSerializer):
    # Include nested user information in the doctor serializer
    user = UserSerializer(read_only=True)  # This will include user's information

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'name']

# Patient Serializer
class PatientSerializer(serializers.ModelSerializer):
    # Nested doctor serializer to include doctor information with each patient
    doctor = DoctorSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'disease', 'doctor']

# Disease Serializer
class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'is_terminal']

# Treatment Serializer
class TreatmentSerializer(serializers.ModelSerializer):
    # Include nested patient and doctor information
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)

    class Meta:
        model = Treatment
        fields = ['id', 'patient', 'doctor', 'treatment_options', 'success']

# Discharge Serializer
class DischargeSerializer(serializers.ModelSerializer):
    # Include nested patient information
    patient = PatientSerializer(read_only=True)

    class Meta:
        model = Discharge
        fields = ['id', 'patient', 'discharged']