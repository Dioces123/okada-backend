from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterPassengerSerializer,
    RegisterRiderSerializer,
    LoginSerializer,
    UserSerializer,
    RiderProfileSerializer
)
from .models import RiderProfile


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterPassengerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterPassengerSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Passenger registered successfully.',
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterRiderView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterRiderSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Rider registered. Awaiting admin approval.',
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response({
                'message': 'Login successful.',
                'user': UserSerializer(user).data,
                'tokens': tokens
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data

        if user.role == 'rider':
            try:
                profile = RiderProfile.objects.get(user=user)
                data['rider_profile'] = RiderProfileSerializer(profile).data
            except RiderProfile.DoesNotExist:
                data['rider_profile'] = None

        return Response(data, status=status.HTTP_200_OK)


class RiderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        if request.user.role != 'rider':
            return Response({'error': 'Only riders can update status.'}, status=403)

        try:
            profile = RiderProfile.objects.get(user=request.user)
        except RiderProfile.DoesNotExist:
            return Response({'error': 'Rider profile not found.'}, status=404)

        if profile.approval_status != 'approved':
            return Response({'error': 'Your account is not approved yet.'}, status=403)

        is_online = request.data.get('is_online')
        if is_online is not None:
            profile.is_online = is_online
            profile.save()

        return Response({
            'message': f"You are now {'online' if profile.is_online else 'offline'}.",
            'is_online': profile.is_online
        })