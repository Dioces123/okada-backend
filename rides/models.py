from django.db import models
from accounts.models import User, RiderProfile


class Ride(models.Model):

    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('arrived', 'Arrived'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passenger_rides')
    rider = models.ForeignKey(RiderProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='rider_rides')

    # Pickup
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_address = models.CharField(max_length=255, blank=True)

    # Dropoff
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_address = models.CharField(max_length=255, blank=True)

    # Fare
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estimated_fare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    final_fare = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    platform_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rider_earnings = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')

    # Rating
    passenger_rating = models.IntegerField(null=True, blank=True)  # Passenger rates rider
    rating_comment = models.TextField(blank=True, null=True)

    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ride #{self.id} | {self.passenger.name} | {self.status}"


class Payment(models.Model):

    METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('vodafone', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Ride #{self.ride.id} | {self.method} | {self.status}"


class FareSettings(models.Model):
    base_fare = models.DecimalField(max_digits=6, decimal_places=2, default=3.00)
    rate_per_km = models.DecimalField(max_digits=6, decimal_places=2, default=2.50)
    minimum_fare = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fare Settings'

    def __str__(self):
        return f"Base: GHS {self.base_fare} | Per KM: GHS {self.rate_per_km}"