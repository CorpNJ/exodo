from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

app = FastAPI(title="Exodo API - Login Admin")

# Credenciales fijas para el administrador (por ahora)
ADMIN_USERNAME = "Corp_Admin_2026_1403"
ADMIN_PASSWORD = "Admin123#2026"

@app.get("/")
def root():
    return {"message": "API de Exodo funcionando. Ve a /docs para probar el login."}

@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de inicio de sesión.
    Recibe 'username' y 'password' como form-data.
    """
    if form_data.username != ADMIN_USERNAME or form_data.password != ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Si las credenciales son correctas
    return {
        "mensaje": "Inicio de sesión exitoso",
        "usuario": form_data.username,
        "rol": "admin"
    }