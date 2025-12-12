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
    total_activities = len(filtered)

    # Most practiced sport
    sports = Counter(a.get("sport_type", "Unknown") for a in filtered)
    unique_sports_count = len([s for s in sports if s != "Unknown"])
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
    # === SOCIAL DATA===
    #Total kudos
    total_kudos = sum(a.get("kudos_count", 0) for a in filtered)
    #Total photos
    total_photos = sum(a.get("total_photo_count", 0) for a in filtered)
    #Total comments
    total_comments = sum(a.get("comment_count", 0) for a in filtered)
    #Ratio company activities
    total_athlets = sum(a.get("athlete_count", 0) for a in filtered)
    
    return {
        "activities_last_year": total_activities,
        "total_distance_km": round(total_distance_km, 1),
        "distance_comparasion": distance_statistics(total_distance_km),
        "total_time_minutes": int(total_time_minutes),
        "total_time_days": round(total_time_days, 2),
        "total_elevation_m": total_elevation,
        "everest_equivalent":everest_equivalents(total_elevation),
        "dominant_sport": dominant_sport,
        "sports_practiced": unique_sports_count,
        "sport_podium": sport_podium(sports),
        "total_energy_kwh": total_energy_kwh,
        "house_power_days": round((total_energy_kwh/9), 2),
        "most_kudos_activity": {
            "name": most_kudos_activity.get("name") if most_kudos_activity else None,
            "kudos": most_kudos_activity.get("kudos_count") if most_kudos_activity else 0
        },
        "total_prs": total_prs,
        "total_kudos": total_kudos,
        "total_photos": total_photos,
        "total_comments": total_comments,
        "social_ratio": social_ratio(total_athlets, total_activities),
        "sports_breakdown": sports,
    }

def distance_statistics(total_distance_km):
    """
    Calculates a distance comparacion always starting from Barcelona.
    :param total_distance_km: The total of km performed in last year activities.
    :return: Returns the a string of the route.
    """
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

def everest_equivalents(total_elevation_m, everest_height_m=8848):
    """
    Calculates how many 'Everests' are equal to your total elevation.
    :param total_elevation_m: Total elevation in last year activties.
    :param everest_height_m: Everest height in meters (default 8848).
    :return: Returns the amount of Everests as a float number
    """
    if everest_height_m <= 0:
        raise ValueError("The total elevation must be a positive number")

    result = round((total_elevation_m / everest_height_m),2)

    return result

def social_ratio(total_athlets, total_activities):
    """
    Calculates the social ratio in your activities that describe if you performed 
    the actvities mostly alone (f.e. between 1-1.75) in pairs, trios or groups.
    :param total_athlets: Total athlets count in all the activties
    :param total_activities: The number of activities.
    :return: Returns the social ratio.
    """
    social_ratio = round((total_athlets - total_activities)/total_activities,2)

    if social_ratio <= 1.75:
        result = "Solo"
    elif social_ratio >= 1.75 and social_ratio <=2.75:
        result = "Duo"
    elif social_ratio >= 2.75 and social_ratio <= 3.75:
        result = "Trio"
    else:
        result = "Group"
    return result

def sport_podium(sport_data):
    podium_data = {
    "first":  {"sport": None, "count": 0},
    "second": {"sport": None, "count": 0},
    "third":  {"sport": None, "count": 0},
    }

    podium = sport_data.most_common(3)

    if len(podium) > 0:
        podium_data["first"] = {"sport": podium[0][0], "count": podium[0][1]}
    if len(podium) > 1:
        podium_data["second"] = {"sport": podium[1][0], "count": podium[1][1]}
    if len(podium) > 2:
        podium_data["third"] = {"sport": podium[2][0], "count": podium[2][1]}
    
    return podium_data