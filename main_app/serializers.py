from rest_framework import serializers
from .models import User, Doctor, Patient, Disease, Treatment, Discharge
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# UserSerializer for general user creation (e.g., admin, doctor)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},  # Password should not be exposed in the API
            'role': {'required': True},  # Ensure role is required
        }

    def validate_password(self, value):
        """Ensure the password meets security requirements."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def validate_role(self, value):
        """Ensure the role is either 'admin' or 'doctor'."""
        if value not in ['admin', 'doctor']:
            raise serializers.ValidationError("Invalid role. Must be either 'admin' or 'doctor'.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role')
        user = User(username=validated_data['username'], role=role)
        user.set_password(password)
        if role in ['admin', 'doctor']:
            user.is_staff = True
        user.save()
        return user

# DoctorSerializer for creating doctor users
class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(write_only=True)  # This allows the user data to be provided during doctor creation

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'name', 'incorrect_treatments']

    def create(self, validated_data):
        # Extract user data and create the user first
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        # Create the doctor with the newly created user
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor

# PatientSerializer for creating and managing patients
class PatientSerializer(serializers.ModelSerializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    diseases = serializers.PrimaryKeyRelatedField(many=True, queryset=Disease.objects.all())

    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'diseases', 'doctor']

# DiseaseSerializer for listing diseases
class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'is_terminal']

# TreatmentSerializer for creating treatments for patients
class TreatmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Treatment
        fields = ['id', 'patient', 'doctor', 'treatment_options', 'success']

    def validate(self, data):
        """Ensure the treatment is applicable to the patient's disease."""
        patient = data['patient']
        treatment_options = data['treatment_options']
        applicable_treatments = [t.name for t in patient.disease.treatments.all()]
        
        if treatment_options not in applicable_treatments:
            raise serializers.ValidationError(f"{treatment_options} is not valid for the patient's disease.")
        
        return data

# DischargeSerializer for managing patient discharges
class DischargeSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())

    class Meta:
        model = Discharge
        fields = ['id', 'patient', 'discharge_date']

# Custom TokenObtainPairSerializer to include role in JWT token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        return token