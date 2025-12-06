from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from src.strava_client import get_all_activities
import src.config as config  # el nostre fitxer .env carregat

app = FastAPI()

# Memòria temporal per guardar tokens (només per testing local)
user_tokens = {}

# Get request for the auth using http://localhost:8000/auth to authorize using strava api the tokens for the app
@app.get("/auth")
def auth():
    params = {
        "client_id": config.STRAVA_CLIENT_ID,
        "redirect_uri": config.STRAVA_REDIRECT_URI,
        "response_type": "code",
        "scope": "activity:read_all",
        "approval_prompt": "auto"
    }
    url = "https://www.strava.com/oauth/authorize?" + urlencode(params)
    return RedirectResponse(url)

# Get request for the auth using http://localhost:8000/auth to get the tokens and returns the athlete info in json
@app.get("/exchange_token")
async def exchange_token(code: str):
    url = "https://www.strava.com/oauth/token"

    payload = {
        "client_id": config.STRAVA_CLIENT_ID,
        "client_secret": config.STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }

    r = requests.post(url, data=payload)
    data = r.json()

    # Import this here to avoid circular imports
    from src.token_store import save_tokens

    # Guardem els tokens nous
    save_tokens({
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_at": data.get("expires_at")
    })

    return data


# Get request for the activities using http://localhost:8000/activities once the .env is with the proper acces_token
@app.get("/activities")
def get_activities():
    from src.token_manager import get_valid_token

    access_token = get_valid_token()

    headers = {"Authorization": f"Bearer {access_token}"}

    url = "https://www.strava.com/api/v3/athlete/activities"

    r = requests.get(url, headers=headers)
    return r.json()

@app.get("/wrapped")
async def get_wrapped():
    activities = get_all_activities()

    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

    filtered = []
    for a in activities:
        if "start_date" not in a:
            continue

        activity_date = datetime.fromisoformat(a["start_date"].replace("Z", "+00:00"))
        if activity_date > one_year_ago:
            filtered.append(a)

    # Estadístiques bàsiques
    total_distance_km = sum(a.get("distance", 0) for a in filtered) / 1000
    total_time_hours = sum(a.get("moving_time", 0) for a in filtered) / 3600
    total_time_minutes = sum(a.get("moving_time", 0) for a in filtered) / 60
    total_time_days = total_time_minutes / (60 * 24)
    total_elevation = sum(a.get("total_elevation_gain", 0) for a in filtered)

    # Esport dominant
    from collections import Counter
    sports = Counter(a.get("sport_type", "Unknown") for a in filtered)
    dominant_sport = sports.most_common(1)[0][0] if sports else None

    # Watts totals
    total_watts = 0
    for a in filtered:
        watts = a.get("weighted_average_watts")
        time = a.get("moving_time", 0)
        if watts:
            total_watts += watts * time  # Joules (W*s)
    total_energy_kwh = round(total_watts / 3600000, 2)

    # Activitat amb més kudos
    most_kudos_activity = None
    if filtered:
        most_kudos_activity = max(filtered, key=lambda x: x.get("kudos_count", 0))

    # Total PRs
    total_prs = sum(a.get("pr_count", 0) for a in filtered)

    return {
        "activities_last_year": len(filtered),
        "total_distance_km": round(total_distance_km, 1),
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
