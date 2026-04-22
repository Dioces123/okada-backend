from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RiderProfile, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('phone', 'name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal Info', {'fields': ('name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'number_plate', 'approval_status', 'is_online', 'average_rating', 'created_at')
    list_filter = ('approval_status', 'is_online')
    search_fields = ('user__name', 'user__phone', 'number_plate', 'ghana_card_number')
    ordering = ('-created_at',)

    fieldsets = (
        ('Rider Info', {'fields': ('user', 'number_plate', 'ghana_card_number', 'license_number')}),
        ('Documents', {'fields': ('ghana_card_image', 'license_image', 'profile_photo')}),
        ('Status', {'fields': ('approval_status', 'rejection_reason', 'is_online')}),
        ('Location', {'fields': ('current_latitude', 'current_longitude')}),
        ('Stats', {'fields': ('total_rating', 'total_trips')}),
    )

    actions = ['approve_riders', 'reject_riders']

    def approve_riders(self, request, queryset):
        queryset.update(approval_status='approved')
        self.message_user(request, f"{queryset.count()} rider(s) approved.")
    approve_riders.short_description = 'Approve selected riders'

    def reject_riders(self, request, queryset):
        queryset.update(approval_status='rejected')
        self.message_user(request, f"{queryset.count()} rider(s) rejected.")
    reject_riders.short_description = 'Reject selected riders'


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp_code', 'is_used', 'created_at')
    list_filter = ('is_used',)