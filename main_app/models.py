from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# Custom user model for both doctors and hospital admin
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  
        blank=True
    )

    # Override save method to create a Doctor if role is doctor
    def save(self, *args, **kwargs):
        is_new_doctor = self.pk is None and self.role == 'doctor'
        super(User, self).save(*args, **kwargs)  # Save the user first
    
        # Automatically create a Doctor if the role is doctor and there's no associated doctor
        if self.role == 'doctor' and not hasattr(self, 'doctor'):
            Doctor.objects.create(user=self, name=self.username)

        # Handle role update from non-doctor to doctor
        if self.role == 'doctor' and not is_new_doctor and not hasattr(self, 'doctor'):
            Doctor.objects.create(user=self, name=self.username)

    def delete(self, *args, **kwargs):
        if self.role == 'admin':
            if Doctor.objects.exists() or Patient.objects.exists():
                raise ValidationError("Cannot delete admin while doctors or patients exist. Please reassign or remove them before proceeding.")
        super(User, self).delete(*args, **kwargs)


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    incorrect_treatments = models.IntegerField(default=0)  # Track incorrect treatments

    def __str__(self):
        return self.name

    def fire(self):
        """Deactivate the doctor instead of deleting them"""
        if self.incorrect_treatments >= 3:
            self.user.is_active = False  # Deactivate the user account instead of deleting
            self.user.save()

    def delete(self, *args, **kwargs):
        # Prevent deletion if doctor is assigned to any active patients
        if Patient.objects.filter(doctor=self).exists():
            raise ValidationError("Cannot delete a doctor while they have active patients.")
        super(Doctor, self).delete(*args, **kwargs)


class Patient(models.Model):
    name = models.CharField(max_length=100)
    time_admitted = models.DateTimeField(auto_now_add=True)
    disease = models.ManyToManyField('Disease')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patients')  # Add related_name

    def __str__(self):
        return self.name


class Disease(models.Model):
    disease_id = models.AutoField(primary_key=True)  # Use auto-increment for disease ID
    name = models.CharField(max_length=100)
    is_terminal = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Treatment(models.Model):
    treatment_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    treatment_options = models.TextField()
    success = models.BooleanField(default=False)  # Field to track whether the treatment is correct

    def __str__(self):
        return f"{self.patient.name} - {self.treatment_options}"

    def save(self, *args, **kwargs):
        """Custom save method to check treatment success"""
        if not self.pk:  # New treatment
            super(Treatment, self).save(*args, **kwargs)
            if not self.success:
                self.doctor.incorrect_treatments += 1
                self.doctor.save()
        else:
            # Handle updates to avoid incrementing on every save
            old_treatment = Treatment.objects.get(pk=self.pk)
            if old_treatment.success and not self.success:
                self.doctor.incorrect_treatments += 1
            elif not old_treatment.success and self.success:
                self.doctor.incorrect_treatments -= 1
            self.doctor.save()
        super(Treatment, self).save(*args, **kwargs)


class Discharge(models.Model):
    discharge_id = models.AutoField(primary_key=True) 
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    discharged = models.BooleanField(default=False)
    discharge_date = models.DateTimeField(auto_now_add=True)  # Track discharge date

    def __str__(self):
        return f"{self.patient.name} - {'Discharged' if self.discharged else 'Not Discharged'}"