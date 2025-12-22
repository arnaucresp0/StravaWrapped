from fastapi import FastAPI, Request, HTTPException
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
import src.config as config  
import os
from starlette.middleware.base import BaseHTTPMiddleware
import secrets
import json
from typing import Dict

SESSION_TOKENS: Dict[str, Dict] = {}  # {token: {"athlete_id": 123, "created_at": ...}}
TOKEN_EXPIRY_HOURS = 24

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="workout_wrapped_session",
    same_site="none",  # Important per cross-site
    https_only=True,   # Requerit amb same_site=none
    max_age=86400,     # 24 hores en segons
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://workout-wrapped-cat.netlify.app/",
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

     # Genera un token de sessió segur
    session_token = secrets.token_urlsafe(32)
    
    # Guarda el token en memòria (associat amb athlete_id)
    SESSION_TOKENS[session_token] = {
        "athlete_id": athlete_id,
        "created_at": datetime.now().isoformat()
    }
    
    # Neteja tokens antics (opcional)
    cleanup_old_tokens()
    
    print(f"✅ [AUTH] Token creat: {session_token[:10]}... per athlete {athlete_id}")
    
    # Redirigeix al frontend amb el token com a paràmetre
    frontend_url = f"{config.FRONTEND_URL}?token={session_token}"
    return RedirectResponse(url=frontend_url)

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
    start_total = time.time()
    
    # DEBUG: Mostrar headers per veure si el token arriba
    token_header = request.headers.get("x-session-token")
    print(f"🔍 [/wrapped/image] Token header: {token_header[:20] + '...' if token_header else 'None'}")
    print(f"🔍 [/wrapped/image] Session: {request.session.get('athlete_id')}")
    
    try:
        athlete_id = get_current_athlete_id(request)
    except HTTPException as e:
        print(f"🚨 [/wrapped/image] Error auth: {e.detail}")
        raise
    
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

@app.get("/me_token")
def me_token(request: Request):
    """
    Endpoint /me que accepta token via header O cookie
    Compatible amb tots els navegadors
    """
    # Opció A: Token via header (per a Safari mòbil)
    token = request.headers.get("x-session-token")
    if token and token in SESSION_TOKENS:
        athlete_data = SESSION_TOKENS[token]
        return {
            "authenticated": True,
            "athlete_id": athlete_data["athlete_id"],
            "auth_method": "token_header"
        }
    
    # Opció B: Token via query param (per a redirecció inicial)
    token_param = request.query_params.get("token")
    if token_param and token_param in SESSION_TOKENS:
        athlete_data = SESSION_TOKENS[token_param]
        return {
            "authenticated": True,
            "athlete_id": athlete_data["athlete_id"],
            "auth_method": "token_param"
        }
    
    # Opció C: Cookies (per a navegadors que les suportin)
    athlete_id = request.session.get("athlete_id")
    if athlete_id:
        return {
            "authenticated": True,
            "athlete_id": athlete_id,
            "auth_method": "cookie"
        }
    
    # Si cap mètode funciona
    print(f"🔍 [/me_token] No autenticat. Token header: {bool(token)}, Token param: {bool(token_param)}, Session: {request.session.get('athlete_id')}")
    return {
        "authenticated": False,
        "auth_method": "none"
    }

@app.get("/debug_tokens")
def debug_tokens():
    """Endpoint de debug per veure tokens actius"""
    return {
        "total_tokens": len(SESSION_TOKENS),
        "tokens": {k[:10] + "...": v for k, v in SESSION_TOKENS.items()}
    }

def cleanup_old_tokens():
    """Elimina tokens antics per evitar que la memòria creixi infinitament"""
    global SESSION_TOKENS
    cutoff = datetime.now().timestamp() - (TOKEN_EXPIRY_HOURS * 3600)
    
    expired = []
    for token, data in SESSION_TOKENS.items():
        created = datetime.fromisoformat(data["created_at"]).timestamp()
        if created < cutoff:
            expired.append(token)
    
    for token in expired:
        del SESSION_TOKENS[token]
    
    if expired:
        print(f"🧹 [CLEANUP] Eliminats {len(expired)} tokens expirats")

