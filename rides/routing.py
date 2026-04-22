from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<ride_id>\w+)/rider/$', consumers.RiderLocationConsumer.as_asgi()),
    re_path(r'ws/ride/(?P<ride_id>\w+)/track/$', consumers.PassengerTrackingConsumer.as_asgi()),
]