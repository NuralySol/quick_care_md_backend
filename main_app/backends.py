from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()  
        try:
            user = User.objects.get(username=username)
            # Superusers bypass the is_active check
            if user.is_superuser or (user.is_active and user.check_password(password)):
                if user.check_password(password):
                    return user
                else:
                    return None  
            else:
                return None 
        except User.DoesNotExist:
            return None  