import requests
from datetime import datetime, timedelta, timezone
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.token_manager import get_valid_token

BASE_URL = "https://www.strava.com/api/v3"

def get_activities_for_last_year():
    """VERSIÓ SIMPLIFICADA: 1 sola petició, sense paral·lelització innecessària"""
    print(f"🔍 [DEBUG] Iniciant get_activities_for_last_year()")
    
    try:
        access_token = get_valid_token()
        if not access_token:
            print("🚨 [DEBUG] Token buit")
            return []
    except Exception as e:
        print(f"🚨 [DEBUG] Error obtenint token: {e}")
        return []
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Últim any
    one_year_ago = int((datetime.now(timezone.utc) - timedelta(days=365)).timestamp())
    
    # 1 SOLA PETICIÓ amb per_page=200 (més que suficient per 135 activitats)
    url = f"{BASE_URL}/athlete/activities?page=1&per_page=200&after={one_year_ago}"
    print(f"🔍 [DEBUG] URL: {url}")
    
    try:
        import time
        start = time.time()
        response = requests.get(url, headers=headers, timeout=15)
        elapsed = time.time() - start
        
        print(f"📡 [DEBUG] Strava API respon en {elapsed:.1f}s - Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"🚨 [DEBUG] Error {response.status_code}: {response.text[:200]}")
            return []
        
        activities = response.json()
        if not isinstance(activities, list):
            print(f"🚨 [DEBUG] Resposta no és llista: {type(activities)}")
            return []
        
        print(f"✅ [DEBUG] Obtingudes {len(activities)} activitats")
        return activities
        
    except requests.exceptions.Timeout:
        print("⏰ [DEBUG] TIMEOUT")
        return []
    except Exception as e:
        print(f"🚨 [DEBUG] Error: {e}")
        return []

def get_wrapped_stats():
    """
    Versió OPTIMITZADA: Un sol pass per calcular totes les estadístiques
    i evita múltiples iteracions sobre la llista.
    """
    activities = get_activities_for_last_year()
    
    if not activities:
        return get_empty_stats()
    
    # Inicialitza totes les variables en una sola passada
    stats = {
        'total_distance': 0,
        'total_time': 0,
        'total_elevation': 0,
        'total_watt_seconds': 0,
        'total_kudos': 0,
        'total_photos': 0,
        'total_comments': 0,
        'total_athlets': 0,
        'total_prs': 0,
        'sports_counter': Counter(),
        'hour_counter': Counter(),
        'max_kudos': 0,
        'most_kudos_activity': None,
        'total_activities': len(activities)
    }
    
    # UN SOL BUCLE per calcular-ho tot
    for a in activities:
        # Distància
        stats['total_distance'] += a.get("distance", 0)
        
        # Temps
        moving_time = a.get("moving_time", 0)
        stats['total_time'] += moving_time
        
        # Elevació
        stats['total_elevation'] += a.get("total_elevation_gain", 0)
        
        # Watts → kWh
        watts = a.get("weighted_average_watts")
        if watts:
            stats['total_watt_seconds'] += watts * moving_time
        
        # Social
        kudos = a.get("kudos_count", 0)
        stats['total_kudos'] += kudos
        if kudos > stats['max_kudos']:
            stats['max_kudos'] = kudos
            stats['most_kudos_activity'] = a
        
        stats['total_photos'] += a.get("total_photo_count", 0)
        stats['total_comments'] += a.get("comment_count", 0)
        stats['total_athlets'] += a.get("athlete_count", 0)
        stats['total_prs'] += a.get("pr_count", 0)
        
        # Esports
        sport = a.get("sport_type", "Unknown")
        if sport != "Unknown":
            stats['sports_counter'][sport] += 1
        
        # Hora de l'activitat
        if "start_date" in a:
            try:
                dt = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))
                hour = dt.hour
                if 5 <= hour < 12:
                    stats['hour_counter']["morning"] += 1
                elif 12 <= hour < 19:
                    stats['hour_counter']["afternoon"] += 1
                else:
                    stats['hour_counter']["night"] += 1
            except:
                pass
    
    # CÀLCULS FINALS
    total_distance_km = stats['total_distance'] / 1000
    total_time_minutes = stats['total_time'] / 60
    total_time_days = total_time_minutes / (60 * 24)
    total_energy_kwh = round(stats['total_watt_seconds'] / 3_600_000, 2)
    
    # Esport dominant
    dominant_sport = "Unknown"
    sport_podium_list = []
    if stats['sports_counter']:
        dominant_sport = stats['sports_counter'].most_common(1)[0][0]
        sport_podium_list = stats['sports_counter'].most_common(3)
    
    # Temps preferit
    training_profile = "Matiner"
    if stats['hour_counter']:
        dominant_hour = stats['hour_counter'].most_common(1)[0][0]
        mapping = {"morning": "Matiner", "afternoon": "De tardes", "night": "Nocturn"}
        training_profile = mapping.get(dominant_hour, "Matiner")
    
    # Construcció del podium
    podium_data = {"first": {"sport": None, "count": 0},
                   "second": {"sport": None, "count": 0},
                   "third": {"sport": None, "count": 0}}
    
    for i, (sport, count) in enumerate(sport_podium_list[:3]):
        key = ["first", "second", "third"][i]
        podium_data[key] = {"sport": sport, "count": count}
    
    # Retorna el diccionari final (igual que abans)
    return {
        "activities_last_year": str(stats['total_activities']) + " Activitats",
        "total_distance_km": str(round(total_distance_km, 1)) + " Km",
        "distance_comparasion": distance_statistics(total_distance_km),
        "total_time_minutes": str(int(total_time_minutes)) + " min",
        "total_time_days": str(round(total_time_days, 2)) + " dies",
        "total_elevation_m": str(int(stats['total_elevation'])) + " m",
        "everest_equivalent": everest_equivalents(stats['total_elevation']),
        "dominant_sport": dominant_sport,
        "sports_practiced": len(stats['sports_counter']),
        "sport_podium": podium_data,
        "total_energy_kwh": str(total_energy_kwh) + " kWh",
        "house_power_days": str(round((total_energy_kwh/9), 1)) + " dies",
        "most_kudos_activity": {
            "name": stats['most_kudos_activity'].get("name") if stats['most_kudos_activity'] else None,
            "kudos": stats['most_kudos_activity'].get("kudos_count") if stats['most_kudos_activity'] else 0
        },
        "total_prs": stats['total_prs'],
        "total_kudos": stats['total_kudos'],
        "total_photos": stats['total_photos'],
        "total_comments": stats['total_comments'],
        "social_ratio": social_ratio(stats['total_athlets'], stats['total_activities']),
        "train_time": training_profile,
    }

def get_empty_stats():
    """Retorna estadístiques buides per a usuaris sense activitats"""
    return {
        "activities_last_year": "0 Activitats",
        "total_distance_km": "0.0 Km",
        "distance_comparasion": "Cap activitat",
        "total_time_minutes": "0 min",
        "total_time_days": "0 dies",
        "total_elevation_m": "0 m",
        "everest_equivalent": 0.0,
        "dominant_sport": None,
        "sports_practiced": 0,
        "sport_podium": {"first": {"sport": None, "count": 0}, "second": {"sport": None, "count": 0}, "third": {"sport": None, "count": 0}},
        "total_energy_kwh": "0 kWh",
        "house_power_days": "0 dies",
        "most_kudos_activity": {"name": None, "kudos": 0},
        "total_prs": 0,
        "total_kudos": 0,
        "total_photos": 0,
        "total_comments": 0,
        "social_ratio": "Solo",
        "train_time": "Matiner",
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

def training_time_profile(activities):
    """
    activities: iterable d'activitats Strava amb camp 'start_date'
    retorna: string descriptiu (ex: 'Matiner', 'De tardes', 'Nocturn')
    """

    if not activities:
        return None

    counter = Counter()

    for act in activities:
        start_date = act.get("start_date")
        if not start_date:
            continue

        # Parse ISO 8601 UTC
        dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        hour = dt.hour

        if 5 <= hour < 12:
            counter["morning"] += 1
        elif 12 <= hour < 19:
            counter["afternoon"] += 1
        else:
            counter["night"] += 1

    if not counter:
        return None

    dominant = counter.most_common(1)[0][0]

    # Text final (ja en l’idioma que vulguis)
    mapping = {
        "morning": "Matiner",
        "afternoon": "De tardes",
        "night": "Nocturn",
    }
    return mapping[dominant]