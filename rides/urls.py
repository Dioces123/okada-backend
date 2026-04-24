from django.urls import path
from .views import (
    FareEstimateView,
    RequestRideView,
    AcceptRideView,
    UpdateRideStatusView,
    CancelRideView,
    RideHistoryView,
    RateRideView,
    AvailableRidesView,
)

urlpatterns = [
    path('fare-estimate/', FareEstimateView.as_view(), name='fare-estimate'),
    path('request/', RequestRideView.as_view(), name='request-ride'),
    path('<int:ride_id>/accept/', AcceptRideView.as_view(), name='accept-ride'),
    path('<int:ride_id>/status/', UpdateRideStatusView.as_view(), name='update-ride-status'),
    path('<int:ride_id>/cancel/', CancelRideView.as_view(), name='cancel-ride'),
    path('<int:ride_id>/rate/', RateRideView.as_view(), name='rate-ride'),
    path('history/', RideHistoryView.as_view(), name='ride-history'),
    path('available/', AvailableRidesView.as_view(), name='available-rides'),
]
