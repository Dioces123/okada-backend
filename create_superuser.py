import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okada.settings')
django.setup()

from accounts.models import User

phone = '0509013833'
password = 'Gbawe@Secure!@#'

try:
    user = User.objects.get(phone=phone)
    user.set_password(password)
    user.save()
    print(f'Password reset for {phone}')
except User.DoesNotExist:
    User.objects.create_superuser(phone=phone, name='Okada Admin', password=password)
    print(f'Superuser created: {phone}')