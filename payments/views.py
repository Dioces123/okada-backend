import requests
import hashlib
import hmac
import json
from decouple import config
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rides.models import Ride, Payment

PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY')
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY')


def initialize_payment(email, amount_ghs, reference, metadata={}):
    """
    Initialize a Paystack payment.
    Amount must be in pesewas (GHS x 100)
    """
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'email': email,
        'amount': int(float(amount_ghs) * 100),  # Convert GHS to pesewas
        'reference': reference,
        'currency': 'GHS',
        'metadata': metadata,
        'channels': ['mobile_money', 'card'],
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()


def verify_payment(reference):
    """
    Verify a Paystack payment by reference.
    """
    url = f'https://api.paystack.co/transaction/verify/{reference}'
    headers = {
        'Authorization': f'Bearer {PAYSTACK_SECRET_KEY}',
    }
    response = requests.get(url, headers=headers)
    return response.json()


class InitializePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ride_id = request.data.get('ride_id')
        phone = request.data.get('phone')

        if not ride_id or not phone:
            return Response({'error': 'ride_id and phone are required.'}, status=400)

        try:
            ride = Ride.objects.get(id=ride_id, passenger=request.user, status='completed')
        except Ride.DoesNotExist:
            return Response({'error': 'Ride not found or not completed.'}, status=404)

        # Check if already paid
        if hasattr(ride, 'payment') and ride.payment.status == 'completed':
            return Response({'error': 'This ride has already been paid.'}, status=400)

        # Generate unique reference
        reference = f'OKADA-{ride.id}-{int(timezone.now().timestamp())}'

        # Use phone as email placeholder for MoMo
        email = f'{phone}@okada.app'

        result = initialize_payment(
            email=email,
            amount_ghs=ride.estimated_fare,
            reference=reference,
            metadata={
                'ride_id': ride.id,
                'passenger': request.user.name,
                'phone': phone,
            }
        )

        if result.get('status'):
            # Create pending payment record
            Payment.objects.update_or_create(
                ride=ride,
                defaults={
                    'amount': ride.estimated_fare,
                    'method': 'mtn_momo',
                    'status': 'pending',
                    'transaction_id': reference,
                }
            )
            return Response({
                'message': 'Payment initialized.',
                'authorization_url': result['data']['authorization_url'],
                'access_code': result['data']['access_code'],
                'reference': reference,
            }, status=200)

        return Response({'error': 'Could not initialize payment.'}, status=400)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get('reference')

        if not reference:
            return Response({'error': 'Reference is required.'}, status=400)

        result = verify_payment(reference)

        if result.get('status') and result['data']['status'] == 'success':
            # Update payment record
            try:
                payment = Payment.objects.get(transaction_id=reference)
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.save()

                # Update ride final fare
                ride = payment.ride
                ride.final_fare = payment.amount
                ride.save()

                # Update rider stats
                if ride.rider:
                    ride.rider.total_trips += 1
                    ride.rider.save()

                return Response({
                    'message': 'Payment successful!',
                    'amount': payment.amount,
                    'ride_id': ride.id,
                })
            except Payment.DoesNotExist:
                return Response({'error': 'Payment record not found.'}, status=404)

        return Response({
            'error': 'Payment not successful.',
            'status': result.get('data', {}).get('status', 'unknown')
        }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class PaystackWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Verify webhook signature
        paystack_signature = request.headers.get('x-paystack-signature')
        payload = request.body

        expected_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload,
            hashlib.sha512
        ).hexdigest()

        if paystack_signature != expected_signature:
            return Response({'error': 'Invalid signature.'}, status=400)

        event = json.loads(payload)

        if event.get('event') == 'charge.success':
            reference = event['data']['reference']
            try:
                payment = Payment.objects.get(transaction_id=reference)
                payment.status = 'completed'
                payment.paid_at = timezone.now()
                payment.save()
            except Payment.DoesNotExist:
                pass

        return Response({'status': 'ok'}, status=200)