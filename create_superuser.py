import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okada.settings')
django.setup()

from accounts.models import User

phone = '0509013833'
name = 'Okada'
password = 'Gbawe@Secure!@#'

if not User.objects.filter(phone=phone).exists():
    user = User.objects.create_superuser(
        phone=phone,
        name=name,
        password=password
    )
    print(f'Superuser created: {phone}')
else:
    print('Superuser already exists.')