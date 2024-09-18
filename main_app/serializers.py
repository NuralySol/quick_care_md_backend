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

    def validate_role(self, value):
        """Ensure the role is either 'admin' or 'doctor'."""
        print(f"Validating role: {value}")  # Logging the role being validated
        if value not in ['admin', 'doctor']:
            print(f"Invalid role provided: {value}")  # Log invalid role
            raise serializers.ValidationError("Invalid role. Must be either 'admin' or 'doctor'.")
        print(f"Role {value} is valid.")  # Log valid role
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        role = validated_data.pop('role')  # Role needs to be explicitly set
        print(f"Creating user with role: {role}")  # Log the role of the user being created
        user = User(username=validated_data['username'], role=role)
        user.set_password(password)
        # Automatically set is_staff=True for both admins and doctors
        if role in ['admin', 'doctor']:
            user.is_staff = True
            print(f"Setting is_staff=True for role: {role}")  # Log the staff setting
        else:
            print(f"Role {role} is not assigned staff privileges.")  # Log non-staff roles
        user.save()
        print(f"User {user.username} created successfully with role: {role}")  # Log success
        return user

# DoctorSerializer for creating doctor users
class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(write_only=True)  # This is used for input when creating a new doctor
    user_info = UserSerializer(read_only=True, source='user')  # Output for the user info

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'user_info', 'name', 'incorrect_treatments']

    def create(self, validated_data):
        # Extract user data from the validated data
        user_data = validated_data.pop('user')
        print(f"User data received for doctor creation: {user_data}")
        
        # Serialize and create the user first
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()  # Save the user object
        
        # Log user creation success
        print(f"User created: {user.username}, proceeding to create doctor")

        # Create the doctor using the user and the remaining validated data
        try:
            doctor = Doctor.objects.create(user=user, **validated_data)
            print(f"Doctor created successfully: {doctor.name} for user: {user.username}")
        except Exception as e:
            print(f"Error during doctor creation: {e}")
            raise serializers.ValidationError(f"Doctor creation failed: {e}")

        return doctor
# PatientSerializer
class PatientSerializer(serializers.ModelSerializer):
    diseases = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Disease.objects.all()
    )
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'diseases', 'doctor']

# DiseaseSerializer
class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'is_terminal']

# TreatmentSerializer
class TreatmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Treatment
        fields = ['id', 'patient', 'doctor', 'treatment_options', 'success']

# DischargeSerializer
class DischargeSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=Patient.objects.all())

    class Meta:
        model = Discharge
        fields = ['id', 'patient', 'discharge_date']

# Custom TokenObtainPairSerializer to include role in token
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role  # Add custom claim for role
        print(f"Token created with role: {user.role}")  # Log the role added to the token
        return token