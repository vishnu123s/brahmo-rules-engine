from pydantic import BaseModel
from fastapi import FastAPI,Depends
from fastapi.security import OAuth2PasswordRequestForm
from supabase import create_client
from dotenv import load_dotenv
import os
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

load_dotenv()

app = FastAPI()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt
    
class User(BaseModel):
    id: str
    org_id: str
    name: str
    role: str
    department: str
    ceiling_level: int
    password:str

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

@app.get("/")
def home():
    return {"message": "BRAHMO Rules Engine Running"}

@app.get("/rules")
def get_rules():
    data = supabase.table("rules").select("*").execute()
    return data.data

@app.get("/hierarchy")
def get_hierarchy():
    data = supabase.table("hierarchy_levels").select("*").execute()
    return data.data

@app.get("/users")
def get_users():
    data = supabase.table("users").select("*").execute()
    return data.data

@app.post("/users")
def create_user(user: User):

    data = supabase.table("users").insert({
        "id": user.id,
        "org_id": user.org_id,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "ceiling_level": user.ceiling_level
    }).execute()

    return data.data

@app.put("/users/{user_id}")
def update_user(user_id: str, user: User):

    data = supabase.table("users").update({
        "org_id": user.org_id,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "ceiling_level": user.ceiling_level
    }).eq("id", user_id).execute()

    return data.data

@app.delete("/users/{user_id}")
def delete_user(user_id: str):

    data = supabase.table("users").delete().eq("id", user_id).execute()

    return {
        "message": "User deleted successfully",
        "data": data.data
    }
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    if form_data.username != "admin" or form_data.password != "admin123":
        return {"error": "Invalid username or password"}

    access_token = create_access_token(
        data={"sub": form_data.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None


@app.get("/protected")
def protected_route(token: str):
    user = verify_token(token)

    if not user:
        return {"message": "Invalid token"}

    return {
        "message": "Protected route accessed",
        "user": user
    }

@app.post("/register")
def register(user: User):
    hashed_password = pwd_context.hash(user.password)

    data = {
        "id": user.id,
        "org_id": user.org_id,
        "name": user.name,
        "role": user.role,
        "department": user.department,
        "ceiling_level": user.ceiling_level,
        "password": hashed_password
    }

    response = supabase.table("users").insert(data).execute()

    return {
        "message": "User registered successfully",
        "data": response.data
    }
    
@app.get("/bfs/{start_id}")
def bfs_traversal(start_id: str):

    all_nodes = supabase.table("hierarchy_levels").select("*").execute().data

    visited = []
    queue = [start_id]

    while queue:
        current = queue.pop(0)
        visited.append(current)

        children = []

        for node in all_nodes:
            if node["parent_id"] == current:
                children.append(node["id"])

        queue.extend(children)

    return {"bfs_order": visited}
