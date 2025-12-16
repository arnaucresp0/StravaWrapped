from fastapi import Request, HTTPException

def get_current_athlete_id(request: Request) -> int:
    athlete_id = request.session.get("athlete_id")

    if not athlete_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return athlete_id
