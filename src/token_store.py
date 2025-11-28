import json
import os

TOKEN_FILE = "token_data.json"

def save_tokens(data: dict):
    """Save access_token, refresh_token and expires_at in a JSON."""
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_tokens():
    """Load the tokens if they exist, else return none."""
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)
