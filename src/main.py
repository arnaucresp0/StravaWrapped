from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import requests
from urllib.parse import urlencode
import src.config as config  # el nostre fitxer .env carregat

app = FastAPI()

# Memòria temporal per guardar tokens (només per testing local)
user_tokens = {}
ACCESS_TOKEN = "baac1838b293ae6306823c"  # Després això ho gestionarem dinàmicament

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