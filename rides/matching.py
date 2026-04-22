from accounts.models import RiderProfile
from math import radians, sin, cos, sqrt, atan2


def get_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [
        float(lat1), float(lon1),
        float(lat2), float(lon2)
    ])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def find_nearest_rider(pickup_lat, pickup_lon, radius_km=5):
    """
    Finds all approved, online riders within radius_km.
    Returns them sorted by distance — nearest first.
    """
    available_riders = RiderProfile.objects.filter(
        approval_status='approved',
        is_online=True,
        current_latitude__isnull=False,
        current_longitude__isnull=False,
    )

    nearby = []

    for rider in available_riders:
        distance = get_distance(
            pickup_lat, pickup_lon,
            rider.current_latitude,
            rider.current_longitude
        )
        if distance <= radius_km:
            nearby.append((distance, rider))

    # Sort by nearest first
    nearby.sort(key=lambda x: x[0])

    return nearby