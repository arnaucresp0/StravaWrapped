import time
import requests
from src.token_store import load_tokens, save_tokens
from src import config

def get_valid_token():
    tokens = load_tokens()

    if tokens is None:
        raise Exception("No hi ha tokens guardats. Primer fes /auth.")

    expires_at = tokens.get("expires_at")
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    # If the token has not expired then, we return the same token because it is valid
    if expires_at and expires_at > time.time():
        return access_token

    # If it has expired then we refresh it by calling the /oauth
    payload = {
        "client_id": config.STRAVA_CLIENT_ID,
        "client_secret": config.STRAVA_CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    url = "https://www.strava.com/oauth/token"
    r = requests.post(url, data=payload)
    new_tokens = r.json()

    # We save the new tokens
    save_tokens({
        "access_token": new_tokens.get("access_token"),
        "refresh_token": new_tokens.get("refresh_token"),
        "expires_at": new_tokens.get("expires_at")
    })

    return new_tokens.get("access_token")
