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

    def delete(self, *args, **kwargs):
        if self.role == 'admin':
            if Doctor.objects.exists() or Patient.objects.exists():
                raise ValidationError("Cannot delete admin while doctors or patients exist.")
        super(User, self).delete(*args, **kwargs)

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    incorrect_treatments = models.IntegerField(default=0)  # Track incorrect treatments

    def __str__(self):
        return self.name

    def fire(self):
        """Fire the doctor if incorrect treatments exceed a limit"""
        if self.incorrect_treatments >= 3:  # Assuming 3 incorrect treatments lead to firing
            self.user.delete()  # Deleting the user will delete the doctor too

class Patient(models.Model):
    name = models.CharField(max_length=100)
    time_admitted = models.DateTimeField(auto_now_add=True)
    disease = models.ManyToManyField('Disease')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    is_terminal = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Treatment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    treatment_options = models.TextField()
    success = models.BooleanField(default=False)  # Field to track whether the treatment is correct

    def __str__(self):
        return f"{self.patient.name} - {self.treatment_options}"

    def save(self, *args, **kwargs):
        """Custom save method to check treatment success"""
        super(Treatment, self).save(*args, **kwargs)
        if not self.success:
            # If treatment is incorrect, increase the doctor's incorrect treatment count
            self.doctor.incorrect_treatments += 1
            self.doctor.save()

class Discharge(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    discharged = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient.name} - {'Discharged' if self.discharged else 'Not Discharged'}"