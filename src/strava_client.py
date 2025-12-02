import requests
from src.token_manager import get_valid_token

BASE_URL = "https://www.strava.com/api/v3"

def get_all_activities():
    access_token = get_valid_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    activities = []
    page = 1

    while True:
        url = f"{BASE_URL}/athlete/activities?page={page}&per_page=200"
        r = requests.get(url, headers=headers)
        data = r.json()

        if not isinstance(data, list) or len(data) == 0:
            break

        activities.extend(data)
        page += 1

    return activities
