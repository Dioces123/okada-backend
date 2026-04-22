from django.urls import path
from .views import (
    RegisterPassengerView,
    RegisterRiderView,
    LoginView,
    ProfileView,
    RiderStatusView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/passenger/', RegisterPassengerView.as_view(), name='register-passenger'),
    path('register/rider/', RegisterRiderView.as_view(), name='register-rider'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('rider/status/', RiderStatusView.as_view(), name='rider-status'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]