from fastapi import Request, HTTPException
import os

# Necessitem importar SESSION_TOKENS de main.py
# Per evitar import circular, ho fem d'una altra manera

def get_current_athlete_id(request: Request) -> int:
    """
    Versió millorada: Accepta tant sessió (cookies) com token (header)
    """
    # Mètode 1: Token via header (per a Safari mòbil)
    token = request.headers.get("x-session-token")
    if token:
        # Import aquí per evitar circular dependencies
        from src.main import SESSION_TOKENS
        if token in SESSION_TOKENS:
            athlete_data = SESSION_TOKENS[token]
            print(f"🔑 [AUTH] Token vàlid, athlete_id: {athlete_data['athlete_id']}")
            return athlete_data["athlete_id"]
    
    # Mètode 2: Sessió tradicional (cookies)
    athlete_id = request.session.get("athlete_id")
    if athlete_id:
        print(f"🍪 [AUTH] Sessió vàlida, athlete_id: {athlete_id}")
        return athlete_id
    
    # Cap mètode vàlid
    print(f"🚨 [AUTH] No autenticat. Token header: {bool(token)}, Session: {request.session.get('athlete_id')}")
    raise HTTPException(status_code=401, detail="Not authenticated")