# This is for the admin panel. It allows the admin to view and edit the models in the admin panel.

from django.contrib import admin
from .models import User, Doctor, Patient, Disease, Treatment, Discharge

# Register the User model
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active')
    search_fields = ('username', 'email')

# Register the Doctor model 
@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'incorrect_treatments')
    search_fields = ('name', 'user__username')

# Register the Patient model
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'doctor', 'time_admitted')
    search_fields = ('name', 'doctor__name')

# Register the Disease model
@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_terminal')
    search_fields = ('name',)

# Register the Treatment model
@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'treatment_options', 'success')
    search_fields = ('patient__name', 'doctor__name')

# Register the Discharge model
@admin.register(Discharge)
class DischargeAdmin(admin.ModelAdmin):
    list_display = ('patient', 'discharged')
    search_fields = ('patient__name',)