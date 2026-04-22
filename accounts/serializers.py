from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, RiderProfile, OTPVerification
import random


class RegisterPassengerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ('phone', 'name', 'password')

    def create(self, validated_data):
        return User.objects.create_user(
            phone=validated_data['phone'],
            name=validated_data['name'],
            role='passenger',
            password=validated_data['password']
        )


class RegisterRiderSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    ghana_card_number = serializers.CharField()
    license_number = serializers.CharField()
    number_plate = serializers.CharField()
    ghana_card_image = serializers.ImageField()
    license_image = serializers.ImageField()
    profile_photo = serializers.ImageField()

    class Meta:
        model = User
        fields = (
            'phone', 'name', 'password',
            'ghana_card_number', 'license_number', 'number_plate',
            'ghana_card_image', 'license_image', 'profile_photo'
        )

    def create(self, validated_data):
        # Separate rider profile fields
        profile_fields = {
            'ghana_card_number': validated_data.pop('ghana_card_number'),
            'license_number': validated_data.pop('license_number'),
            'number_plate': validated_data.pop('number_plate'),
            'ghana_card_image': validated_data.pop('ghana_card_image'),
            'license_image': validated_data.pop('license_image'),
            'profile_photo': validated_data.pop('profile_photo'),
        }

        # Create the user
        user = User.objects.create_user(
            phone=validated_data['phone'],
            name=validated_data['name'],
            role='rider',
            password=validated_data['password']
        )

        # Create rider profile
        RiderProfile.objects.create(user=user, **profile_fields)

        return user


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone = data.get('phone')
        password = data.get('password')
        user = authenticate(username=phone, password=password)

        if not user:
            raise serializers.ValidationError('Invalid phone number or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been suspended.')

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'phone', 'name', 'role', 'date_joined')


class RiderProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()

    class Meta:
        model = RiderProfile
        fields = (
            'id', 'user', 'number_plate', 'ghana_card_number',
            'license_number', 'profile_photo', 'approval_status',
            'is_online', 'average_rating', 'total_trips',
            'current_latitude', 'current_longitude', 'created_at'
        )