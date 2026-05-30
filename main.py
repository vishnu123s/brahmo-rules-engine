from pydantic import BaseModel
from fastapi import FastAPI
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

class User(BaseModel):
    id: str
    org_id: str
    name: str
    role: str
    department: str
    ceiling_level: int

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
