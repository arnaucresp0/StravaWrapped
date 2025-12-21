from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import requests
from urllib.parse import urlencode
from src.strava_client import get_wrapped_stats
from src.image_generator import generate_wrapped_images_in_memory
from src.token_manager import get_valid_token, has_tokens
from src.auth_helper import get_current_athlete_id
import src.config as config  # el nostre fitxer .env carregat
import os
import base64
import io

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SECRET_KEY,
    session_cookie="strava_wrapped_session",
    same_site="none",
    https_only=True
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
    athlete_id = get_current_athlete_id(request)
    stats = get_wrapped_stats()
    
    images_pil = generate_wrapped_images_in_memory(stats, athlete_id)
    
    images_base64 = []
    for img_pil in images_pil:
        # Processa una imatge a la vegada
        img_byte_arr = io.BytesIO()
        img_pil.save(img_byte_arr, format='PNG', optimize=True)  # Afegeix optimize
        img_byte_arr.seek(0)
        
        encoded_string = base64.b64encode(img_byte_arr.read()).decode('utf-8')
        images_base64.append(encoded_string)
        
        # Allibera memòria explícitament
        img_pil.close()  # Tanca la imatge PIL
        del img_byte_arr  # Elimina el buffer
    
    return {
        "athlete_id": athlete_id,
        "images": images_base64
    }

@app.get("/me")
def me(request: Request):
    authenticated = request.session.get("authenticated", False)
    tokens = has_tokens()

    return {
        "authenticated": authenticated and tokens
    }

@app.get("/test_image")
def test_image():
    # Crea una imatge senzilla en memòria
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (300, 200), color='blue')
    d = ImageDraw.Draw(img)
    d.text((100, 100), "Test OK", fill='white')

    # Converteix a Base64
    import base64, io
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    encoded_string = base64.b64encode(img_byte_arr.read()).decode('utf-8')

    return {"image_base64": encoded_string}

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

