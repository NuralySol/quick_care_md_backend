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
    
# DiseaseSerializer for listing diseases
class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['disease_id', 'name', 'is_terminal']

# TreatmentSerializer for creating treatments for patients
class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ['treatment_id', 'patient', 'doctor', 'treatment_options', 'success']

    def create(self, validated_data):
        treatment_options = validated_data['treatment_options']
        patient = validated_data['patient']
        doctor = validated_data['doctor']

        # Logic to determine if the treatment is valid
        valid_treatments = [
            "Insulin therapy", "Lifestyle changes", "ACE inhibitors", "Bypass surgery",
            "Chemotherapy", "Radiation therapy", "Surgery", "Dialysis", "Kidney transplant",
            "Inhalers", "Steroids", "Antiviral medications", "Rest and hydration"
        ]
        success = treatment_options in valid_treatments

        treatment = Treatment.objects.create(
            patient=patient,
            doctor=doctor,
            treatment_options=treatment_options,
            success=success
        )

        if not success:
            doctor.incorrect_treatments += 1
            doctor.save()

        return treatment

# PatientSerializer for creating and managing patients
class PatientSerializer(serializers.ModelSerializer):
    # Use DiseaseSerializer to accept full disease objects
    disease = DiseaseSerializer(many=True)
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())
    treatments = TreatmentSerializer(many=True, read_only=True)  

    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'disease', 'doctor', 'treatments']

    def create(self, validated_data):
        # Extract disease data
        disease_data = validated_data.pop('disease')
        
        # Create the patient without the diseases first
        patient = Patient.objects.create(**validated_data)

        # Assign diseases by creating objects or fetching existing ones
        for disease_dict in disease_data:
            disease_obj, created = Disease.objects.get_or_create(
                disease_id=disease_dict.get('disease_id'),
                defaults={
                    'name': disease_dict.get('name'),
                    'is_terminal': disease_dict.get('is_terminal', False)
                }
            )
            patient.disease.add(disease_obj)  # Add the disease to the ManyToMany field

        return patient

    def update(self, instance, validated_data):
        # Extract and update disease data
        disease_data = validated_data.pop('disease', None)

        # Update patient details
        instance.name = validated_data.get('name', instance.name)
        instance.doctor = validated_data.get('doctor', instance.doctor)
        instance.save()

        # Update diseases if provided
        if disease_data is not None:
            instance.disease.clear()  # Clear existing diseases
            for disease_dict in disease_data:
                disease_obj, created = Disease.objects.get_or_create(
                    disease_id=disease_dict.get('disease_id'),
                    defaults={
                        'name': disease_dict.get('name'),
                        'is_terminal': disease_dict.get('is_terminal', False)
                    }
                )
                instance.disease.add(disease_obj)  

        return instance

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

# DischargeSerializer for managing patient discharges
class DischargeSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.name', read_only=True)  # Patient's name
    doctor_name = serializers.CharField(source='patient.doctor.user.username', read_only=True)  # Doctor's username

    class Meta:
        model = Discharge
        fields = ['discharge_id', 'patient_name', 'doctor_name', 'discharge_date', 'discharged']  

# Custom TokenObtainPairSerializer to include role in JWT token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['role'] = user.role
        return token