from dotenv import load_dotenv
import os

# Determinar l'entorn actual
def is_production():
    # Render posa aquesta variable quan està en producció
    if os.getenv("RENDER") is not None:
        return True
    # O pots posar manualment ENV=production
    if os.getenv("ENV") == "production":
        return True
    # Per defecte, desenvolupament
    return False

# Carregar el fitxer .env correcte
if is_production():
    print("🚀 Entorn: PRODUCCIÓ")
    env_file = ".env.production"
else:
    print("💻 Entorn: DESENVOLUPAMENT")  
    env_file = ".env"

# Carregar variables
dotenv_path = os.path.join(os.path.dirname(__file__), env_file)
load_dotenv(dotenv_path)

# Les variables (sense canvis)
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")
STRAVA_ACCESS_TOKEN = os.getenv("STRAVA_ACCESS_TOKEN")
STRAVA_REFRESH_TOKEN = os.getenv("STRAVA_REFRESH_TOKEN")
STRAVA_EXPIRES_AT = os.getenv("STRAVA_EXPIRES_AT")
SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Verificació
if not SECRET_KEY or SECRET_KEY == "super-secret-production-key":
    raise ValueError("Cal configurar una SECRET_KEY vàlida a producció!")