from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from supabase import create_client
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import hashlib

load_dotenv()

app = FastAPI(
    title="BRAHMO Rules Engine API",
    description="Role Based Access Control System using FastAPI, Supabase and JWT Authentication",
    version="1.0.0"
)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)


class User(BaseModel):
    id: str
    org_id: str
    name: str
    role: str
    department: str
    ceiling_level: int
    password: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def admin_only(user: dict = Depends(get_current_user)):
    if user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Access denied. Admin only")
    return user


@app.get("/", tags=["Home"])
def home():
    return {"message": "BRAHMO Rules Engine Running"}


@app.get("/rules", tags=["Rules"])
def get_rules():
    try:
        data = supabase.table("rules").select("*").execute()
        return data.data
    except Exception as e:
        return {"error": str(e)}


@app.get("/hierarchy", tags=["Hierarchy"])
def get_hierarchy():
    try:
        data = supabase.table("hierarchy_levels").select("*").execute()
        return data.data
    except Exception as e:
        return {"error": str(e)}


@app.get("/users", tags=["Users"])
def get_users():
    try:
        data = supabase.table("users").select("*").execute()
        return data.data
    except Exception as e:
        return {"error": str(e)}


@app.post("/register", tags=["Auth"])
def register(user: User):
    try:
        existing_user = supabase.table("users").select("*").eq("id", user.id).execute()

        if existing_user.data:
            return {"error": "User already exists"}

        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

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

    except Exception as e:
        return {"error": str(e)}


@app.post("/login", tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        username = form_data.username
        password = form_data.password

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        response = supabase.table("users").select("*").eq("id", username).execute()

        if len(response.data) == 0:
            raise HTTPException(status_code=404, detail="User not found")

        user = response.data[0]

        if user["password"] != hashed_password:
            raise HTTPException(status_code=401, detail="Invalid password")

        access_token = create_access_token(
            data={
                "sub": user["id"],
                "role": user["role"]
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        return {"error": str(e)}


@app.get("/protected", tags=["Auth"])
def protected_route(user: dict = Depends(get_current_user)):
    return {
        "message": "Protected route accessed",
        "user": user
    }


@app.post("/users", tags=["Users"])
def create_user(user: User, admin: dict = Depends(admin_only)):
    try:
        existing_user = supabase.table("users").select("*").eq("id", user.id).execute()

        if existing_user.data:
            return {"error": "User already exists"}

        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

        data = supabase.table("users").insert({
            "id": user.id,
            "org_id": user.org_id,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "ceiling_level": user.ceiling_level,
            "password": hashed_password
        }).execute()

        return data.data

    except Exception as e:
        return {"error": str(e)}


@app.put("/users/{user_id}", tags=["Users"])
def update_user(user_id: str, user: User, admin: dict = Depends(admin_only)):
    try:
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()

        data = supabase.table("users").update({
            "org_id": user.org_id,
            "name": user.name,
            "role": user.role,
            "department": user.department,
            "ceiling_level": user.ceiling_level,
            "password": hashed_password
        }).eq("id", user_id).execute()

        return {
            "message": "User updated successfully",
            "data": data.data
        }

    except Exception as e:
        return {"error": str(e)}


@app.delete("/users/{user_id}", tags=["Users"])
def delete_user(user_id: str, admin: dict = Depends(admin_only)):
    try:
        data = supabase.table("users").delete().eq("id", user_id).execute()

        return {
            "message": "User deleted successfully",
            "data": data.data
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/bfs/{start_id}", tags=["Hierarchy"])
def bfs_traversal(start_id: str):
    try:
        all_nodes = supabase.table("hierarchy_levels").select("*").execute().data

        visited = []
        queue = [start_id]

        while queue:
            current = queue.pop(0)

            if current in visited:
                continue

            visited.append(current)

            for node in all_nodes:
                if node["parent_id"] == current:
                    queue.append(node["id"])

        return {"bfs_order": visited}

    except Exception as e:
        return {"error": str(e)}
