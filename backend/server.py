from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from starlette.responses import JSONResponse
import secrets

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajuste se quiser restringir o frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Autenticação Básica
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "gabi")
    correct_password = secrets.compare_digest(credentials.password, "gabi03")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# MODELOS DE DADOS

class Cliente(BaseModel):
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None

clientes_db = []  # mock (você pode depois trocar por banco real)

# ROTAS PROTEGIDAS

@app.get("/")
def home(user: str = Depends(authenticate)):
    return {"message": f"Bem-vindo, {user}!"}

@app.post("/clientes", response_model=Cliente)
def criar_cliente(cliente: Cliente, user: str = Depends(authenticate)):
    clientes_db.append(cliente)
    return cliente

@app.get("/clientes")
def listar_clientes(user: str = Depends(authenticate)):
    return clientes_db
