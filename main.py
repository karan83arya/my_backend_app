from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import get_connection
from fastapi import UploadFile, File
import shutil
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from strawberry.fastapi import GraphQLRouter
from main2 import schema   # <-- your file name

os.makedirs("uploads", exist_ok=True)

app = FastAPI()
# 🔥 Attach GraphQL
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")


# ============================
# 📁 CONFIG
# ============================

SERVER_URL = "http://192.168.1.56:8000"  # your FastAPI IP

MENU_ICON_DIR = r"C:\xampp\htdocs\smartEduERANew\public\assets\adminAssets\img\menu-icon"

app.mount(
    "/menu-icons",
    StaticFiles(directory=MENU_ICON_DIR),
    name="menu-icons"
)

UPLOAD_DIR = r"C:\xampp\htdocs\smartEduERANew\public\uploads\profile_images"

TICKET_UPLOAD_DIR = r"C:\xampp\htdocs\smartEduERANew\public\uploads\ticket_images"

app.mount(
    "/uploads/profile_images",
    StaticFiles(directory=UPLOAD_DIR),
    name="profile_images"
)
app.mount(
    "/uploads/ticket_images",
    StaticFiles(directory=TICKET_UPLOAD_DIR),
    name="ticket_images"
)

# 🔥 CORS (very important for Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 📦 MODELS (THIS WAS MISSING)
# ============================

class LoginRequest(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    phone: str
    rollno: str
    course: str
    first_name: str
    last_name: str


class UserUpdate(BaseModel):
    username: str
    email: str
    phone: str
    rollno: str
    course: str
    first_name: str
    last_name: str

# ============================
# 👤 GET ALL USERS
# ============================

@app.get("/users")
def get_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, username, email, phone, rollno, course, first_name, last_name, photo
        FROM users
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "phone": r[3],
            "rollno": r[4],
            "course": r[5],
            "first_name": r[6],
            "last_name": r[7],
            "photo": r[8],
        }
        for r in rows
    ]


# ============================
# ➕ ADD USER
# ============================

@app.post("/users")
def add_user(user: UserCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users 
        (username, password, email, phone, rollno, course, first_name, last_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user.username,
            user.password,
            user.email,
            user.phone,
            user.rollno,
            user.course,
            user.first_name,
            user.last_name,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "User added successfully"}


# ============================
# ✏️ UPDATE USER
# ============================

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET username=%s, email=%s, phone=%s,
            rollno=%s, course=%s,
            first_name=%s, last_name=%s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id=%s
        """,
        (
            user.username,
            user.email,
            user.phone,
            user.rollno,
            user.course,
            user.first_name,
            user.last_name,
            user_id,
        ),
    )

    conn.commit()

    cur.close()
    conn.close()

    return {"message": "User updated successfully"}
# ============================
# 🗑 DELETE USER
# ============================

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()

    cur.close()
    conn.close()

    return {"message": "User deleted successfully"}


# ============================
# 🔍 SEARCH USER
# ============================

@app.get("/search")
def search_users(query: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, email, phone
        FROM users
        WHERE username ILIKE %s
        OR email ILIKE %s
        OR phone LIKE %s
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%"),
    )

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "username": r[1],
            "email": r[2],
            "phone": r[3],
        }
        for r in rows
    ]


# ============================
# 👤 GET SINGLE USER
# ============================

@app.get("/users/{user_id}")
def get_user(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, username, email, phone, rollno, course, first_name, last_name, photo
        FROM users
        WHERE id = %s
        """,
        (user_id,),
    )

    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user[0],
        "username": user[1],
        "email": user[2],
        "phone": user[3],
        "rollno": user[4],
        "course": user[5],
        "first_name": user[6],
        "last_name": user[7],
        "photo": user[8],
    }

from fastapi.responses import FileResponse


import os
from fastapi import UploadFile, File



@app.post("/upload-profile/{user_id}")
def upload_profile(user_id: int, file: UploadFile = File(...)):

    if not file.content_type.startswith("image/"):
        return {"error": "Only image files allowed"}

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"user_{user_id}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # ✅ Save clean relative path in DB
    relative_path = f"uploads/profile_images/{file_name}"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET profile_image = %s WHERE id = %s",
        (relative_path, user_id),  # ✅ clean path in DB
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Profile image uploaded",
        "path": relative_path,
        "url": f"{SERVER_URL}/uploads/profile_images/{file_name}"  # ✅ full URL for Flutter
    }


@app.post("/upload-ticket/{ticket_id}")
def upload_ticket(ticket_id: int, file: UploadFile = File(...)):

    if not file.content_type.startswith("image/"):
        return {"error": "Only image files allowed"}

    os.makedirs(TICKET_UPLOAD_DIR, exist_ok=True)

    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    file_name = f"ticket_{ticket_id}.{ext}"
    file_path = os.path.join(TICKET_UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # ✅ Save clean relative path in DB
    relative_path = f"uploads/ticket_images/{file_name}"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE support_tickets SET attachment_name = %s WHERE id = %s",
        (relative_path, ticket_id),  # ✅ clean path in DB
    )
    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "Ticket image uploaded",
        "path": relative_path,
        "url": f"{SERVER_URL}/uploads/ticket_images/{file_name}"
    }