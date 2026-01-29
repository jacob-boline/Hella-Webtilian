# hr_access/auth_backend.py


from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class CustomBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        ident = username.strip()
        ident_ci = ident.casefold()

        if "@" in ident:
            user = User.objects.filter(email__iexact=ident).first()
        else:
            user = User.objects.filter(username_ci=ident_ci).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
