import requests
from datetime import datetime, timedelta, timezone
from collections import Counter

from src.token_manager import get_valid_token

BASE_URL = "https://www.strava.com/api/v3"

def get_all_activities():
    access_token = get_valid_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    activities = []
    page = 1

    while True:
        url = f"{BASE_URL}/athlete/activities?page={page}&per_page=200"
        r = requests.get(url, headers=headers)
        data = r.json()

        if not isinstance(data, list) or len(data) == 0:
            break

        activities.extend(data)
        page += 1

    return activities

def get_wrapped_stats():
    activities = get_all_activities()

    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    filtered = []
    for a in activities:
        if "start_date" not in a:
            continue

        activity_date = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))
        if activity_date > one_year_ago:
            filtered.append(a)

    # Basic stats
    total_distance_km = sum(a.get("distance", 0) for a in filtered) / 1000
    total_time_minutes = sum(a.get("moving_time", 0) for a in filtered) / 60
    total_time_days = total_time_minutes / (60 * 24)
    total_elevation = sum(a.get("total_elevation_gain", 0) for a in filtered)

    # Most practiced sport
    sports = Counter(a.get("sport_type", "Unknown") for a in filtered)
    dominant_sport = sports.most_common(1)[0][0] if sports else None

    # Watts → kWh
    total_watt_seconds = 0
    for a in filtered:
        watts = a.get("weighted_average_watts")
        time = a.get("moving_time", 0)
        if watts:
            total_watt_seconds += watts * time

    total_energy_kwh = round(total_watt_seconds / 3_600_000, 2)

    # Most liked activity
    most_kudos_activity = None
    if filtered:
        most_kudos_activity = max(filtered, key=lambda x: x.get("kudos_count", 0))

    # Total PRs
    total_prs = sum(a.get("pr_count", 0) for a in filtered)

    return {
        "activities_last_year": len(filtered),
        "total_distance_km": round(total_distance_km, 1),
        "distance_comparasion": distance_statistics(total_distance_km),
        "total_time_minutes": int(total_time_minutes),
        "total_time_days": round(total_time_days, 2),
        "total_elevation_m": total_elevation,
        "dominant_sport": dominant_sport,
        "total_energy_kwh": total_energy_kwh,
        "most_kudos_activity": {
            "name": most_kudos_activity.get("name") if most_kudos_activity else None,
            "kudos": most_kudos_activity.get("kudos_count") if most_kudos_activity else 0
        },
        "total_prs": total_prs,
        "sports_breakdown": sports,
    }

def distance_statistics(total_distance_km):
    if total_distance_km >= 50  and total_distance_km <= 150:
        distance_comp = "Barcelona - Girona"
    elif total_distance_km >= 150  and total_distance_km <= 300:
        distance_comp = "Barcelona - Perpinyà"
    elif total_distance_km >= 300  and total_distance_km <= 600:
        distance_comp = "Barcelona - Madrid"
    elif total_distance_km >= 600  and total_distance_km <= 1000:
        distance_comp = "Barcelona - Paris"
    elif total_distance_km >= 1000  and total_distance_km <= 2000:
        distance_comp = "Barcelona - Berlin"
    elif total_distance_km >= 2000  and total_distance_km <= 4000:
        distance_comp = "Barcelona - Moscou"
    elif total_distance_km >= 4000  and total_distance_km <= 8000:
        distance_comp = "Barcelona - Nova York"
    elif total_distance_km >= 8000  and total_distance_km <= 14000:
        distance_comp = "Barcelona - Tòquio"
    else:
        "Gairebé mitja volta al món."
    return distance_comp

def elevation_statistics(total_elevation_input):
    if total_elevation_input >= 50  and total_elevation_input <= 150:
        elevation_comp = "Barcelona - Girona"
    elif total_elevation_input >= 150  and total_elevation_input <= 300:
        elevation_comp = "Barcelona - Perpinyà"
    else:
        "Deixa descansar els bessons."

    return elevation_comp