from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import requests
from datetime import datetime
import time
from urllib.parse import urlencode
from src.strava_client import get_wrapped_stats
from src.image_generator import generate_wrapped_images_base64
from src.token_manager import get_valid_token, has_tokens
from src.auth_helper import get_current_athlete_id
import src.config as config  # el nostre fitxer .env carregat
import os# Afegeix aquest middleware després de crear l'app
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="strava_wrapped_session",
    same_site="none",  # Important per cross-site
    https_only=True,   # Requerit amb same_site=none
    max_age=86400,     # 24 hores en segons
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://strava-wrapped-cat.netlify.app",
        config.FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MobileFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Headers específics per a Safari mòbil
        user_agent = request.headers.get("user-agent", "").lower()
        if "safari" in user_agent and "chrome" not in user_agent:
            response.headers["P3P"] = 'CP="This is not a P3P policy!"'
            response.headers["Cache-Control"] = "no-cache, private"
        
        return response

# Registra el middleware
app.add_middleware(MobileFixMiddleware)
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
    request.session["authenticated"] = True

    return RedirectResponse(url=config.FRONTEND_URL)


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
    import time
    start_total = time.time()
    
    athlete_id = get_current_athlete_id(request)
    print(f"⏱️  [TIMING] START /wrapped/image per athlete {athlete_id}")
    
    # 1. Estadístiques
    start_stats = time.time()
    stats = get_wrapped_stats()
    stats_time = time.time() - start_stats
    print(f"✅ [TIMING] Stats en {stats_time:.1f}s - {stats.get('activities_last_year', 'N/A')}")
    
    # 2. Imatges en Base64 directament (nova funció)
    start_images = time.time()
    images_base64 = generate_wrapped_images_base64(stats, athlete_id)
    images_time = time.time() - start_images
    
    total_time = time.time() - start_total
    print(f"🎯 [TIMING] COMPLET en {total_time:.1f}s")
    
    return {
        "athlete_id": athlete_id,
        "images": images_base64
    }

@app.get("/me")
def me(request: Request):
    # DEBUG: Mostrar info completa
    athlete_id = request.session.get("athlete_id")
    authenticated = request.session.get("authenticated", False)
    
    print(f"🔍 [/me] athlete_id: {athlete_id}, authenticated: {authenticated}")
    print(f"🔍 [/me] User-Agent: {request.headers.get('user-agent', 'No UA')}")
    print(f"🔍 [/me] Cookies: {request.headers.get('cookie', 'No cookies')}")
    
    # SOLUCIÓ: No depèn de has_tokens(), només de la sessió
    return {
        "authenticated": authenticated,
        "athlete_id": athlete_id,
        "user_agent": request.headers.get('user-agent', 'unknown'),
        "session_keys": list(request.session.keys())
    }

@app.get("/debug_session")
def debug_session(request: Request):
    """Endpoint per debug de sessió complet"""
    import json
    
    info = {
        "session": dict(request.session),
        "headers": {
            "user_agent": request.headers.get("user-agent"),
            "cookie": request.headers.get("cookie"),
            "origin": request.headers.get("origin"),
            "referer": request.headers.get("referer"),
        },
        "is_mobile": any(x in request.headers.get("user-agent", "").lower() 
                        for x in ['mobile', 'android', 'iphone', 'ipad']),
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📱 [SESSION DEBUG] {json.dumps(info, indent=2)}")
    return info

@app.get("/debug_cookies")
def debug_cookies(request: Request):
    """Mostra les cookies rebudes"""
    cookies = request.headers.get("cookie", "No cookies")
    print(f"🍪 [COOKIES] {cookies}")
    
    return {
        "cookies_received": cookies,
        "set_cookie_header": request.headers.get("set-cookie", "None"),
        "user_agent": request.headers.get("user-agent")
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

