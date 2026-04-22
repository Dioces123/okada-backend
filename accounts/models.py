from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, phone, name, role='passenger', password=None):
        if not phone:
            raise ValueError('Phone number is required')
        user = self.model(phone=phone, name=name, role=role)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name, password):
        user = self.create_user(phone=phone, name=name, password=password)
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('passenger', 'Passenger'),
        ('rider', 'Rider'),
        ('admin', 'Admin'),
    )

    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='passenger')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return f"{self.name} ({self.phone}) - {self.role}"


class RiderProfile(models.Model):

    APPROVAL_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')

    # Verification documents
    ghana_card_number = models.CharField(max_length=50, unique=True)
    license_number = models.CharField(max_length=50, unique=True)
    number_plate = models.CharField(max_length=20, unique=True)

    # Document uploads
    ghana_card_image = models.ImageField(upload_to='documents/ghana_cards/')
    license_image = models.ImageField(upload_to='documents/licenses/')
    profile_photo = models.ImageField(upload_to='documents/photos/')

    # Status
    approval_status = models.CharField(max_length=20, choices=APPROVAL_STATUS, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    is_online = models.BooleanField(default=False)

    # Location (updated in real-time)
    current_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Rating
    total_rating = models.FloatField(default=0.0)
    total_trips = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def average_rating(self):
        if self.total_trips == 0:
            return 0.0
        return round(self.total_rating / self.total_trips, 1)

    def __str__(self):
        return f"Rider: {self.user.name} | {self.number_plate} | {self.approval_status}"


class OTPVerification(models.Model):
    phone = models.CharField(max_length=15)
    otp_code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.phone}"