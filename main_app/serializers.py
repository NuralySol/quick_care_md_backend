from rest_framework import serializers
from .models import User, Doctor, Patient, Disease, Treatment, Discharge
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# UserSerializer for general user creation (e.g., admin, doctor)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role')
        user = User(username=validated_data['username'], role=role)
        user.set_password(password)
        if role in ['admin', 'doctor']:
            user.is_staff = True
        user.save()

        # Create a Doctor instance when the role is 'doctor'
        if role == 'doctor':
            Doctor.objects.create(user=user, name=user.username)

        return user


# PatientSerializer for creating and managing patients
class PatientSerializer(serializers.ModelSerializer):
    disease = serializers.PrimaryKeyRelatedField(many=True, queryset=Disease.objects.all())  # ManyToMany field

    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'disease', 'doctor']

    def create(self, validated_data):
        disease_data = validated_data.pop('disease', [])
        if not disease_data:
            raise serializers.ValidationError("No valid diseases selected for the patient.")
        
        # Create the patient without diseases first
        patient = Patient.objects.create(**validated_data)
        
        # Assign diseases after creation
        patient.disease.set(disease_data)
        
        return patient


# DoctorSerializer for creating doctor users
class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    patients = PatientSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'user', 'incorrect_treatments', 'patients']

    def create(self, validated_data):
        # Extract user data from the nested serializer
        user_data = validated_data.pop('user')
        password = user_data.pop('password')  # Handle password separately

        # Check if the user with the given username already exists
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={'role': 'doctor', **user_data}  # Set defaults for new users
        )
        if created:
            # If the user is newly created, set the password
            user.set_password(password)
            user.save()

        # If user already exists but isn't a doctor, raise a validation error
        elif user.role != 'doctor':
            raise serializers.ValidationError("User already exists but isn't a doctor.")

        # Create the doctor profile and associate it with the user
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor


# DiseaseSerializer for listing diseases
class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['disease_id', 'name', 'is_terminal']


# TreatmentSerializer for creating treatments for patients
class TreatmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Treatment
        fields = ['treatment_id', 'patient', 'doctor', 'treatment_options', 'success']

    def validate(self, data):
        """Ensure the treatment is applicable to the patient's disease."""
        patient = data['patient']
        treatment_options = data['treatment_options']

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
        
        return data


# DischargeSerializer for managing patient discharges
class DischargeSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())

    class Meta:
        model = Discharge
        fields = ['discharge_id', 'patient', 'discharge_date']


# Custom TokenObtainPairSerializer to include role in JWT token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        return token