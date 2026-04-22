from rest_framework import serializers
from .models import Ride, Payment, FareSettings
from accounts.serializers import UserSerializer, RiderProfileSerializer


class FareSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareSettings
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class RideSerializer(serializers.ModelSerializer):
    passenger = UserSerializer(read_only=True)
    rider = RiderProfileSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Ride
        fields = '__all__'


class RequestRideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ride
        fields = (
            'pickup_latitude',
            'pickup_longitude',
            'pickup_address',
            'dropoff_latitude',
            'dropoff_longitude',
            'dropoff_address',
        )