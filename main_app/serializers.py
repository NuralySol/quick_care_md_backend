from rest_framework import serializers
from .models import User, Doctor, Patient, Disease, Treatment, Discharge

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'name']

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'name', 'time_admitted', 'disease', 'doctor']

class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = ['id', 'name', 'is_terminal']

class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = ['id', 'patient', 'doctor', 'treatment_options', 'success']

class DischargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discharge
        fields = ['id', 'patient', 'discharged']