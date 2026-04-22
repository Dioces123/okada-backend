from django.contrib import admin
from .models import Ride, Payment, FareSettings


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'rider', 'status', 'estimated_fare', 'requested_at')
    list_filter = ('status',)
    search_fields = ('passenger__name', 'passenger__phone')
    ordering = ('-requested_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('ride', 'amount', 'method', 'status', 'paid_at')
    list_filter = ('method', 'status')


@admin.register(FareSettings)
class FareSettingsAdmin(admin.ModelAdmin):
    list_display = ('base_fare', 'rate_per_km', 'minimum_fare', 'is_active', 'updated_at')