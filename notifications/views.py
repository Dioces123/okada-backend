import requests
from decouple import config


ARKESEL_API_KEY = config('ARKESEL_API_KEY')
SENDER_ID = config('ARKESEL_SENDER_ID', default='Okada')


def send_sms(phone, message):
    print(f"📱 Sending SMS to {phone}: {message}")
    try:
        # Convert 0XXXXXXXXX to 233XXXXXXXXX
        if phone.startswith('0'):
            phone = '233' + phone[1:]

        url = "https://sms.arkesel.com/sms/api"
        params = {
            'action': 'send-sms',
            'api_key': ARKESEL_API_KEY,
            'to': phone,
            'from': SENDER_ID,
            'sms': message,
        }
        response = requests.get(url, params=params)
        print(f"📱 Arkesel response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"SMS error: {e}")
        return None


# ── Notification messages ─────────────────────────────────────

def notify_ride_requested(passenger_phone, fare, pickup):
    send_sms(
        passenger_phone,
        f"Okada: Your ride has been requested from {pickup}. "
        f"Estimated fare: GHS {fare}. Finding your rider now..."
    )


def notify_rider_new_request(rider_phone, passenger_name, pickup):
    send_sms(
        rider_phone,
        f"Okada: New ride request from {passenger_name} at {pickup}. "
        f"Open the app to accept."
    )


def notify_ride_accepted(passenger_phone, rider_name, plate):
    send_sms(
        passenger_phone,
        f"Okada: Your rider {rider_name} ({plate}) has accepted your ride. "
        f"They are on their way to you!"
    )


def notify_rider_arrived(passenger_phone, rider_name):
    send_sms(
        passenger_phone,
        f"Okada: Your rider {rider_name} has arrived at your location. "
        f"Please come out."
    )


def notify_trip_started(passenger_phone):
    send_sms(
        passenger_phone,
        f"Okada: Your trip has started. Sit tight and enjoy your ride!"
    )


def notify_trip_completed(passenger_phone, fare):
    send_sms(
        passenger_phone,
        f"Okada: Your trip is complete. Total fare: GHS {fare}. "
        f"Thank you for riding with Okada!"
    )


def notify_ride_cancelled(phone, by_who):
    send_sms(
        phone,
        f"Okada: Your ride has been cancelled by {by_who}. "
        f"Please request a new ride."
    )


def notify_rider_approved(rider_phone, rider_name):
    send_sms(
        rider_phone,
        f"Okada: Congratulations {rider_name}! Your account has been approved. "
        f"You can now go online and start accepting rides."
    )


def notify_rider_rejected(rider_phone, rider_name, reason):
    send_sms(
        rider_phone,
        f"Okada: Hi {rider_name}, your rider application was not approved. "
        f"Reason: {reason}. Please contact support."
    )