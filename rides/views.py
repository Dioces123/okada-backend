from notifications.views import (
    notify_ride_requested,
    notify_rider_new_request,
    notify_ride_accepted,
    notify_rider_arrived,
    notify_trip_started,
    notify_trip_completed,
    notify_ride_cancelled,
)
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Ride, Payment, FareSettings
from .serializers import RideSerializer, RequestRideSerializer, FareSettingsSerializer
from .fare import calculate_fare
from .matching import find_nearest_rider
from django.db import transaction


class FareEstimateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        required = ['pickup_latitude', 'pickup_longitude', 'dropoff_latitude', 'dropoff_longitude']
        for field in required:
            if field not in request.data:
                return Response({'error': f'{field} is required.'}, status=400)

        result = calculate_fare(
            request.data['pickup_latitude'],
            request.data['pickup_longitude'],
            request.data['dropoff_latitude'],
            request.data['dropoff_longitude']
        )

        return Response(result, status=200)


class RequestRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'passenger':
            return Response({'error': 'Only passengers can request rides.'}, status=403)

        active = Ride.objects.filter(
            passenger=request.user,
            status__in=['requested', 'accepted', 'arrived', 'ongoing']
        ).exists()

        if active:
            return Response({'error': 'You already have an active ride.'}, status=400)

        serializer = RequestRideSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        fare_data = calculate_fare(
            data['pickup_latitude'], data['pickup_longitude'],
            data['dropoff_latitude'], data['dropoff_longitude']
        )

        ride = Ride.objects.create(
            passenger=request.user,
            pickup_latitude=data['pickup_latitude'],
            pickup_longitude=data['pickup_longitude'],
            pickup_address=data.get('pickup_address', ''),
            dropoff_latitude=data['dropoff_latitude'],
            dropoff_longitude=data['dropoff_longitude'],
            dropoff_address=data.get('dropoff_address', ''),
            distance_km=fare_data['distance_km'],
            estimated_fare=fare_data['estimated_fare'],
            status='requested'
        )

        nearby_riders = find_nearest_rider(
            data['pickup_latitude'],
            data['pickup_longitude']
        )

        # Notify passenger
        notify_ride_requested(
            request.user.phone,
            fare_data['estimated_fare'],
            data.get('pickup_address', 'your location')
        )

        # Notify nearby riders
        for distance, rider in nearby_riders[:3]:
            notify_rider_new_request(
                rider.user.phone,
                request.user.name,
                data.get('pickup_address', 'unknown location')
            )

        return Response({
            'message': 'Ride requested successfully.',
            'ride': RideSerializer(ride).data,
            'nearby_riders_found': len(nearby_riders),
            'estimated_fare': fare_data['estimated_fare'],
            'distance_km': fare_data['distance_km'],
        }, status=201)


class AcceptRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        if request.user.role != 'rider':
            return Response({'error': 'Only riders can accept rides.'}, status=403)

        try:
            rider_profile = request.user.rider_profile
        except:
            return Response({'error': 'Rider profile not found.'}, status=404)

        if rider_profile.approval_status != 'approved':
            return Response({'error': 'Your account is not approved.'}, status=403)

        # Use atomic transaction + select_for_update to prevent race condition
        try:
            with transaction.atomic():
                ride = Ride.objects.select_for_update().get(
                    id=ride_id,
                    status='requested',
                    rider__isnull=True
                )
                ride.rider = rider_profile
                ride.status = 'accepted'
                ride.accepted_at = timezone.now()
                ride.save()

                notify_ride_accepted(
                    ride.passenger.phone,
                    rider_profile.user.name,
                    rider_profile.number_plate
                )

        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found or already taken.'}, status=404)

        return Response({
            'message': 'Ride accepted.',
            'ride': RideSerializer(ride).data
        }, status=200)


class UpdateRideStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found.'}, status=404)

        new_status = request.data.get('status')
        now = timezone.now()

        valid_transitions = {
            'accepted': 'arrived',
            'arrived': 'ongoing',
            'ongoing': 'completed',
        }

        if new_status not in valid_transitions.values():
            return Response({'error': 'Invalid status.'}, status=400)

        if valid_transitions.get(ride.status) != new_status:
            return Response({
                'error': f'Cannot move from {ride.status} to {new_status}.'
            }, status=400)

        if new_status == 'arrived':
            ride.arrived_at = now
            notify_rider_arrived(ride.passenger.phone, ride.rider.user.name)

        elif new_status == 'ongoing':
            ride.started_at = now
            notify_trip_started(ride.passenger.phone)

        elif new_status == 'completed':
            ride.completed_at = now
            ride.final_fare = ride.estimated_fare
            Payment.objects.create(
                ride=ride,
                amount=ride.final_fare,
                method=request.data.get('payment_method', 'cash'),
                status='completed',
                paid_at=now
            )
            rider = ride.rider
            rider.total_trips += 1
            rider.save()
            notify_trip_completed(ride.passenger.phone, ride.final_fare)

        ride.status = new_status
        ride.save()

        return Response({
            'message': f'Ride status updated to {new_status}.',
            'ride': RideSerializer(ride).data
        }, status=200)


class CancelRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found.'}, status=404)

        if ride.status in ['completed', 'cancelled']:
            return Response({'error': 'This ride cannot be cancelled.'}, status=400)

        cancelled_by = 'passenger' if request.user.role == 'passenger' else 'rider'

        if cancelled_by == 'rider' and ride.passenger:
            notify_ride_cancelled(ride.passenger.phone, 'your rider')
        elif cancelled_by == 'passenger' and ride.rider:
            notify_ride_cancelled(ride.rider.user.phone, 'the passenger')

        ride.status = 'cancelled'
        ride.cancelled_at = timezone.now()
        ride.save()

        return Response({'message': 'Ride cancelled.'}, status=200)


class RideHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'passenger':
            rides = Ride.objects.filter(passenger=user).order_by('-requested_at')
        elif user.role == 'rider':
            rides = Ride.objects.filter(rider__user=user).order_by('-requested_at')
        else:
            rides = Ride.objects.all().order_by('-requested_at')

        return Response(RideSerializer(rides, many=True).data, status=200)


class RateRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        try:
            ride = Ride.objects.get(id=ride_id, passenger=request.user, status='completed')
        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found or not completed.'}, status=404)

        rating = request.data.get('rating')
        if not rating or int(rating) not in range(1, 6):
            return Response({'error': 'Rating must be between 1 and 5.'}, status=400)

        ride.passenger_rating = rating
        ride.rating_comment = request.data.get('comment', '')
        ride.save()

        rider = ride.rider
        rider.total_rating += int(rating)
        rider.save()

        return Response({'message': 'Rating submitted. Thank you!'}, status=200)


class AvailableRidesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'rider':
            return Response({'error': 'Only riders can view available rides.'}, status=403)

        try:
            rider_profile = request.user.rider_profile
        except:
            return Response({'error': 'Rider profile not found.'}, status=404)

        if rider_profile.approval_status != 'approved':
            return Response({'error': 'Your account is not approved.'}, status=403)

        rides = Ride.objects.filter(
            status='requested',
            rider__isnull=True
        ).order_by('-requested_at')

        return Response(RideSerializer(rides, many=True).data, status=200)