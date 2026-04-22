import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class RiderLocationConsumer(AsyncWebsocketConsumer):
    """
    Rider connects here to broadcast their live GPS location.
    Every update is sent to the ride's group so passenger can see it.
    """

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f'ride_{self.ride_id}'

        # Join ride group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'location_update':
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Save rider location to database
            await self.update_rider_location(latitude, longitude)

            # Broadcast to everyone in the ride group (passenger sees this)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'location_message',
                    'latitude': latitude,
                    'longitude': longitude,
                    'timestamp': str(timezone.now()),
                }
            )

        elif message_type == 'ride_status_update':
            new_status = data.get('status')

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'status_message',
                    'status': new_status,
                    'timestamp': str(timezone.now()),
                }
            )

    async def location_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp'],
        }))

    async def status_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ride_status_update',
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def update_rider_location(self, latitude, longitude):
        from accounts.models import RiderProfile
        from rides.models import Ride
        try:
            ride = Ride.objects.get(id=self.ride_id)
            if ride.rider:
                ride.rider.current_latitude = latitude
                ride.rider.current_longitude = longitude
                ride.rider.save()
        except Ride.DoesNotExist:
            pass


class PassengerTrackingConsumer(AsyncWebsocketConsumer):
    """
    Passenger connects here to receive live rider location updates.
    """

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.group_name = f'ride_{self.ride_id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': f'Tracking ride #{self.ride_id}',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass  # Passenger only listens, doesn't send

    async def location_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp'],
        }))

    async def status_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ride_status_update',
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))