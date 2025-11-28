from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from urllib.parse import urlencode
import src.config as config  # el nostre fitxer .env carregat

app = FastAPI()

# Memòria temporal per guardar tokens (només per testing local)
user_tokens = {}
ACCESS_TOKEN = "baac1838b293ae6306823c"  # Després això ho gestionarem dinàmicament

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


@app.get("/exchange_token")
def exchange_token(code: str):
    payload = {
        "client_id": config.STRAVA_CLIENT_ID,
        "client_secret": config.STRAVA_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
    }
    res = requests.post("https://www.strava.com/oauth/token", json=payload)
    data = res.json()

    # Guardem en memòria temporal
    if "athlete" in data and "id" in data["athlete"]:
        athlete_id = data["athlete"]["id"]
        user_tokens[athlete_id] = {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token"),
            "expires_at": data.get("expires_at"),
            "athlete": data["athlete"],
        }

    return JSONResponse(content=data)

@app.get("/activities")
def get_activities():
    url = "https://www.strava.com/api/v3/athlete/activities"

    headers = {
        "Authorization": f"Bearer {config.STRAVA_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    # Si falla per token caducat ja t'ho diré com arreglar-ho
    return response.json()