import os
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    admin_user = os.getenv("ADMIN_USERNAME", "")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")

    ok_user = secrets.compare_digest(form_data.username, admin_user)
    ok_pass = secrets.compare_digest(form_data.password, admin_pass)

    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "mensaje": "Inicio de sesión exitoso",
        "usuario": form_data.username,
        "rol": "admin",
    }