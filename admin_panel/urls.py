from django.urls import path
from .views import (
    PendingRidersView,
    ApproveRiderView,
    RejectRiderView,
    AllUsersView,
    SuspendUserView,
    UnsuspendUserView,
    AllRidesView,
    ActiveRidesView,
    OnlineRidersView,
    ManageFareView,
    AnalyticsView,
)

urlpatterns = [
    # Riders
    path('riders/pending/', PendingRidersView.as_view(), name='pending-riders'),
    path('riders/<int:rider_id>/approve/', ApproveRiderView.as_view(), name='approve-rider'),
    path('riders/<int:rider_id>/reject/', RejectRiderView.as_view(), name='reject-rider'),
    path('riders/online/', OnlineRidersView.as_view(), name='online-riders'),

    # Users
    path('users/', AllUsersView.as_view(), name='all-users'),
    path('users/<int:user_id>/suspend/', SuspendUserView.as_view(), name='suspend-user'),
    path('users/<int:user_id>/unsuspend/', UnsuspendUserView.as_view(), name='unsuspend-user'),

    # Rides
    path('rides/', AllRidesView.as_view(), name='all-rides'),
    path('rides/active/', ActiveRidesView.as_view(), name='active-rides'),

    # Fare
    path('fare/', ManageFareView.as_view(), name='manage-fare'),

    # Analytics
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]