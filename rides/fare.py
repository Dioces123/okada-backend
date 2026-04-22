from .models import FareSettings
from math import radians, sin, cos, sqrt, atan2


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula — calculates real distance
    between two GPS coordinates in kilometers.
    """
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(radians, [
        float(lat1), float(lon1),
        float(lat2), float(lon2)
    ])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return round(R * c, 2)


def calculate_fare(lat1, lon1, lat2, lon2):
    """
    fare = base_fare + (distance x rate_per_km)
    Uses active FareSettings from the database.
    """
    try:
        settings = FareSettings.objects.filter(is_active=True).latest('updated_at')
    except FareSettings.DoesNotExist:
        # Fallback defaults if admin hasn't set pricing yet
        base_fare = 3.00
        rate_per_km = 2.50
        minimum_fare = 5.00
    else:
        base_fare = float(settings.base_fare)
        rate_per_km = float(settings.rate_per_km)
        minimum_fare = float(settings.minimum_fare)

    distance = calculate_distance(lat1, lon1, lat2, lon2)
    fare = base_fare + (distance * rate_per_km)

    # Never charge below minimum
    fare = max(fare, minimum_fare)

    return {
        'distance_km': distance,
        'estimated_fare': round(fare, 2)
    }