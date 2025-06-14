from fastapi import Request
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt

SECRET_KEY = "segredo-teste"
ALGORITHM = "HS256"

def get_current_user(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise RedirectResponse("/login")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise RedirectResponse("/login")
