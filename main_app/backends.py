import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        logger.debug(f"Attempting to authenticate user: {username}")

        User = get_user_model()
        if username is None or password is None:
            logger.warning("Username or password not provided")
            return None

        try:
            user = User.objects.get(username=username)
            if user.is_superuser or (user.is_active and user.check_password(password)):
                logger.debug(f"User {username} authenticated successfully")
                print(user)
                return user
            else:
                logger.warning(f"Authentication failed for user {username}: inactive or incorrect password")
                return None
        except User.DoesNotExist:
            logger.warning(f"User {username} does not exist")
            return None