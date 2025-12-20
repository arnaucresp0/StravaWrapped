from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import requests
from urllib.parse import urlencode
from datetime import datetime, timedelta, timezone
from src.strava_client import get_wrapped_stats
from src.image_generator import generate_wrapped_images
from src.user_context import set_active_user, get_active_user
from src.token_manager import get_valid_token
from src.auth_helper import get_current_athlete_id
import src.config as config  # el nostre fitxer .env carregat
import os

print("ENV =", os.getenv("ENV"))
print("STRAVA_CLIENT_ID =", config.STRAVA_CLIENT_ID)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="strava_wrapped_session"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",  # frontend local  
        "http://127.0.0.1:5500",  # frontend local
        #config.FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def exchange_token(request: Request,code: str):
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
    # Define the active user from Strava auth
    athlete = data.get("athlete")
    if not athlete:
        raise RuntimeError("No athlete info returned from Strava")

    athlete_id = athlete["id"]

    request.session["athlete_id"] = athlete_id

    return RedirectResponse(url="http://localhost:5500/index.html")


# Get request for the activities using http://localhost:8000/activities once the .env is with the proper acces_token
@app.get("/activities")
def get_activities():

    access_token = get_valid_token()

    headers = {"Authorization": f"Bearer {access_token}"}

    url = "https://www.strava.com/api/v3/athlete/activities"

    r = requests.get(url, headers=headers)
    return r.json()

@app.get("/wrapped")
def get_wrapped():
    return get_wrapped_stats()


@app.get("/wrapped/image")
async def generate_wrapped_image_endpoint(request: Request):
    athlete_id = get_current_athlete_id(request)

    stats = get_wrapped_stats()
    outputs = generate_wrapped_images(stats, athlete_id)

    return {
        "athlete_id": athlete_id,
        "images": outputs
    }

@app.get("/wrapped/image/{image_name}")
def get_wrapped_image(request: Request, image_name: str):
    athlete_id = get_current_athlete_id(request)

    image_path = get_user_wrapped_image_path(athlete_id, image_name)

    return FileResponse(
        image_path,
        media_type="image/png",
        filename=image_name
    )

@app.get("/me")
def me(request: Request):
    athlete_id = request.session.get("athlete_id")

    if not athlete_id:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "athlete_id": athlete_id
    }

def get_user_wrapped_image_path(athlete_id: int, image_name: str) -> str:
    base_dir = os.path.join(
        "storage",
        "generated",
        str(athlete_id),
        "wrapped"
    )

    image_path = os.path.join(base_dir, image_name)

    # Seguretat bàsica
    if not os.path.isfile(image_path):
        raise FileNotFoundError("Image not found")

    return image_path
