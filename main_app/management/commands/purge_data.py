#! Special script to purge the PSQL DB local

from django.core.management.base import BaseCommand
from main_app.models import User, Doctor, Patient

class Command(BaseCommand):
    help = 'Purge all data from the User, Doctor, and Patient tables.'

    def handle(self, *args, **kwargs):
        # Purge all doctors
        Doctor.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all Doctor records'))

        # Purge all patients
        Patient.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all Patient records'))

        # Purge all users
        User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully deleted all User records'))

        self.stdout.write(self.style.SUCCESS('All data purged successfully!'))