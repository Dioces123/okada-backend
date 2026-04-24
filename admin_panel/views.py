from notifications.views import notify_rider_approved, notify_rider_rejected
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from accounts.models import User, RiderProfile
from rides.models import Ride, Payment, FareSettings
from accounts.serializers import RiderProfileSerializer, UserSerializer
from rides.serializers import RideSerializer, FareSettingsSerializer


class IsAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'admin'


# ─── RIDER MANAGEMENT ───────────────────────────────────────────

class PendingRidersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        riders = RiderProfile.objects.filter(
            approval_status='pending'
        ).order_by('-created_at')
        return Response(RiderProfileSerializer(riders, many=True).data)


class ApproveRiderView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, rider_id):
        try:
            rider = RiderProfile.objects.get(id=rider_id)
        except RiderProfile.DoesNotExist:
            return Response({'error': 'Rider not found.'}, status=404)

        rider.approval_status = 'approved'
        rider.rejection_reason = None
        rider.save()

        # Notify rider via SMS
        notify_rider_approved(rider.user.phone, rider.user.name)

        return Response({
            'message': f'{rider.user.name} has been approved.',
            'rider': RiderProfileSerializer(rider).data
        })


class RejectRiderView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, rider_id):
        try:
            rider = RiderProfile.objects.get(id=rider_id)
        except RiderProfile.DoesNotExist:
            return Response({'error': 'Rider not found.'}, status=404)

        reason = request.data.get('reason', 'Documents not acceptable.')
        rider.approval_status = 'rejected'
        rider.rejection_reason = reason
        rider.save()

        # Notify rider via SMS
        notify_rider_rejected(rider.user.phone, rider.user.name, reason)

        return Response({
            'message': f'{rider.user.name} has been rejected.',
            'reason': reason
        })


# ─── USER MANAGEMENT ────────────────────────────────────────────

class AllUsersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        role = request.query_params.get('role')
        users = User.objects.all().order_by('-date_joined')
        if role:
            users = users.filter(role=role)
        return Response(UserSerializer(users, many=True).data)


class SuspendUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        if user.role == 'admin':
            return Response({'error': 'Cannot suspend an admin.'}, status=403)

        user.is_active = False
        user.save()

        if user.role == 'rider':
            try:
                user.rider_profile.is_online = False
                user.rider_profile.save()
            except Exception:
                pass

        return Response({'message': f'{user.name} has been suspended.'})


class UnsuspendUserView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        user.is_active = True
        user.save()
        return Response({'message': f'{user.name} has been reactivated.'})


# ─── RIDE MONITORING ────────────────────────────────────────────

class AllRidesView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        status_filter = request.query_params.get('status')
        rides = Ride.objects.all().order_by('-requested_at')
        if status_filter:
            rides = rides.filter(status=status_filter)
        return Response(RideSerializer(rides, many=True).data)


class ActiveRidesView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        rides = Ride.objects.filter(
            status__in=['requested', 'accepted', 'arrived', 'ongoing']
        ).order_by('-requested_at')
        return Response(RideSerializer(rides, many=True).data)


class OnlineRidersView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        riders = RiderProfile.objects.filter(
            is_online=True,
            approval_status='approved'
        )
        return Response(RiderProfileSerializer(riders, many=True).data)


# ─── FARE MANAGEMENT ────────────────────────────────────────────

class ManageFareView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        try:
            fare = FareSettings.objects.filter(is_active=True).latest('updated_at')
            return Response(FareSettingsSerializer(fare).data)
        except FareSettings.DoesNotExist:
            return Response({'message': 'No fare settings found.'}, status=404)

    def post(self, request):
        FareSettings.objects.all().update(is_active=False)

        serializer = FareSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(is_active=True)
            return Response({
                'message': 'Fare settings updated.',
                'settings': serializer.data
            }, status=201)
        return Response(serializer.errors, status=400)


# ─── ANALYTICS ──────────────────────────────────────────────────

class AnalyticsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        today = timezone.now().date()

        total_users = User.objects.filter(role='passenger').count()
        total_riders = RiderProfile.objects.filter(approval_status='approved').count()
        pending_riders = RiderProfile.objects.filter(approval_status='pending').count()

        total_rides = Ride.objects.count()
        completed_rides = Ride.objects.filter(status='completed').count()
        cancelled_rides = Ride.objects.filter(status='cancelled').count()
        active_rides = Ride.objects.filter(
            status__in=['requested', 'accepted', 'arrived', 'ongoing']
        ).count()

        rides_today = Ride.objects.filter(requested_at__date=today).count()
        completed_today = Ride.objects.filter(
            status='completed',
            completed_at__date=today
        ).count()

        revenue_today = Payment.objects.filter(
            status='completed',
            paid_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0

        total_revenue = Payment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Calculate platform earnings (13%) and rider payouts (87%)
        platform_earnings_today = round(float(revenue_today) * 0.13, 2)
        platform_total_earnings = round(float(total_revenue) * 0.13, 2)
        rider_payouts_today = round(float(revenue_today) * 0.87, 2)
        rider_total_payouts = round(float(total_revenue) * 0.87, 2)

        return Response({
            'users': {
                'total_passengers': total_users,
                'total_approved_riders': total_riders,
                'pending_rider_approvals': pending_riders,
            },
            'rides': {
                'total_rides': total_rides,
                'completed_rides': completed_rides,
                'cancelled_rides': cancelled_rides,
                'active_rides_now': active_rides,
                'rides_today': rides_today,
                'completed_today': completed_today,
            },
            'revenue': {
                'revenue_today_ghs': float(revenue_today),
                'total_revenue_ghs': float(total_revenue),
                'platform_earnings_today': platform_earnings_today,
                'platform_total_earnings': platform_total_earnings,
                'rider_payouts_today': rider_payouts_today,
                'rider_total_payouts': rider_total_payouts,
                'commission_rate': '13%',
            }
        })